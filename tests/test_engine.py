from __future__ import annotations
import asyncio
import unittest
from sentinel_runtime.engine import DynamicDebouncer, ExecutionEngine, OCOStopLimit, Tick
from sentinel_runtime.experiments import make_stream, oco_gap_sweep, run_experiments
from sentinel_runtime.zmq_bridge import tick_from_message, tick_to_message

class TickTests(unittest.TestCase):
    def test_rejects_invalid_quotes(self):
        with self.assertRaises(ValueError): Tick("X",1,10,102.0,101.0)
        with self.assertRaises(ValueError): Tick("X",1,10,float("nan"),101.0)
        with self.assertRaises(ValueError): Tick("",1,10,100.0,101.0)
    def test_midpoint(self): self.assertEqual(Tick("X",1,10,99.0,101.0).mid,100.0)

class DebouncerTests(unittest.TestCase):
    def test_fixed_window_rejects_repeats(self):
        d=DynamicDebouncer(100,100,10.0)
        self.assertTrue(d.accept("X",1000,100.0));self.assertFalse(d.accept("X",1050,100.0));self.assertTrue(d.accept("X",1100,100.0))
    def test_large_move_extends_debounce_window(self):
        d=DynamicDebouncer(100000,2000000,5.0)
        self.assertTrue(d.accept("X",1000000,100.0));self.assertTrue(d.accept("X",1200000,100.0))
        self.assertFalse(d.accept("X",1300000,98.0));self.assertFalse(d.accept("X",2000000,98.0));self.assertTrue(d.accept("X",3300000,98.0))
    def test_cooldown_is_independent_per_symbol(self):
        d=DynamicDebouncer(100,100,10.0);self.assertTrue(d.accept("X",1000,100.0));self.assertTrue(d.accept("Y",1000,100.0))

class OcoTests(unittest.TestCase):
    def test_long_stop_limit_has_exact_five_bps_offset(self):
        order=OCOStopLimit(100.0,"long",25.0,50.0,5.0);event=order.observe("X",99.70)
        self.assertIsNotNone(event);self.assertEqual(event.kind,"stop_triggered")
        self.assertAlmostEqual(event.trigger_price,99.75)
        self.assertAlmostEqual((event.trigger_price-event.limit_price)/event.trigger_price*10000,5.0)
    def test_short_stop_limit_direction(self):
        event=OCOStopLimit(100.0,"short",25.0,50.0,5.0).observe("X",100.30)
        self.assertIsNotNone(event);self.assertGreater(event.limit_price,event.trigger_price)
        self.assertAlmostEqual((event.limit_price-event.trigger_price)/event.trigger_price*10000,5.0)
    def test_oco_fires_only_once(self):
        o=OCOStopLimit(100.0);self.assertIsNotNone(o.observe("X",99.7));self.assertIsNone(o.observe("X",100.6))
    def test_gap_beyond_limit_can_remain_unfilled(self):
        o=OCOStopLimit(100.0,"long",25.0,50.0,5.0);o.observe("X",98.2)
        self.assertFalse(o.limit_is_marketable(98.2));self.assertTrue(o.limit_is_marketable(99.72))

class EngineTests(unittest.TestCase):
    def test_duplicate_and_out_of_order_quotes_are_rejected(self):
        e=ExecutionEngine(max_quote_age_ns=1000000);t=Tick("X",1,1000000,99.9,100.1)
        self.assertEqual(e.process(t,1000500).reason,"accepted");self.assertEqual(e.process(t,1000500).reason,"duplicate_sequence")
        self.assertEqual(e.process(Tick("X",2,900000,99.9,100.1),900500).reason,"out_of_order_timestamp")
    def test_stale_and_future_quotes_are_rejected(self):
        e=ExecutionEngine(max_quote_age_ns=100,max_future_skew_ns=20)
        self.assertEqual(e.process(Tick("X",1,100,99,100),250).reason,"stale_quote")
        self.assertEqual(e.process(Tick("X",2,300,99,100),200).reason,"future_quote")
    def test_protective_order_checks_even_when_signal_is_debounced(self):
        e=ExecutionEngine(DynamicDebouncer(1000000,2000000,5.0));e.add_order("X",OCOStopLimit(100.0,stop_bps=25.0))
        self.assertTrue(e.process(Tick("X",1,1000000,99.9,100.1)).accepted_signal)
        r=e.process(Tick("X",2,1010000,98.1,98.3));self.assertFalse(r.accepted_signal)
        self.assertIsNotNone(r.risk_event);self.assertEqual(r.risk_event.kind,"stop_triggered")

class ExperimentsTests(unittest.TestCase):
    def test_stream_is_reproducible_and_contains_injected_duplicates(self):
        self.assertEqual(make_stream(500,42),make_stream(500,42));self.assertGreater(len(make_stream(500,42)),500)
    def test_oco_gap_sweep_matches_expected_fill_boundaries(self):
        rows=[x for x in oco_gap_sweep() if x["offset_bps"]==5.0]
        self.assertEqual([x["gap_bps"] for x in rows if x["marketable"]],[0.0,1.0,2.0,5.0])
    def test_experiment_result_counts_anomalies_and_triggers_stop(self):
        s=run_experiments(2000,1,42);self.assertEqual(len(s["policies"]),3)
        for row in s["policies"]:
            self.assertGreater(row["duplicate_sequences"],0);self.assertGreater(row["out_of_order_timestamps"],0)
            self.assertGreater(row["stale_quotes"],0);self.assertEqual(row["stop_triggers"],1)
            self.assertFalse(row["stop_limit_marketable_at_crash"])
        self.assertGreater(next(x for x in s["policies"] if x["policy"]=="dynamic debounce")["debounced_signals"],
                           next(x for x in s["policies"] if x["policy"]=="no debounce")["debounced_signals"])

class FakeDuckDBLoggerTests(unittest.IsolatedAsyncioTestCase):
    async def test_async_writer_batches_without_losing_rows(self):
        import tempfile,sys,types
        from pathlib import Path
        from unittest.mock import patch
        from sentinel_runtime.duckdb_logger import AsyncDuckDBTickLogger
        written=[];sizes=[]
        class Connection:
            def execute(self,query): self.query=query
            def executemany(self,query,rows): sizes.append(len(rows));written.extend(list(rows))
            def close(self): pass
        fake=types.SimpleNamespace(connect=lambda path:Connection())
        with tempfile.TemporaryDirectory() as d,patch.dict(sys.modules,{"duckdb":fake}):
            logger=AsyncDuckDBTickLogger(Path(d)/"ticks.duckdb",batch_size=10,queue_size=2)
            await logger.start();await logger.log_many([Tick("X",i,i+1,99,101) for i in range(25)]);await logger.close()
        self.assertEqual(logger.rows_written,25);self.assertEqual(len(written),25);self.assertEqual(sizes,[10,10,5])

try:
    import zmq, zmq.asyncio
    ZMQ_AVAILABLE=True
except ImportError: ZMQ_AVAILABLE=False

@unittest.skipUnless(ZMQ_AVAILABLE,"optional dependency: install .[ipc]")
class ZeroMQTransportTests(unittest.IsolatedAsyncioTestCase):
    async def test_inproc_roundtrip(self):
        import zmq.asyncio
        from sentinel_runtime.zmq_bridge import receive_tick,send_tick
        ctx=zmq.asyncio.Context();receiver=ctx.socket(zmq.PULL);sender=ctx.socket(zmq.PUSH);endpoint="inproc://sentinel-unit-test"
        receiver.bind(endpoint);sender.connect(endpoint)
        try:
            expected=Tick("BTC-USD",5,10000,99,101);await send_tick(sender,expected)
            self.assertEqual(await asyncio.wait_for(receive_tick(receiver),timeout=1.0),expected)
        finally: sender.close(0);receiver.close(0);ctx.term()

try:
    import duckdb
    DUCKDB_AVAILABLE=True
except ImportError: DUCKDB_AVAILABLE=False

@unittest.skipUnless(DUCKDB_AVAILABLE,"optional dependency: install .[storage]")
class DuckDBLoggerTests(unittest.IsolatedAsyncioTestCase):
    async def test_async_writer_persists_all_rows(self):
        import tempfile,duckdb
        from pathlib import Path
        from sentinel_runtime.duckdb_logger import AsyncDuckDBTickLogger
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"ticks.duckdb";logger=AsyncDuckDBTickLogger(path,batch_size=10,queue_size=20)
            await logger.start();await logger.log_many([Tick("X",i,i+1,99,101) for i in range(25)]);await logger.close()
            con=duckdb.connect(str(path),read_only=True)
            try:self.assertEqual(con.execute("select count(*) from ticks").fetchone()[0],25)
            finally:con.close()

if __name__=="__main__": unittest.main()
