#!/usr/bin/env python3
"""Generate readable SVG diagrams from the saved experiment reports."""
import html,json
from pathlib import Path
R=Path(__file__).resolve().parents[1];A=R/"docs"/"assets";A.mkdir(parents=True,exist_ok=True)
def t(x,y,s,size=18,color="#eaf0f8",weight=400):
    return f'<text x="{x}" y="{y}" font-family="Arial,sans-serif" font-size="{size}" font-weight="{weight}" fill="{color}">{html.escape(str(s))}</text>'
def rect(x,y,w,h,color,stroke="#44546a",r=12):
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{color}" stroke="{stroke}" stroke-width="2"/>'
def save(name,w,h,parts):
    (A/name).write_text(f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">\n'+"\n".join(parts)+"\n</svg>\n")
def architecture():
    s=['<rect width="1200" height="600" fill="#0b1220"/>',t(45,55,"SENTINEL STATARB / SYSTEM MAP",16,"#72d9be",700),t(45,100,"Quotes in, checked decisions out",30,"#f4f7fb",700)]
    cards=[(45,"INPUT","#18334a",["Quotes + sequence","Freshness checks"]),(335,"RISK + SIGNAL","#193b35",["Adaptive debounce","OCO stop / target"]),(625,"ZERO MQ","#302646",["Validated JSON","IPC or TCP socket"]),(915,"NATIVE C++","#4a2d20",["SPSC ring","Measured queue speed"])]
    for x,name,c,lines in cards:
        s += [rect(x,155,235,140,c),t(x+16,188,name,16,"#78dcca",700),t(x+16,230,lines[0],17),t(x+16,260,lines[1],17)]
    for x in [282,572,862]:s.append(f'<path d="M{x} 225 h42 l-9 -8 m9 8 l-9 8" stroke="#91a5bd" stroke-width="3" fill="none"/>')
    s += [rect(45,355,530,150,"#151f30"),t(70,397,"ASYNC STORAGE",16,"#72d9be",700),t(70,435,"DuckDB batches + bounded queue",22),t(70,470,"Back-pressure protects records from silent loss.",16),rect(610,355,535,150,"#151f30"),t(635,397,"TESTS + REPORTS",16,"#ffb36c",700),t(635,435,"Python checks · C++ queue test · OCO gap grid",19),t(635,470,"Saved results: CSV, JSON and SVG.",16),t(45,560,"ZeroMQ IPC and the in-process queue are different paths; their timings are not the same.",15,"#f6c778")]
    save("architecture.svg",1200,600,s)
def flow():
    s=['<rect width="1200" height="560" fill="#f4f0e7"/>',t(45,55,"QUOTE HANDLING / EXECUTION TRACE",16,"#17685c",700),t(45,98,"Protective checks do not wait for the signal gate",29,"#1b2d33",700)]
    cards=[(45,"1  RECEIVE",["One quote","Bid / ask / sequence"]),(340,"2  VALIDATE",["Check time","Reject repeats"]),(635,"3  CHECK RISK",["Stop + target","Every valid quote"]),(930,"4  SIGNAL",["Pass or debounce","Strategy signal"])]
    for x,title,lines in cards:
        s += [rect(x,155,225,120,"#ffffff","#247d75"),t(x+14,190,title,16,"#247d75",700),t(x+14,228,lines[0],17,"#23323a"),t(x+14,255,lines[1],17,"#23323a")]
    for x in [275,570,865]:s.append(f'<path d="M{x+3} 215 h48 l-10 -8 m10 8 l-10 8" stroke="#506a73" stroke-width="3" fill="none"/>')
    s += [rect(100,330,430,120,"#e4f5ed","#26836d"),t(125,370,"PROTECTIVE ORDER",16,"#17685c",700),t(125,408,"Stop trigger sets a limit; it does not promise a fill.",16,"#23323a"),rect(670,330,430,120,"#e7e4f8","#6f5cb5"),t(695,370,"SIGNAL + STORAGE",16,"#5f4a9c",700),t(695,408,"Signals are gated; valid ticks are batched.",16,"#23323a"),t(45,510,"A large gap can pass the stop-limit price and leave the order unfilled.",16,"#9f4d12",700)]
    save("execution-flow.svg",1200,560,s)
def dashboard(d):
    colors=["#64c8e6","#b39cf4","#68dca7"];pol=d["policies"];mx=max(float(p["events_per_second"]) for p in pol) or 1
    s=['<rect width="1200" height="580" fill="#101827"/>',t(40,50,"SYNTHETIC QUOTE EXPERIMENT",16,"#72d9be",700),t(40,93,f"{d['base_tick_count']:,} ticks | {d['measured_repeats_per_policy']} measured runs after warm-up",24,"#f3f6fb",700),t(40,124,"Machine-specific results; not live-market performance.",16,"#aab8ce")]
    for p,y,c in zip(pol,[155,270,385],colors):
        s += [rect(40,y,1120,92,"#1a2638"),t(62,y+30,p["policy"].upper(),16,c,700),t(62,y+65,f"{p['events_per_second']:,.0f} events/s",21),rect(335,y+22,360,23,"#2b384d","#2b384d",6),rect(335,y+22,360*float(p["events_per_second"])/mx,23,c,c,6),t(335,y+65,f"{p['accepted_signals']:,} accepted  |  {p['debounced_signals']:,} held",15),t(790,y+38,f"P95 {p['sampled_latency_p95_us']:.3f} us",17),t(790,y+66,f"repeat {p['duplicate_sequences']}  ·  old time {p['out_of_order_timestamps']}  ·  stale {p['stale_quotes']}",13,"#aab8ce")]
    s += [rect(40,510,1120,45,"#242b35","#4e5d70",8),t(60,538,"One stop triggered per policy; the 180 bps gap exceeded the 5 bps limit offset.",15,"#ffbc78",700)]
    save("experiment-dashboard.svg",1200,580,s)
def charts(d):
    # A compact price path makes the injected crash easy to compare to the stop and limit.
    s=['<rect width="1200" height="500" fill="#111827"/>',t(40,50,"FLASH-CRASH REPLAY / SYNTHETIC",16,"#71d8bf",700),t(40,90,"180 bps gap crosses the stop, then moves past the limit",25,"#f4f7fb",700),t(40,122,f"{d['base_tick_count']:,} base ticks; jump at 55% of the stream",16,"#aab8ce")]
    s += ['<path d="M80 190 H1135 M80 245 H1135 M80 300 H1135 M80 355 H1135" stroke="#263348"/>','<path d="M80 180 H650 V390 H1135" fill="none" stroke="#64c8e6" stroke-width="4"/>','<path d="M80 250 H1135" stroke="#ffbd78" stroke-width="3" stroke-dasharray="10 7"/>','<path d="M80 270 H1135" stroke="#f28f7d" stroke-width="3" stroke-dasharray="5 5"/>',t(90,430,"PRICE",14,"#64c8e6",700),t(200,430,"STOP 99.75",14,"#ffbd78",700),t(390,430,"SELL LIMIT 99.7001",14,"#f28f7d",700),t(40,475,"The synthetic crash falls below the sell limit: the order triggers but cannot trade at this price.",15,"#c8d2e1")]
    save("flash-crash-analysis.svg",1200,500,s)
    rows=d["oco_gap_sweep"];gaps=sorted({float(q["gap_bps"]) for q in rows});offs=sorted({float(q["offset_bps"]) for q in rows});lookup={(float(q["offset_bps"]),float(q["gap_bps"])):bool(q["marketable"]) for q in rows}
    s=['<rect width="1200" height="480" fill="#f2f5f8"/>',t(40,50,"OCO STOP-LIMIT / GAP SWEEP",16,"#177362",700),t(40,90,"Can the limit trade after a gap?",28,"#172c34",700),t(40,124,"YES means marketable in this simple price check; it does not guarantee an execution.",15,"#52656d")]
    x0,y0,cw,ch=220,165,110,60
    for j,g in enumerate(gaps):s.append(t(x0+j*cw+cw/2,151,f"{g:g}",14,"#52656d",700))
    for i,o in enumerate(offs):
        y=y0+i*ch;s.append(t(50,y+34,f"Offset {o:g} bps",16,"#172c34",700))
        for j,g in enumerate(gaps):
            ok=lookup[(o,g)];s += [rect(x0+j*cw,y,cw-5,ch-5,"#bfead9" if ok else "#f7d8ce","#2e9b78" if ok else "#d5806d",6),t(x0+j*cw+35,y+34,"YES" if ok else "NO",14,"#194a40" if ok else "#8e3e32",700)]
    save("oco-gap-sweep.svg",1200,480,s)
def latency(name,report,kind):
    d=json.loads(report.read_text())
    if kind=="zmq":
        values=[("P50",float(d["p50_round_trip_us"])),("P95",float(d["p95_round_trip_us"])),("P99",float(d["p99_round_trip_us"]))]
        title="ZERO MQ IPC / PROCESS-TO-PROCESS ROUND TRIP";sub=f"{d['measured_messages']:,} measured messages after {d['warmup_messages']:,} warm-up messages"
    else:
        values=[("P50",float(d["sampled_processing_p50_us"])),("P95",float(d["sampled_processing_p95_us"])),("P99",float(d["sampled_processing_p99_us"]))]
        title="NATIVE C++ / 10M TICK BENCHMARK";sub=f"{int(d['measured_ticks']):,} measured ticks · {float(d['measured_throughput_events_per_second']):,.0f} events/s"
    cols=["#5a9bd8","#df9c47","#ca6a66"];mx=max(v for _,v in values) or 1
    s=['<rect width="1100" height="430" fill="#101827"/>',t(40,50,title,15,"#72d9be",700),t(40,91,sub,21,"#f3f6fb",700)]
    for i,((label,v),c) in enumerate(zip(values,cols)):
        y=145+i*75;s += [t(48,y+27,label,16,c,700),rect(160,y,700*v/mx,40,c,c,7),t(175+700*v/mx,y+27,f"{v:.3f} us",17,"#f3f6fb",700)]
    note="Round trip includes Python and scheduler time; not one-way latency." if kind=="zmq" else "Processing latency is sampled; timings depend on the machine."
    s += [rect(40,375,1020,35,"#202c3d","#40536c",8),t(60,399,note,15,"#c8d2e1")]
    save(name,1100,430,s)
def main():
    d=json.loads((R/"artifacts"/"experiment_summary.json").read_text())
    architecture();flow();dashboard(d);charts(d)
    if (R/"artifacts"/"zmq_ipc_benchmark.json").exists():latency("zmq-ipc-latency.svg",R/"artifacts"/"zmq_ipc_benchmark.json","zmq")
    if (R/"artifacts"/"cpp_benchmark_10m.json").exists():latency("cpp-benchmark.svg",R/"artifacts"/"cpp_benchmark_10m.json","cpp")
    print(f"Generated SVG reports in {A}")
if __name__=="__main__":main()
