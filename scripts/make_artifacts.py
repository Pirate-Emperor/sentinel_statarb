#!/usr/bin/env python3
"""Generate readable SVG diagrams from the saved experiment reports."""
import html,json,random
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
    # Build the plotted path from the same seeded synthetic stream used by experiments.py.
    count=int(d["base_tick_count"]);crash_at=max(1,int(count*float(d["crash_at_fraction"])))
    rng=random.Random(int(d["seed"]));stride=max(1,count//180);points=[]
    for i in range(count):
        regime=98.2 if i>=crash_at else 100.0
        price=regime*(1.0+rng.uniform(-0.000025,0.000025))
        if i%stride==0 or i in (crash_at-1,crash_at,count-1):points.append((i,price))
    x0,x1,y0,y1=82.0,1110.0,170.0,385.0
    low,high=97.8,100.4
    def px(i):return x0+(x1-x0)*i/max(1,count-1)
    def py(price):return y1-(price-low)/(high-low)*(y1-y0)
    trace=" ".join(("M" if index==0 else "L")+f"{px(i):.2f},{py(price):.2f}" for index,(i,price) in enumerate(points))
    s=['<rect width="1200" height="520" fill="#101827"/>',
        t(40,45,"FLASH-CRASH REPLAY / SEEDED SYNTHETIC PRICES",16,"#72d9be",700),
        t(40,84,"The 180 bps gap moves through the stop-limit price",27,"#f4f7fb",700),
        t(40,116,f"{count:,} base ticks · price step at {100*float(d['crash_at_fraction']):.0f}% of the stream",15,"#aab8ce")]
    for tick in (100.0,99.0,98.0):
        y=py(tick)
        s += [f'<path d="M{x0} {y:.2f} H{x1}" stroke="#263348" stroke-width="1"/>',
              t(24,y+5,f"{tick:.0f}",13,"#aab8ce")]
    stop=100.0*(1.0-25.0/10000.0);limit=stop*(1.0-5.0/10000.0)
    s += [f'<path d="M{x0} {py(stop):.2f} H{x1}" stroke="#ffbd78" stroke-width="2" stroke-dasharray="10 7"/>',
          f'<path d="M{x0} {py(limit):.2f} H{x1}" stroke="#f28f7d" stroke-width="2" stroke-dasharray="4 5"/>',
          f'<path d="{trace}" fill="none" stroke="#64c8e6" stroke-width="3" stroke-linejoin="round" stroke-linecap="round"/>',
          t(x0,415,"START",13,"#aab8ce"),t(px(crash_at),415,"GAP",13,"#f28f7d",700),
          t(x1-35,415,"END",13,"#aab8ce"),
          rect(80,440,235,42,"#222f40","#40536c",7),
          t(96,467,f"STOP  {stop:.2f}",14,"#ffbd78",700),
          rect(332,440,285,42,"#222f40","#40536c",7),
          t(348,467,f"SELL LIMIT  {limit:.4f}",14,"#f28f7d",700),
          rect(634,440,500,42,"#222f40","#40536c",7),
          t(650,467,"Observed price after gap: 98.20 · not marketable",14,"#f3f6fb",700),
          t(40,505,"Synthetic replay only; it shows why a stop trigger cannot guarantee a fill.",14,"#c8d2e1")]
    save("flash-crash-analysis.svg",1200,520,s)
    rows=d["oco_gap_sweep"];gaps=sorted({float(q["gap_bps"]) for q in rows});offs=sorted({float(q["offset_bps"]) for q in rows})
    lookup={(float(q["offset_bps"]),float(q["gap_bps"])):bool(q["marketable"]) for q in rows}
    s=['<rect width="1200" height="480" fill="#f2f5f8"/>',
       t(40,50,"OCO STOP-LIMIT / GAP SWEEP",16,"#177362",700),
       t(40,90,"Can the limit trade after a gap?",28,"#172c34",700),
       t(40,124,"YES means marketable in this price check; it does not guarantee an execution.",15,"#52656d")]
    x0,y0,cw,ch=220,165,110,60
    for j,g in enumerate(gaps):s.append(t(x0+j*cw+cw/2,151,f"{g:g}",14,"#52656d",700))
    for i,o in enumerate(offs):
        y=y0+i*ch;s.append(t(50,y+34,f"Offset {o:g} bps",16,"#172c34",700))
        for j,g in enumerate(gaps):
            ok=lookup[(o,g)]
            s += [rect(x0+j*cw,y,cw-5,ch-5,"#bfead9" if ok else "#f7d8ce","#2e9b78" if ok else "#d5806d",6),
                  t(x0+j*cw+35,y+34,"YES" if ok else "NO",14,"#194a40" if ok else "#8e3e32",700)]
    save("oco-gap-sweep.svg",1200,480,s)

def latency(name,report,kind):
    d=json.loads(report.read_text())
    if kind=="zmq":
        values=[("P50",float(d["p50_round_trip_us"])),("P95",float(d["p95_round_trip_us"])),("P99",float(d["p99_round_trip_us"]))]
        title="ZERO MQ IPC / PROCESS-TO-PROCESS ROUND TRIP";sub=f"{d['measured_messages']:,} measured messages after {d['warmup_messages']:,} warm-up messages"
    else:
        values=[("P50",float(d["sampled_processing_p50_us"])),("P95",float(d["sampled_processing_p95_us"])),("P99",float(d["sampled_processing_p99_us"]))]
        title=f"NATIVE C++ / {int(d.get('ticks', d.get('measured_ticks', 0))):,} TICK RUN";sub=f"{int(d['measured_ticks']):,} measured ticks after {int(d.get('warmup_ticks', 0)):,} warm-up · {float(d['measured_throughput_events_per_second']):,.0f} events/s"
    cols=["#5a9bd8","#df9c47","#ca6a66"];mx=max(v for _,v in values) or 1
    s=['<rect width="1100" height="430" fill="#101827"/>',t(40,50,title,15,"#72d9be",700),t(40,91,sub,21,"#f3f6fb",700)]
    for i,((label,v),c) in enumerate(zip(values,cols)):
        y=145+i*75;s += [t(48,y+27,label,16,c,700),rect(160,y,700*v/mx,40,c,c,7),t(175+700*v/mx,y+27,f"{v:.3f} us",17,"#f3f6fb",700)]
    note="Round trip includes Python and scheduler time; not one-way latency." if kind=="zmq" else "Processing latency is sampled; timings depend on the machine."
    s += [rect(40,375,1020,35,"#202c3d","#40536c",8),t(60,399,note,15,"#c8d2e1")]
    save(name,1100,430,s)
def data_quality(d):
    p=next(row for row in d["policies"] if row["policy"]=="dynamic debounce")
    total=int(p["input_events"])
    valid=int(p["accepted_signals"])+int(p["debounced_signals"])
    rejected=total-valid
    passed_w=1070*valid/total if total else 0
    counts=[
        ("Duplicate sequence",int(p["duplicate_sequences"]),"#d97b68"),
        ("Old timestamp",int(p["out_of_order_timestamps"]),"#dfaa4a"),
        ("Stale quote",int(p["stale_quotes"]),"#9b87d8"),
        ("Future quote",int(p["future_quotes"]),"#62b6d7"),
    ]
    parts=['<rect width="1200" height="640" fill="#f3f6f8"/>',
        t(40,48,"DATA QUALITY / REJECTED QUOTE COUNTS",16,"#17685c",700),
        t(40,88,"Every event is accounted for before signal control",28,"#1b2d33",700),
        rect(40,118,1120,168,"#ffffff","#d6e0e5"),
        t(64,157,"INPUT STREAM",15,"#17685c",700),
        t(64,188,f"{total:,} events",25,"#1b2d33",700),
        rect(64,205,1070,28,"#e7edf1","#e7edf1",6),
        rect(64,205,passed_w,28,"#4aa889","#4aa889",6),
        t(64,257,f"Passed quote checks: {valid:,} ({100*valid/total:.2f}%)",16,"#17685c",700),
        t(650,257,f"Rejected before signal: {rejected:,} ({100*rejected/total:.2f}%)",16,"#a24f41",700)]
    for i,(label,count,color) in enumerate(counts):
        x=40+i*280
        parts += [rect(x,306,250,96,"#ffffff","#d6e0e5"),
            t(x+16,339,label,14,color,700),
            t(x+16,378,f"{count:,}",27,"#1b2d33",700)]
    accepted=int(p["accepted_signals"]);held=int(p["debounced_signals"])
    accepted_w=1070*accepted/valid if valid else 0
    parts += [rect(40,424,1120,174,"#ffffff","#d6e0e5"),
        t(64,463,"SIGNAL DEBOUNCER / VALID QUOTES ONLY",15,"#5f4a9c",700),
        t(64,494,f"{valid:,} valid quotes",19,"#1b2d33",700),
        rect(64,512,1070,30,"#ebe8f8","#ebe8f8",6),
        rect(64,512,accepted_w,30,"#4aa889","#4aa889",6),
        t(64,568,f"Accepted: {accepted:,} ({100*accepted/valid:.2f}%)",16,"#17685c",700),
        t(590,568,f"Held back: {held:,} ({100*held/valid:.2f}%)",16,"#5f4a9c",700),
        t(40,624,"The risk check still runs on every quote that passes quote-quality validation.",15,"#52656d")]
    save("data-quality.svg",1200,640,parts)

def performance_comparison(d):
    rows=d["policies"]
    colors=["#3988a8","#8c79c8","#399b7d"]
    max_rate=max(float(row["events_per_second"]) for row in rows) or 1
    parts=['<rect width="1200" height="560" fill="#101827"/>',
        t(40,48,"PERFORMANCE / POLICY COMPARISON",16,"#72d9be",700),
        t(40,89,"Throughput and sampled processing latency",28,"#f3f6fb",700),
        t(40,121,"Throughput includes synthetic input generation; latency is sampled around engine.process().",15,"#aab8ce")]
    for row,y,color in zip(rows,[177,292,407],colors):
        rate=float(row["events_per_second"])
        p95=float(row["sampled_latency_p95_us"])
        p99=float(row["sampled_latency_p99_us"])
        parts += [rect(40,y-32,1120,94,"#1a2638"),
            t(62,y-3,row["policy"].upper(),16,color,700),
            rect(285,y-19,450,22,"#2b384d","#2b384d",5),
            rect(285,y-19,450*rate/max_rate,22,color,color,5),
            t(285,y+29,f"{rate:,.0f} events/s",16,"#f3f6fb",700),
            t(790,y-2,f"P95 {p95:.3f} us",16,"#f3f6fb",700),
            t(985,y-2,f"P99 {p99:.3f} us",16,"#c8d2e1",700),
            t(790,y+29,f"{int(row['accepted_signals']):,} accepted · {int(row['debounced_signals']):,} held",13,"#aab8ce")]
    parts += [t(40,526,"Machine-specific synthetic test; use the same machine and settings for comparisons.",15,"#aab8ce")]
    save("performance-comparison.svg",1200,560,parts)

def experiment_pipeline():
    parts=['<rect width="1200" height="520" fill="#f2f5f7"/>',
        t(40,48,"EXPERIMENT PIPELINE / REPEATABLE STEPS",16,"#17685c",700),
        t(40,88,"From synthetic quotes to checked reports",28,"#1b2d33",700)]
    cards=[
        (40,"1 · GENERATE",["Seeded quote stream","Known 180 bps gap"]),
        (270,"2 · INJECT",["Repeat sequences","Old / stale quotes"]),
        (500,"3 · COMPARE",["No / fixed / dynamic","debounce policies"]),
        (730,"4 · MEASURE",["Warm-up excluded","Timed repeats"]),
        (960,"5 · CHECK",["Counts + price rules","CSV / JSON / SVG"]),
    ]
    for x,title,lines in cards:
        parts += [rect(x,150,200,150,"#ffffff","#8ba7b2"),
            t(x+14,184,title,14,"#17685c",700),
            t(x+14,225,lines[0],14,"#23323a"),
            t(x+14,252,lines[1],14,"#23323a")]
    for x in [240,470,700,930]:
        parts.append(f'<path d="M{x} 225 h24 l-7 -6 m7 6 l-7 6" fill="none" stroke="#506a73" stroke-width="2.5"/>')
    parts += [rect(40,354,1120,93,"#e3eee9","#b5d1c6"),
        t(64,391,"REPEATABLE INPUTS",15,"#17685c",700),
        t(64,422,"Same seed and count; measured runs follow one warm-up run per policy.",17,"#23323a"),
        t(40,489,"All outputs are simulations. They do not place live orders or guarantee fills.",15,"#52656d")]
    save("experiment-pipeline.svg",1200,520,parts)

def storage_chart(report):
    data=json.loads(report.read_text())
    rows=int(data["rows_read_back"])
    throughput=float(data["rows_per_second"])
    parts=['<rect width="1100" height="420" fill="#101827"/>',
        t(40,48,"DUCKDB / VERIFIED BATCH WRITE",16,"#72d9be",700),
        t(40,90,f"{rows:,} rows read back",28,"#f3f6fb",700),
        t(40,124,f"Separate warm-up: {int(data['warmup_row_count']):,} rows · batch size {int(data['batch_size']):,}",16,"#aab8ce"),
        rect(40,160,1020,100,"#1a2638"),
        t(65,197,f"Measured throughput: {throughput:,.0f} rows/s",22,"#f3f6fb",700),
        t(65,231,f"Read-back sequences: {int(data['first_sequence']):,} to {int(data['last_sequence']):,}",16,"#c8d2e1"),
        rect(40,292,1020,77,"#1a2638"),
        t(65,325,f"Elapsed: {float(data['elapsed_ms']):,.1f} ms  ·  Database: {int(data['database_bytes']):,} bytes",16,"#c8d2e1"),
        t(40,402,"This chart is generated only when a verified storage_benchmark.json report exists.",13,"#aab8ce")]
    save("storage-benchmark.svg",1100,420,parts)

def one_way_latency(report):
    d=json.loads(report.read_text())
    values=[
        ("P50",float(d["p50_one_way_us"]),"#5a9bd8"),
        ("P95",float(d["p95_one_way_us"]),"#df9c47"),
        ("P99",float(d["p99_one_way_us"]),"#ca6a66"),
    ]
    target_met=values[0][1] < 10.0
    maximum=max(10.0,max(v for _,v,_ in values))
    s=['<rect width="1120" height="500" fill="#101827"/>',
       t(40,48,"NATIVE C++ / ZERO MQ IPC ONE-WAY LATENCY",16,"#72d9be",700),
       t(40,89,f"{int(d['measured_messages']):,} measured messages after {int(d['warmup_messages']):,} warm-up",22,"#f3f6fb",700),
       t(40,121,"C++ sender and receiver processes · IPC socket · same-host monotonic clock",15,"#aab8ce")]
    for i,(label,value,color) in enumerate(values):
        y=170+i*78
        s += [t(48,y+25,label,16,color,700),
              rect(150,y,730,38,"#2b384d","#2b384d",6),
              rect(150,y,730*value/maximum,38,color,color,6),
              t(min(910,165+730*value/maximum),y+25,f"{value:.3f} us",17,"#f3f6fb",700)]
    s += [rect(40,414,1040,42,"#202c3d","#40536c",8),
          t(60,441,"Sub-10 us p50: " + ("MET on this run" if target_met else "NOT MET on this run"),16,"#72d9be" if target_met else "#ffbc78",700),
          t(40,485,"Machine-dependent measurement; ZeroMQ itself is not a lock-free transport.",14,"#c8d2e1")]
    save("zmq-ipc-oneway-latency.svg",1120,500,s)

def storage_sweep_chart(report):
    data=json.loads(report.read_text())
    rows=sorted(data["results"],key=lambda row:int(row["batch_size"]))
    maximum=max(float(row["rows_per_second"]) for row in rows) or 1
    parts=['<rect width="1120" height="470" fill="#101827"/>',
        t(40,48,"DUCKDB / BATCH-SIZE EXPERIMENT",16,"#72d9be",700),
        t(40,89,f"{int(data['ticks_per_run']):,} ticks per run · one warm-up and one measured run",22,"#f3f6fb",700),
        t(40,121,"Every measured database is read back and sequence-checked.",15,"#aab8ce")]
    colors=["#64c8e6","#b39cf4","#68dca7"]
    for index,row in enumerate(rows):
        y=180+index*88
        rate=float(row["rows_per_second"])
        parts += [rect(40,y-31,1040,70,"#1a2638"),
            t(60,y-5,f"Batch {int(row['batch_size']):,}",16,colors[index],700),
            rect(250,y-20,500,22,"#2b384d","#2b384d",5),
            rect(250,y-20,500*rate/maximum,22,colors[index],colors[index],5),
            t(250,y+23,f"{rate:,.0f} rows/s",15,"#f3f6fb",700),
            t(800,y-2,f"P95 not sampled · {int(row['rows_read_back']):,} rows verified",14,"#c8d2e1")]
    parts += [t(40,450,"Machine-specific result; use the same hardware and tick count when comparing batch sizes.",14,"#aab8ce")]
    save("storage-batch-sweep.svg",1120,470,parts)

def shared_memory_latency(report):
    d=json.loads(report.read_text())
    values=[
        ("P50",float(d["p50_one_way_us"]),"#64c8e6"),
        ("P95",float(d["p95_one_way_us"]),"#b39cf4"),
        ("P99",float(d["p99_one_way_us"]),"#68dca7"),
    ]
    max_value=max(10.0,max(v for _,v,_ in values))
    passed=float(d["p50_one_way_us"])<10.0
    parts=['<rect width="1120" height="500" fill="#101827"/>',
        t(40,48,"LOCK-FREE IPC / SHARED-MEMORY SPSC RING",16,"#72d9be",700),
        t(40,89,f"{int(d['measured_messages']):,} measured messages after {int(d['warmup_messages']):,} warm-up",22,"#f3f6fb",700),
        t(40,121,"Producer and consumer are separate processes sharing one memory mapping.",15,"#aab8ce")]
    for index,(label,value,color) in enumerate(values):
        y=170+index*75
        parts += [t(48,y+26,label,16,color,700),
            rect(150,y,730,38,"#2b384d","#2b384d",6),
            rect(150,y,730*value/max_value,38,color,color,6),
            t(min(910,165+730*value/max_value),y+25,f"{value:.3f} us",17,"#f3f6fb",700)]
    parts += [rect(40,414,1040,42,"#202c3d","#40536c",8),
        t(60,441,"Sub-10 us p50: "+("MET on this run" if passed else "NOT MET on this run"),16,"#72d9be" if passed else "#ffbc78",700),
        t(40,485,"The chart checks lock-free atomics separately from ZeroMQ socket measurements.",14,"#c8d2e1")]
    save("shm-spsc-ipc-latency.svg",1120,500,parts)

def main():
    d=json.loads((R/"artifacts"/"experiment_summary.json").read_text())
    architecture();flow();dashboard(d);charts(d)
    data_quality(d);performance_comparison(d);experiment_pipeline()
    zmq_report=R/"artifacts"/"zmq_ipc_benchmark.json"
    if zmq_report.exists():latency("zmq-ipc-latency.svg",zmq_report,"zmq")
    native_oneway=R/"artifacts"/"cpp_zmq_ipc_oneway_benchmark.json"
    if native_oneway.exists():one_way_latency(native_oneway)
    shared_memory=R/"artifacts"/"shm_spsc_ipc_benchmark.json"
    if shared_memory.exists():shared_memory_latency(shared_memory)
    cpp_report=R/"artifacts"/"cpp_benchmark.json"
    if not cpp_report.exists():cpp_report=R/"artifacts"/"cpp_benchmark_10m.json"
    if cpp_report.exists():latency("cpp-benchmark.svg",cpp_report,"cpp")
    storage_report=R/"artifacts"/"storage_benchmark.json"
    if storage_report.exists():storage_chart(storage_report)
    sweep_report=R/"artifacts"/"storage_batch_sweep.json"
    if sweep_report.exists():storage_sweep_chart(sweep_report)
    print(f"Generated SVG reports in {A}")
if __name__=="__main__":main()
