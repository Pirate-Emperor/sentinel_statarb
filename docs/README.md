# Sentinel StatArb figures and reports

Three compact SVG figures summarize the data path and the latest completed HPC measurement set. They are regenerated with:

```bash
python scripts/make_artifacts.py
python scripts/validate_reports.py
```

- [System path and subsystem boundaries](assets/architecture.svg)
- [HPC #9 benchmark snapshot: native throughput, paired pipeline, IPC, DuckDB](assets/performance-comparison.svg)
- [Crash-window signal gating and OCO gap behavior](assets/flash-crash-analysis.svg)
- [Detailed experiment methods and historical reference measurements](EXPERIMENTS.md)
- [HPC #9 validation report, host provenance, and run boundaries](HPC_VALIDATION_2026-10-14.md)

The figure values are pinned to the successful HPC #9 report and tested source revision `bd7f72c365fb9d40d2e90ac778cfde1005b68ff8`. They are reference measurements from synthetic inputs. Detailed CSV/JSON artifacts, raw repetitions, historical runs, and reproduction commands remain in the experiment ledger and the linked HPC artifact store.

The A100 GPUs were present on the host but unused by these CPU/IPC/storage benchmarks. Percentiles are not hard latency guarantees; signal gating is not P&L; and price marketability does not establish order execution.
