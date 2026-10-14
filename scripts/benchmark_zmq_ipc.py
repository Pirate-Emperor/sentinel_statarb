#!/usr/bin/env python3
"""Measure ZeroMQ process-to-process IPC round-trip latency after warm-up."""
from __future__ import annotations
import argparse,json,multiprocessing as mp,statistics,tempfile,time
from pathlib import Path
def server(endpoint,count):
    import zmq
    ctx=zmq.Context();sock=ctx.socket(zmq.PAIR);sock.setsockopt(zmq.LINGER,0);sock.bind(endpoint)
    try:
        for _ in range(count):
            msg=sock.recv();sock.send(msg)
    finally:sock.close(0);ctx.term()
def percentile(values,p):
    values=sorted(values);return values[min(len(values)-1,int((len(values)-1)*p))]/1000.0
def benchmark(count,warmup):
    import zmq
    with tempfile.TemporaryDirectory(prefix="sentinel-zmq-") as directory:
        endpoint=f"ipc://{directory}/roundtrip.sock";ctx_mp=mp.get_context("spawn")
        worker=ctx_mp.Process(target=server,args=(endpoint,count+warmup),daemon=True);worker.start()
        ctx=zmq.Context();sock=ctx.socket(zmq.PAIR);sock.setsockopt(zmq.LINGER,0);sock.setsockopt(zmq.SNDHWM,256);sock.setsockopt(zmq.RCVHWM,256);sock.connect(endpoint)
        samples=[];start_total=end_total=0
        try:
            for i in range(count+warmup):
                payload=str(i).encode("ascii");start=time.perf_counter_ns() if i>=warmup else 0
                if i==warmup:start_total=start
                sock.send(payload);reply=sock.recv()
                if reply!=payload:raise RuntimeError(f"IPC payload mismatch at sequence {i}")
                if i>=warmup:end_total=time.perf_counter_ns();samples.append(end_total-start)
        finally:
            sock.close(0);ctx.term();worker.join(timeout=10)
            if worker.is_alive():worker.terminate();worker.join()
        if worker.exitcode!=0:raise RuntimeError(f"ZeroMQ IPC worker exited with code {worker.exitcode}")
    duration=end_total-start_total
    return {"transport":"ZeroMQ ipc:// PAIR socket","measurement":"process-to-process round-trip; includes Python and scheduler overhead",
        "warmup_messages":warmup,"measured_messages":count,"payload_check":"passed","mean_round_trip_us":statistics.mean(samples)/1000.0,
        "p50_round_trip_us":percentile(samples,0.50),"p95_round_trip_us":percentile(samples,0.95),"p99_round_trip_us":percentile(samples,0.99),
        "max_round_trip_us":max(samples)/1000.0,"throughput_round_trips_per_second":count/(duration/1e9),
        "timed_sample_count":len(samples),"measured_duration_ms":duration/1e6,
        "note":"Machine-dependent round-trip; not one-way latency and not a lock-free guarantee."}
def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument("--ticks",type=int,default=20000);ap.add_argument("--warmup",type=int,default=2000)
    ap.add_argument("--out",type=Path,default=Path("artifacts/zmq_ipc_benchmark.json"));a=ap.parse_args()
    if a.ticks<1 or a.warmup<0:ap.error("--ticks must be positive and --warmup non-negative")
    result=benchmark(a.ticks,a.warmup);a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,indent=2));return 0
if __name__=="__main__":raise SystemExit(main())
