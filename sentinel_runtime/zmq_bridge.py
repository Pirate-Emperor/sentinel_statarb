"""Validated JSON bridge for ZeroMQ IPC or TCP sockets."""
from __future__ import annotations
from dataclasses import asdict
from typing import Any
from .engine import Tick

def tick_to_message(tick: Tick) -> dict[str, Any]:
    return asdict(tick)

def tick_from_message(message: dict[str, Any]) -> Tick:
    required = {"symbol", "sequence", "timestamp_ns", "bid", "ask"}
    if set(message) != required: raise ValueError(f"tick message must contain exactly {sorted(required)}")
    return Tick(**message)

async def send_tick(socket: Any, tick: Tick) -> None:
    await socket.send_json(tick_to_message(tick))

async def receive_tick(socket: Any) -> Tick:
    message = await socket.recv_json()
    if not isinstance(message, dict): raise ValueError("tick frame must be a JSON object")
    return tick_from_message(message)
