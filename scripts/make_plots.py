#!/usr/bin/env python3
"""Generate conventional, reproducible Matplotlib plots from Sentinel reports."""
from __future__ import annotations
import json
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import ListedColormap

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts"
OUT = ROOT / "docs" / "assets"
OUT.mkdir(parents=True, exist_ok=True)
PALETTE = {"blue":"#3568a8","teal":"#19877d","orange":"#d97736","slate":"#8795a5","grid":"#e3e8ee","text":"#243447","muted":"#627286"}
POLICY_COLORS = [PALETTE["slate"], PALETTE["blue"], PALETTE["teal"]]
plt.rcParams.update({"font.family":"DejaVu Sans","font.size":10,"axes.titlesize":13,"axes.titleweight":"semibold","axes.labelsize":10,"xtick.labelsize":9,"ytick.labelsize":9,"svg.fonttype":"none","svg.hashsalt":"sentinel-statarb","figure.facecolor":"white","axes.facecolor":"white","savefig.facecolor":"white","savefig.bbox":"tight"})

def read_json(name: str) -> dict:
    path = ARTIFACTS / name
    if not path.is_file():
        raise FileNotFoundError(f"Required report is missing: {path.relative_to(ROOT)}")
    with path.open(encoding="utf-8") as stream:
        return json.load(stream)

def style_axes(ax, horizontal: bool = False) -> None:
    ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color(PALETTE["grid"]); ax.spines["bottom"].set_color(PALETTE["grid"])
    ax.tick_params(colors=PALETTE["muted"], length=0, pad=6)
    if horizontal:
        ax.xaxis.grid(True, color=PALETTE["grid"], linewidth=0.8); ax.yaxis.grid(False)
    else:
        ax.yaxis.grid(True, color=PALETTE["grid"], linewidth=0.8); ax.xaxis.grid(False)
    ax.set_axisbelow(True)

def annotate_bars(ax, bars, fmt, horizontal: bool = False, pad: float = 0.02) -> None:
    span = (ax.get_xlim()[1]-ax.get_xlim()[0]) if horizontal else (ax.get_ylim()[1]-ax.get_ylim()[0])
    for bar in bars:
        if horizontal:
            value=bar.get_width()
            ax.text(value+span*pad,bar.get_y()+bar.get_height()/2,fmt(value),va="center",ha="left",color=PALETTE["text"],fontsize=9)
        else:
            value=bar.get_height()
            ax.text(bar.get_x()+bar.get_width()/2,value+span*pad,fmt(value),va="bottom",ha="center",color=PALETTE["text"],fontsize=8.5)

def save(fig, filename: str, source: str) -> None:
    # Use only the plot itself: no footnotes, decorative banners, or generated-image styling.
    # A fixed SVG metadata set also avoids nondeterministic timestamps in diffs.
    fig.savefig(
        OUT / filename,
        format="svg",
        bbox_inches="tight",
        metadata={
            "Title": filename.replace("-", " ").replace(".svg", ""),
            "Creator": "Matplotlib",
            "Date": None,
        },
    )
    plt.close(fig)

def make_policy_throughput(summary: dict) -> None:
    rows=summary["policies"]; labels=[r["policy"] for r in rows]; values=[float(r["events_per_second"])/1000 for r in rows]
    fig,ax=plt.subplots(figsize=(7.2,4.0),layout="constrained")
    bars=ax.bar(labels,values,color=POLICY_COLORS,width=0.62)
    ax.set_title("Quote-policy throughput",loc="left",color=PALETTE["text"],pad=12); ax.set_ylabel("Events per second (thousands)")
    ax.set_ylim(0,max(values)*1.2); style_axes(ax); annotate_bars(ax,bars,lambda v:f"{v:,.1f}K",pad=0.018)
    ax.text(0.99,0.98,f"{int(summary['input_event_count_with_duplicates']):,} input events per run",transform=ax.transAxes,ha="right",va="top",color=PALETTE["muted"],fontsize=8)
    save(fig,"policy-throughput.svg","artifacts/experiment_summary.json")

def make_policy_latency(summary: dict) -> None:
    rows=summary["policies"]; labels=[r["policy"] for r in rows]; x=np.arange(len(rows)); width=0.23
    quantiles=[("sampled_latency_p50_us","P50",PALETTE["blue"]),("sampled_latency_p95_us","P95",PALETTE["orange"]),("sampled_latency_p99_us","P99",PALETTE["teal"])]
    fig,ax=plt.subplots(figsize=(7.2,4.0),layout="constrained")
    for i,(key,label,color) in enumerate(quantiles):
        bars=ax.bar(x+(i-1)*width,[float(r[key]) for r in rows],width,label=label,color=color)
        for b in bars: ax.text(b.get_x()+b.get_width()/2,b.get_height()+0.035,f"{b.get_height():.2f}",ha="center",va="bottom",fontsize=7.5,color=PALETTE["text"])
    ax.set_xticks(x,labels); ax.set_ylabel("Sampled processing latency (μs)")
    ax.set_title("Quote-policy latency percentiles",loc="left",color=PALETTE["text"],pad=12); ax.legend(frameon=False,ncol=3,loc="upper left")
    ax.set_ylim(0,max(float(r["sampled_latency_p99_us"]) for r in rows)*1.28); style_axes(ax)
    save(fig,"policy-latency-percentiles.svg","artifacts/experiment_summary.json")

def make_signal_counts(summary: dict) -> None:
    rows=summary["policies"]; labels=[r["policy"] for r in rows]
    accepted=np.array([int(r["accepted_signals"]) for r in rows]); held=np.array([int(r["debounced_signals"]) for r in rows])
    fig,ax=plt.subplots(figsize=(7.2,4.0),layout="constrained"); y=np.arange(len(rows))
    ax.barh(y,accepted,color=PALETTE["blue"],label="Accepted"); ax.barh(y,held,left=accepted,color=PALETTE["orange"],label="Debounced")
    ax.set_yticks(y,labels); ax.invert_yaxis(); ax.set_xlabel("Signal count")
    ax.set_title("Signal gating by policy",loc="left",color=PALETTE["text"],pad=12)
    ax.text(0.99,0.98,"Blue = accepted · Orange = debounced",transform=ax.transAxes,ha="right",va="top",fontsize=8,color=PALETTE["muted"])
    ax.set_xlim(0,max(accepted+held)*1.22); style_axes(ax,horizontal=True)
    for i,(a,h) in enumerate(zip(accepted,held)):
        ax.text(a/2,i,f"{a:,}",color="white",va="center",ha="center",fontsize=8.5,fontweight="semibold")
        if h>0: ax.text(a+h/2,i,f"{h:,}",color="white",va="center",ha="center",fontsize=8.5,fontweight="semibold")
    save(fig,"signal-gating-counts.svg","artifacts/experiment_summary.json")

def make_quality_faults(summary: dict) -> None:
    row=summary["policies"][0]; names=["Duplicate sequence","Out-of-order timestamp","Stale quote","Future timestamp"]
    keys=["duplicate_sequences","out_of_order_timestamps","stale_quotes","future_quotes"]; values=[int(row[k]) for k in keys]
    fig,ax=plt.subplots(figsize=(7.2,4.0),layout="constrained"); y=np.arange(len(names))
    bars=ax.barh(y,values,color=[PALETTE["blue"],PALETTE["teal"],PALETTE["orange"],PALETTE["slate"]],height=0.62)
    ax.set_yticks(y,names); ax.invert_yaxis(); ax.set_xlabel("Injected / observed events")
    ax.set_title("Quote-quality fault counts",loc="left",color=PALETTE["text"],pad=12); ax.set_xlim(0,max(values+[1])*1.22)
    style_axes(ax,horizontal=True); annotate_bars(ax,bars,lambda v:f"{int(v):,}",horizontal=True,pad=0.015)
    save(fig,"quote-quality-faults.svg","artifacts/experiment_summary.json")

def make_gap_boundary(summary: dict) -> None:
    rows=summary["oco_gap_sweep"]; offsets=sorted({float(r["offset_bps"]) for r in rows}); gaps=sorted({float(r["gap_bps"]) for r in rows})
    matrix=np.array([[int(bool(next(r["marketable"] for r in rows if float(r["offset_bps"])==o and float(r["gap_bps"])==g))) for g in gaps] for o in offsets])
    fig,ax=plt.subplots(figsize=(7.2,3.7),layout="constrained")
    ax.imshow(matrix,aspect="auto",cmap=ListedColormap(["#f6e5df","#d8eee8"]),vmin=0,vmax=1)
    ax.set_xticks(np.arange(len(gaps)),[f"{g:g}" for g in gaps]); ax.set_yticks(np.arange(len(offsets)),[f"{o:g} bps" for o in offsets])
    ax.set_xlabel("Injected price gap (bps)"); ax.set_ylabel("Stop-limit offset")
    ax.set_title("Stop-limit marketability boundary",loc="left",color=PALETTE["text"],pad=12)
    for i in range(len(offsets)):
        for j in range(len(gaps)):
            okay=bool(matrix[i,j]); ax.text(j,i,"Yes" if okay else "No",ha="center",va="center",fontsize=8.5,color="#1f514c" if okay else "#873d32")
    ax.set_xticks(np.arange(-0.5,len(gaps),1),minor=True); ax.set_yticks(np.arange(-0.5,len(offsets),1),minor=True)
    ax.grid(which="minor",color="white",linewidth=2); ax.tick_params(which="minor",bottom=False,left=False); ax.tick_params(colors=PALETTE["muted"],length=0,pad=7)
    for spine in ax.spines.values(): spine.set_visible(False)
    save(fig,"stop-limit-gap-boundary.svg","artifacts/experiment_summary.json · OCO sweep")

def make_cpp_throughput() -> None:
    row=read_json("cpp_benchmark_10m.json"); ticks=int(row["ticks"]); warmup=int(row["warmup_ticks"]); measured=int(row["measured_ticks"])
    rate=float(row["measured_throughput_events_per_second"])/1e6
    fig,ax=plt.subplots(figsize=(7.2,3.8),layout="constrained"); bars=ax.bar(["Native C++17"],[rate],color=PALETTE["blue"],width=0.42)
    ax.set_ylabel("Measured throughput (million events/s)"); ax.set_title("Native C++ event throughput",loc="left",color=PALETTE["text"],pad=12)
    ax.set_ylim(0,rate*1.27); style_axes(ax); annotate_bars(ax,bars,lambda v:f"{v:.2f}M events/s",pad=0.02)
    ax.text(0.99,0.96,f"{ticks:,} total · {measured:,} measured · {warmup:,} warm-up",transform=ax.transAxes,ha="right",va="top",fontsize=8,color=PALETTE["muted"])
    save(fig,"cpp-throughput.svg","artifacts/cpp_benchmark_10m.json")

def make_cpp_latency() -> None:
    row=read_json("cpp_benchmark_10m.json"); labels=["P50","P95","P99"]
    values=[float(row[f"sampled_processing_{label.lower()}_us"]) for label in labels]
    fig,ax=plt.subplots(figsize=(7.2,3.8),layout="constrained"); bars=ax.bar(labels,values,color=[PALETTE["blue"],PALETTE["teal"],PALETTE["orange"]],width=0.5)
    ax.set_ylabel("Sampled processing latency (μs)"); ax.set_title("Native C++ sampled latency",loc="left",color=PALETTE["text"],pad=12)
    ax.set_ylim(0,max(values)*1.5); style_axes(ax); annotate_bars(ax,bars,lambda v:f"{v:.3f} μs",pad=0.02)
    ax.text(0.99,0.96,f"{int(row['latency_sample_count']):,} samples · hot path only",transform=ax.transAxes,ha="right",va="top",fontsize=8,color=PALETTE["muted"])
    save(fig,"cpp-latency-percentiles.svg","artifacts/cpp_benchmark_10m.json")

def make_zmq_latency() -> None:
    row=read_json("zmq_ipc_benchmark.json"); labels=["P50","P95","P99"]
    values=[float(row[f"p{p}_round_trip_us"]) for p in (50,95,99)]
    fig,ax=plt.subplots(figsize=(7.2,3.8),layout="constrained"); bars=ax.bar(labels,values,color=[PALETTE["blue"],PALETTE["teal"],PALETTE["orange"]],width=0.5)
    ax.set_ylabel("Process-to-process round-trip (μs)"); ax.set_title("ZeroMQ IPC round-trip latency",loc="left",color=PALETTE["text"],pad=12)
    ax.set_ylim(0,max(values)*1.35); style_axes(ax); annotate_bars(ax,bars,lambda v:f"{v:,.1f} μs",pad=0.02)
    ax.text(0.99,0.96,f"Max observed: {float(row['max_round_trip_us']):,.1f} μs · {int(row['measured_messages']):,} messages",transform=ax.transAxes,ha="right",va="top",fontsize=8,color=PALETTE["muted"])
    save(fig,"zmq-round-trip-latency.svg","artifacts/zmq_ipc_benchmark.json")

def main() -> int:
    summary=read_json("experiment_summary.json")
    make_policy_throughput(summary); make_policy_latency(summary); make_signal_counts(summary)
    make_quality_faults(summary); make_gap_boundary(summary); make_cpp_throughput(); make_cpp_latency(); make_zmq_latency()
    expected={"policy-throughput.svg","policy-latency-percentiles.svg","signal-gating-counts.svg","quote-quality-faults.svg","stop-limit-gap-boundary.svg","cpp-throughput.svg","cpp-latency-percentiles.svg","zmq-round-trip-latency.svg"}
    missing=sorted(name for name in expected if not (OUT/name).is_file())
    if missing: raise RuntimeError(f"Plot generation incomplete: missing {missing}")
    print(f"Generated {len(expected)} Matplotlib SVG plots in {OUT}")
    for name in sorted(expected): print(f"  {name}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
