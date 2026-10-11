#!/usr/bin/env python3
"""Run repeatable simulation checks and refresh CSV/JSON reports."""
from __future__ import annotations
import argparse,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from sentinel_runtime.experiments import run_experiments,write_reports
def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument("--ticks",type=int,default=100000)
    ap.add_argument("--repeats",type=int,default=3);ap.add_argument("--seed",type=int,default=20261011)
    ap.add_argument("--out",type=Path,default=ROOT/"artifacts");a=ap.parse_args()
    r=run_experiments(a.ticks,a.repeats,a.seed);write_reports(r,a.out)
    print(f"Base ticks: {r['base_tick_count']:,}; input events: {r['input_event_count_with_duplicates']:,}")
    print("Policy                 events/s     accepted     debounced     sampled p95 (us)")
    for x in r["policies"]:print(f"{x['policy']:<22} {x['events_per_second']:>10,.0f} {x['accepted_signals']:>12,} {x['debounced_signals']:>13,} {x['sampled_latency_p95_us']:>18.3f}")
    print(f"Reports written to {a.out}");print("Synthetic results only; timing varies by machine.");return 0
if __name__=="__main__":raise SystemExit(main())
