"""Bounded asynchronous tick writer backed by DuckDB."""
from __future__ import annotations
import asyncio
import queue
import threading
from pathlib import Path
from typing import Final, TypeAlias
from .engine import Tick
Row: TypeAlias = tuple[str, int, int, float, float]
QueueItem: TypeAlias = Row | list[Row] | object
_STOP: Final = object()

class AsyncDuckDBTickLogger:
    """Write rows in batches on one thread; apply back-pressure rather than drop data."""
    def __init__(self, database_path: str | Path, batch_size: int = 2048, queue_size: int = 64) -> None:
        if batch_size < 1 or queue_size < 1: raise ValueError("batch_size and queue_size must be positive")
        self.database_path, self.batch_size = str(database_path), batch_size
        self._queue: queue.Queue[QueueItem] = queue.Queue(maxsize=queue_size)
        self._ready = threading.Event()
        self._thread: threading.Thread | None = None
        self._error: BaseException | None = None
        self.rows_written, self._closed = 0, False
    async def start(self) -> None:
        if self._thread is not None: raise RuntimeError("logger has already been started")
        Path(self.database_path).expanduser().resolve().parent.mkdir(parents=True, exist_ok=True)
        self._thread = threading.Thread(target=self._worker, name="sentinel-duckdb-writer", daemon=True)
        self._thread.start()
        await asyncio.to_thread(self._ready.wait)
        self._raise_if_failed()
    async def log(self, tick: Tick) -> None:
        self._ensure_running()
        await self._put((tick.symbol, tick.sequence, tick.timestamp_ns, tick.bid, tick.ask))
    async def log_many(self, ticks: list[Tick]) -> None:
        self._ensure_running()
        batch: list[Row] = []
        for tick in ticks:
            batch.append((tick.symbol, tick.sequence, tick.timestamp_ns, tick.bid, tick.ask))
            if len(batch) >= self.batch_size:
                await self._put(batch)
                batch = []
        if batch: await self._put(batch)
    async def close(self) -> None:
        if self._thread is None or self._closed: return
        self._closed = True
        if self._thread.is_alive():
            await self._put(_STOP)
            await asyncio.to_thread(self._thread.join)
        self._raise_if_failed()
    def _ensure_running(self) -> None:
        if self._thread is None or self._closed: raise RuntimeError("logger must be started and not closed")
        self._raise_if_failed()
    async def _put(self, item: QueueItem) -> None:
        await asyncio.to_thread(self._put_blocking, item)
        self._raise_if_failed()
    def _put_blocking(self, item: QueueItem) -> None:
        while True:
            self._raise_if_failed()
            try:
                self._queue.put(item, timeout=0.1)
                return
            except queue.Full:
                if self._thread is not None and not self._thread.is_alive():
                    self._raise_if_failed()
                    raise RuntimeError("DuckDB writer stopped unexpectedly")
    def _raise_if_failed(self) -> None:
        if self._error is not None: raise RuntimeError("DuckDB tick writer failed") from self._error
    def _worker(self) -> None:
        connection = None
        try:
            import duckdb
            connection = duckdb.connect(self.database_path)
            connection.execute("CREATE TABLE IF NOT EXISTS ticks (symbol VARCHAR, sequence BIGINT, timestamp_ns BIGINT, bid DOUBLE, ask DOUBLE)")
            self._ready.set()
            batch: list[Row] = []
            while True:
                item = self._queue.get()
                if item is _STOP:
                    if batch: self._flush(connection, batch)
                    break
                incoming: list[Row] = item if isinstance(item, list) else [item]  # type: ignore[list-item]
                batch.extend(incoming)
                while len(batch) >= self.batch_size:
                    to_write, batch = batch[:self.batch_size], batch[self.batch_size:]
                    self._flush(connection, to_write)
            connection.close()
        except BaseException as exc:
            self._error = exc
            self._ready.set()
            if connection is not None:
                try: connection.close()
                except Exception: pass
    def _flush(self, connection: object, batch: list[Row]) -> None:
        connection.executemany("INSERT INTO ticks VALUES (?, ?, ?, ?, ?)", batch)  # type: ignore[attr-defined]
        self.rows_written += len(batch)
        batch.clear()
