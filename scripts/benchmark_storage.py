#!/usr/bin/env python3
"""Stress the async DuckDB writer with a full warm-up then a measured run."""
from __future__ import annotations
import argparse,asyncio,json,random,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from sentinel_runtime.engine import Tick
from sentinel_runtime.duckdb_logger import AsyncDuckDBTickLogger
def make_batch(start,stop,seed):
    rng=random.Random(seed+start);price=100.0+(start%100000)*0.00001;rows=[]
    for seq in range(start,stop):
        price*=1.0+rng.uniform(-0.000001,0.000001)
        rows.append(Tick("STRESS-USD",seq,1700000000000000000+seq*10000,price-0.005,price+0.005))
    return rows
async def write_run(path,count,batch_size):
    if path.exists():path.unlink()
    logger=AsyncDuckDBTickLogger(path,batch_size=batch_size,queue_size=64);await logger.start()
    start=time.perf_counter_ns()
    for offset in range(0,count,batch_size):await logger.log_many(make_batch(offset,min(count,offset+batch_size),20261011))
    await logger.close();elapsed=time.perf_counter_ns()-start
    import duckdb
    con=duckdb.connect(str(path),read_only=True)
    try:
        rows=int(con.execute("SELECT COUNT(*) FROM ticks").fetchone()[0])
        distinct_sequences=int(con.execute("SELECT COUNT(DISTINCT sequence) FROM ticks").fetchone()[0])
        first,last=con.execute("SELECT MIN(sequence),MAX(sequence) FROM ticks").fetchone()
    finally:con.close()
    if rows!=count or logger.rows_written!=count or distinct_sequences!=count or first!=0 or last!=count-1:
        raise RuntimeError(
            f"storage check failed: wanted {count} unique rows 0..{count-1}; "
            f"logger={logger.rows_written}, read_back={rows}, unique={distinct_sequences}, range={first}..{last}"
        )
    return {"rows_requested":count,"rows_written_by_logger":logger.rows_written,"rows_read_back":rows,
        "distinct_sequences":distinct_sequences,"first_sequence":first,"last_sequence":last,
        "elapsed_ms":elapsed/1e6,"rows_per_second":count/(elapsed/1e9),"batch_size":batch_size,"database_bytes":path.stat().st_size}
async def run(count,batch_size,output):
    output.parent.mkdir(parents=True,exist_ok=True);warm=output.with_name(output.stem+".warmup.duckdb")
    try:await write_run(warm,count,batch_size)
    finally:
        for p in (warm,Path(str(warm)+".wal")):
            if p.exists():p.unlink()
    measured=await write_run(output,count,batch_size)
    report={"benchmark":"async_duckdb_tick_logging","warmup_runs":1,"measured_runs":1,"warmup_row_count":count,**measured}
    output.with_name("storage_benchmark.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    return report
def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument("--ticks",type=int,default=10000000)
    ap.add_argument("--batch-size",type=int,default=10000);ap.add_argument("--out",type=Path,default=ROOT/"artifacts"/"stress_ticks.duckdb");a=ap.parse_args()
    if a.ticks<1 or a.batch_size<1:ap.error("--ticks and --batch-size must be positive")
    try:import duckdb
    except ImportError as exc:
        print("DuckDB is not installed. Run: python -m pip install -e '.[storage]'",file=sys.stderr);print(exc,file=sys.stderr);return 2
    print(json.dumps(asyncio.run(run(a.ticks,a.batch_size,a.out)),indent=2));return 0
if __name__=="__main__":raise SystemExit(main())
