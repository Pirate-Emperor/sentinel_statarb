#!/usr/bin/env python3
"""Write the three compact, pinned SVG figures used in the project reports."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "assets"
OUT.mkdir(parents=True, exist_ok=True)

FIGURES = {
    "architecture.svg": r'''<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="440" viewBox="0 0 1280 440"><defs><marker id="arrow" markerWidth="7" markerHeight="7" refX="5" refY="3.5" orient="auto"><path d="M0,0 L6,3.5 L0,7 Z" fill="#8291a2"/></marker></defs>
<rect x="0" y="0" width="1280" height="440" rx="0" fill="#ffffff" stroke="#ffffff" stroke-width="0"/>
<rect x="0" y="0" width="1280" height="1" rx="0" fill="#ffffff" stroke="#ffffff" stroke-width="0"/>
<text x="40" y="30" font-family="Inter,Arial,sans-serif" font-size="11" font-weight="700" fill="#275dad" text-anchor="start">SENTINEL STATARB / 01</text>
<text x="40" y="62" font-family="Inter,Arial,sans-serif" font-size="27" font-weight="700" fill="#172536" text-anchor="start">Event path &amp; subsystem boundaries</text>
<text x="40" y="86" font-family="Inter,Arial,sans-serif" font-size="13" font-weight="400" fill="#607184" text-anchor="start">Synthetic quote replay · deterministic tests · no broker connectivity</text>
<line x1="40" y1="101" x2="1240" y2="101" stroke="#d7e0e8" stroke-width="1"/>
<rect x="40" y="125" width="170" height="92" rx="4" fill="#f7f9fb" stroke="#d7e0e8" stroke-width="1"/>
<line x1="41" y1="128" x2="209" y2="128" stroke="#8a98a8" stroke-width="3"/>
<text x="54" y="154" font-family="Inter,Arial,sans-serif" font-size="16" font-weight="700" fill="#172536" text-anchor="start">Quote stream</text>
<text x="54" y="176" font-family="Inter,Arial,sans-serif" font-size="12" font-weight="400" fill="#607184" text-anchor="start">sequence · bid/ask</text>
<text x="54" y="195" font-family="Inter,Arial,sans-serif" font-size="12" font-weight="400" fill="#607184" text-anchor="start">event timestamp</text>
<rect x="245" y="125" width="205" height="92" rx="4" fill="#f7f9fb" stroke="#d7e0e8" stroke-width="1"/>
<line x1="246" y1="128" x2="449" y2="128" stroke="#275dad" stroke-width="3"/>
<text x="259" y="154" font-family="Inter,Arial,sans-serif" font-size="16" font-weight="700" fill="#172536" text-anchor="start">Integrity gate</text>
<text x="259" y="176" font-family="Inter,Arial,sans-serif" font-size="12" font-weight="400" fill="#607184" text-anchor="start">sequence strictly advances</text>
<text x="259" y="195" font-family="Inter,Arial,sans-serif" font-size="12" font-weight="400" fill="#607184" text-anchor="start">time order + freshness</text>
<rect x="485" y="125" width="190" height="92" rx="4" fill="#f7f9fb" stroke="#d7e0e8" stroke-width="1"/>
<line x1="486" y1="128" x2="674" y2="128" stroke="#275dad" stroke-width="3"/>
<text x="499" y="154" font-family="Inter,Arial,sans-serif" font-size="16" font-weight="700" fill="#172536" text-anchor="start">Event engine</text>
<text x="499" y="176" font-family="Inter,Arial,sans-serif" font-size="12" font-weight="400" fill="#607184" text-anchor="start">bounded queue</text>
<text x="499" y="195" font-family="Inter,Arial,sans-serif" font-size="12" font-weight="400" fill="#607184" text-anchor="start">C++ SPSC / Python queue</text>
<rect x="735" y="110" width="215" height="92" rx="4" fill="#f7f9fb" stroke="#d7e0e8" stroke-width="1"/>
<line x1="736" y1="113" x2="949" y2="113" stroke="#087e78" stroke-width="3"/>
<text x="749" y="139" font-family="Inter,Arial,sans-serif" font-size="16" font-weight="700" fill="#172536" text-anchor="start">Signal path</text>
<text x="749" y="161" font-family="Inter,Arial,sans-serif" font-size="12" font-weight="400" fill="#607184" text-anchor="start">adaptive debounce</text>
<text x="749" y="180" font-family="Inter,Arial,sans-serif" font-size="12" font-weight="400" fill="#607184" text-anchor="start">entry signals only</text>
<rect x="735" y="225" width="215" height="92" rx="4" fill="#f7f9fb" stroke="#d7e0e8" stroke-width="1"/>
<line x1="736" y1="228" x2="949" y2="228" stroke="#c45b25" stroke-width="3"/>
<text x="749" y="254" font-family="Inter,Arial,sans-serif" font-size="16" font-weight="700" fill="#172536" text-anchor="start">Risk path</text>
<text x="749" y="276" font-family="Inter,Arial,sans-serif" font-size="12" font-weight="400" fill="#607184" text-anchor="start">OCO stop / target</text>
<text x="749" y="295" font-family="Inter,Arial,sans-serif" font-size="12" font-weight="400" fill="#607184" text-anchor="start">checked on valid quotes</text>
<rect x="1010" y="110" width="230" height="92" rx="4" fill="#f7f9fb" stroke="#d7e0e8" stroke-width="1"/>
<line x1="1011" y1="113" x2="1239" y2="113" stroke="#087e78" stroke-width="3"/>
<text x="1024" y="139" font-family="Inter,Arial,sans-serif" font-size="16" font-weight="700" fill="#172536" text-anchor="start">Strategy output</text>
<text x="1024" y="161" font-family="Inter,Arial,sans-serif" font-size="12" font-weight="400" fill="#607184" text-anchor="start">emit / suppress entry</text>
<rect x="1010" y="225" width="230" height="92" rx="4" fill="#f7f9fb" stroke="#d7e0e8" stroke-width="1"/>
<line x1="1011" y1="228" x2="1239" y2="228" stroke="#c45b25" stroke-width="3"/>
<text x="1024" y="254" font-family="Inter,Arial,sans-serif" font-size="16" font-weight="700" fill="#172536" text-anchor="start">Protective action</text>
<text x="1024" y="276" font-family="Inter,Arial,sans-serif" font-size="12" font-weight="400" fill="#607184" text-anchor="start">one-shot stop or target</text>
<line x1="210" y1="171" x2="245" y2="171" stroke="#8291a2" stroke-width="1" marker-end="url(#arrow)"/>
<line x1="450" y1="171" x2="485" y2="171" stroke="#8291a2" stroke-width="1" marker-end="url(#arrow)"/>
<line x1="675" y1="171" x2="705" y2="171" stroke="#d7e0e8" stroke-width="1"/>
<line x1="705" y1="156" x2="705" y2="271" stroke="#d7e0e8" stroke-width="1"/>
<line x1="705" y1="156" x2="735" y2="156" stroke="#8291a2" stroke-width="1" marker-end="url(#arrow)"/>
<line x1="705" y1="271" x2="735" y2="271" stroke="#8291a2" stroke-width="1" marker-end="url(#arrow)"/>
<line x1="950" y1="156" x2="1010" y2="156" stroke="#8291a2" stroke-width="1" marker-end="url(#arrow)"/>
<line x1="950" y1="271" x2="1010" y2="271" stroke="#8291a2" stroke-width="1" marker-end="url(#arrow)"/>
<line x1="40" y1="344" x2="1240" y2="344" stroke="#d7e0e8" stroke-width="1"/>
<text x="40" y="365" font-family="Inter,Arial,sans-serif" font-size="11" font-weight="700" fill="#607184" text-anchor="start">SEPARATELY MEASURED SUBSYSTEMS</text>
<text x="40" y="394" font-family="Inter,Arial,sans-serif" font-size="13" font-weight="700" fill="#172536" text-anchor="start">SHARED-MEMORY SPSC</text>
<text x="40" y="416" font-family="Inter,Arial,sans-serif" font-size="11" font-weight="400" fill="#607184" text-anchor="start">lock-free atomics verified on host</text>
<text x="445" y="394" font-family="Inter,Arial,sans-serif" font-size="13" font-weight="700" fill="#172536" text-anchor="start">ZEROMQ</text>
<text x="445" y="416" font-family="Inter,Arial,sans-serif" font-size="11" font-weight="400" fill="#607184" text-anchor="start">IPC/TCP transport · not lock-free</text>
<text x="850" y="394" font-family="Inter,Arial,sans-serif" font-size="13" font-weight="700" fill="#172536" text-anchor="start">DUCKDB WRITER</text>
<text x="850" y="416" font-family="Inter,Arial,sans-serif" font-size="11" font-weight="400" fill="#607184" text-anchor="start">async batches · complete read-back check</text>
</svg>''',
    "performance-comparison.svg": r'''<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="750" viewBox="0 0 1280 750"><defs><marker id="arrow" markerWidth="7" markerHeight="7" refX="5" refY="3.5" orient="auto"><path d="M0,0 L6,3.5 L0,7 Z" fill="#8291a2"/></marker></defs>
<rect x="0" y="0" width="1280" height="750" rx="0" fill="#ffffff" stroke="#ffffff" stroke-width="0"/>
<rect x="0" y="0" width="1280" height="1" rx="0" fill="#ffffff" stroke="#ffffff" stroke-width="0"/>
<text x="40" y="30" font-family="Inter,Arial,sans-serif" font-size="11" font-weight="700" fill="#275dad" text-anchor="start">SENTINEL STATARB / 02 · HPC RUN #9</text>
<text x="40" y="62" font-family="Inter,Arial,sans-serif" font-size="27" font-weight="700" fill="#172536" text-anchor="start">Benchmark snapshot</text>
<text x="40" y="86" font-family="Inter,Arial,sans-serif" font-size="13" font-weight="400" fill="#607184" text-anchor="start">14 Oct 2026 · source bd7f72c · synthetic workloads · CPU/IPC/storage (A100 unused)</text>
<line x1="40" y1="101" x2="1240" y2="101" stroke="#d7e0e8" stroke-width="1"/>
<rect x="32" y="119" width="600" height="218" rx="5" fill="#ffffff" stroke="#d7e0e8" stroke-width="1"/>
<text x="54" y="149" font-family="Inter,Arial,sans-serif" font-size="12" font-weight="700" fill="#607184" text-anchor="start">NATIVE C++17 / EVENT THROUGHPUT</text>
<text x="54" y="184" font-family="Inter,Arial,sans-serif" font-size="13" font-weight="600" fill="#172536" text-anchor="start">1M ticks</text>
<rect x="170" y="165" width="295" height="20" rx="2" fill="#f7f9fb" stroke="#f7f9fb" stroke-width="0"/>
<rect x="170" y="165" width="279" height="20" rx="2" fill="#275dad" stroke="#275dad" stroke-width="0"/>
<text x="477" y="181" font-family="Inter,Arial,sans-serif" font-size="14" font-weight="700" fill="#172536" text-anchor="start">42.62M/s</text>
<text x="54" y="224" font-family="Inter,Arial,sans-serif" font-size="13" font-weight="600" fill="#172536" text-anchor="start">10M ticks</text>
<rect x="170" y="205" width="295" height="20" rx="2" fill="#f7f9fb" stroke="#f7f9fb" stroke-width="0"/>
<rect x="170" y="205" width="253" height="20" rx="2" fill="#275dad" stroke="#275dad" stroke-width="0"/>
<text x="477" y="221" font-family="Inter,Arial,sans-serif" font-size="14" font-weight="700" fill="#172536" text-anchor="start">38.68M/s</text>
<line x1="54" y1="244" x2="610" y2="244" stroke="#d7e0e8" stroke-width="1"/>
<text x="54" y="270" font-family="Inter,Arial,sans-serif" font-size="12" font-weight="400" fill="#607184" text-anchor="start">Sampled hot-path p99</text>
<text x="234" y="270" font-family="Inter,Arial,sans-serif" font-size="14" font-weight="700" fill="#172536" text-anchor="start">0.051 μs</text>
<text x="350" y="270" font-family="Inter,Arial,sans-serif" font-size="12" font-weight="400" fill="#607184" text-anchor="start">Invalid ticks</text>
<text x="449" y="270" font-family="Inter,Arial,sans-serif" font-size="14" font-weight="700" fill="#087e78" text-anchor="start">0</text>
<text x="54" y="304" font-family="Inter,Arial,sans-serif" font-size="11" font-weight="400" fill="#607184" text-anchor="start">10M run: 9.99M measured after 10K warm-up</text>
<rect x="650" y="119" width="598" height="218" rx="5" fill="#ffffff" stroke="#d7e0e8" stroke-width="1"/>
<text x="672" y="149" font-family="Inter,Arial,sans-serif" font-size="11" font-weight="700" fill="#607184" text-anchor="start">PAIRED 1M-TICK PIPELINE · 5 MEASURED RUNS / IMPLEMENTATION</text>
<text x="672" y="184" font-family="Inter,Arial,sans-serif" font-size="13" font-weight="600" fill="#172536" text-anchor="start">C++ SPSC</text>
<rect x="810" y="165" width="178" height="20" rx="2" fill="#f7f9fb" stroke="#f7f9fb" stroke-width="0"/>
<rect x="810" y="165" width="159" height="20" rx="2" fill="#275dad" stroke="#275dad" stroke-width="0"/>
<text x="998" y="181" font-family="Inter,Arial,sans-serif" font-size="13" font-weight="700" fill="#172536" text-anchor="start">44.57M/s</text>
<text x="672" y="224" font-family="Inter,Arial,sans-serif" font-size="13" font-weight="600" fill="#172536" text-anchor="start">CPython queue</text>
<rect x="810" y="205" width="178" height="20" rx="2" fill="#f7f9fb" stroke="#f7f9fb" stroke-width="0"/>
<rect x="810" y="205" width="4" height="20" rx="2" fill="#087e78" stroke="#087e78" stroke-width="0"/>
<text x="998" y="221" font-family="Inter,Arial,sans-serif" font-size="13" font-weight="700" fill="#172536" text-anchor="start">264.57K/s</text>
<text x="1130" y="215" font-family="Inter,Arial,sans-serif" font-size="20" font-weight="700" fill="#087e78" text-anchor="start">168.46×</text>
<line x1="672" y1="244" x2="1226" y2="244" stroke="#d7e0e8" stroke-width="1"/>
<text x="672" y="270" font-family="Inter,Arial,sans-serif" font-size="12" font-weight="400" fill="#607184" text-anchor="start">Exact semantic parity</text>
<text x="833" y="270" font-family="Inter,Arial,sans-serif" font-size="13" font-weight="700" fill="#087e78" text-anchor="start">PASS</text>
<text x="672" y="304" font-family="Inter,Arial,sans-serif" font-size="11" font-weight="400" fill="#607184" text-anchor="start">Whole-pipeline ratio; not isolated GIL overhead</text>
<rect x="32" y="354" width="600" height="303" rx="5" fill="#ffffff" stroke="#d7e0e8" stroke-width="1"/>
<text x="54" y="384" font-family="Inter,Arial,sans-serif" font-size="12" font-weight="700" fill="#607184" text-anchor="start">INTERPROCESS LATENCY · μs</text>
<circle cx="400" cy="380" r="4" fill="#275dad"/>
<text x="410" y="384" font-family="Inter,Arial,sans-serif" font-size="11" font-weight="400" fill="#607184" text-anchor="start">p50</text>
<line x1="458" y1="374" x2="458" y2="386" stroke="#c45b25" stroke-width="2"/>
<text x="468" y="384" font-family="Inter,Arial,sans-serif" font-size="11" font-weight="400" fill="#607184" text-anchor="start">p99</text>
<line x1="198" y1="411" x2="198" y2="558" stroke="#d7e0e8" stroke-width="1"/>
<text x="198" y="579" font-family="Inter,Arial,sans-serif" font-size="10" font-weight="400" fill="#607184" text-anchor="middle">0</text>
<line x1="272" y1="411" x2="272" y2="558" stroke="#d7e0e8" stroke-width="1"/>
<text x="272" y="579" font-family="Inter,Arial,sans-serif" font-size="10" font-weight="400" fill="#607184" text-anchor="middle">20</text>
<line x1="346" y1="411" x2="346" y2="558" stroke="#d7e0e8" stroke-width="1"/>
<text x="346" y="579" font-family="Inter,Arial,sans-serif" font-size="10" font-weight="400" fill="#607184" text-anchor="middle">40</text>
<line x1="420" y1="411" x2="420" y2="558" stroke="#d7e0e8" stroke-width="1"/>
<text x="420" y="579" font-family="Inter,Arial,sans-serif" font-size="10" font-weight="400" fill="#607184" text-anchor="middle">60</text>
<text x="54" y="445" font-family="Inter,Arial,sans-serif" font-size="11" font-weight="600" fill="#172536" text-anchor="start">Shared-memory SPSC · one-way</text>
<line x1="198" y1="441" x2="457" y2="441" stroke="#f7f9fb" stroke-width="3"/>
<line x1="211.1202" y1="441" x2="221.8724" y2="441" stroke="#087e78" stroke-width="3"/>
<circle cx="211.1202" cy="441" r="4" fill="#087e78"/>
<line x1="221.8724" y1="434" x2="221.8724" y2="448" stroke="#c45b25" stroke-width="2"/>
<text x="465" y="445" font-family="Inter,Arial,sans-serif" font-size="11" font-weight="700" fill="#172536" text-anchor="start">3.546 / 6.452</text>
<text x="54" y="490" font-family="Inter,Arial,sans-serif" font-size="11" font-weight="600" fill="#172536" text-anchor="start">ZeroMQ C++ · one-way</text>
<line x1="198" y1="486" x2="457" y2="486" stroke="#f7f9fb" stroke-width="3"/>
<line x1="295.1213" y1="486" x2="320.1444" y2="486" stroke="#275dad" stroke-width="3"/>
<circle cx="295.1213" cy="486" r="4" fill="#275dad"/>
<line x1="320.1444" y1="479" x2="320.1444" y2="493" stroke="#c45b25" stroke-width="2"/>
<text x="465" y="490" font-family="Inter,Arial,sans-serif" font-size="11" font-weight="700" fill="#172536" text-anchor="start">26.249 / 33.012</text>
<text x="54" y="535" font-family="Inter,Arial,sans-serif" font-size="11" font-weight="600" fill="#172536" text-anchor="start">ZeroMQ C++ · request/reply</text>
<line x1="198" y1="531" x2="457" y2="531" stroke="#f7f9fb" stroke-width="3"/>
<line x1="391.2473" y1="531" x2="427.7626" y2="531" stroke="#c45b25" stroke-width="3"/>
<circle cx="391.2473" cy="531" r="4" fill="#c45b25"/>
<line x1="427.7626" y1="524" x2="427.7626" y2="538" stroke="#c45b25" stroke-width="2"/>
<text x="465" y="535" font-family="Inter,Arial,sans-serif" font-size="11" font-weight="700" fill="#172536" text-anchor="start">52.229 / 62.098</text>
<text x="54" y="618" font-family="Inter,Arial,sans-serif" font-size="10" font-weight="400" fill="#607184" text-anchor="start">p50 / p99 · percentiles are observations, not latency bounds</text>
<rect x="650" y="354" width="598" height="303" rx="5" fill="#ffffff" stroke="#d7e0e8" stroke-width="1"/>
<text x="672" y="384" font-family="Inter,Arial,sans-serif" font-size="12" font-weight="700" fill="#607184" text-anchor="start">DUCKDB · FULL WRITE + READ-BACK</text>
<text x="672" y="430" font-family="Inter,Arial,sans-serif" font-size="30" font-weight="700" fill="#172536" text-anchor="start">10.10M</text>
<text x="672" y="452" font-family="Inter,Arial,sans-serif" font-size="12" font-weight="400" fill="#607184" text-anchor="start">rows verified</text>
<text x="855" y="430" font-family="Inter,Arial,sans-serif" font-size="25" font-weight="700" fill="#275dad" text-anchor="start">241.7K/s</text>
<text x="855" y="452" font-family="Inter,Arial,sans-serif" font-size="12" font-weight="400" fill="#607184" text-anchor="start">measured throughput</text>
<text x="1074" y="430" font-family="Inter,Arial,sans-serif" font-size="22" font-weight="700" fill="#172536" text-anchor="start">41.787 s</text>
<text x="1074" y="452" font-family="Inter,Arial,sans-serif" font-size="12" font-weight="400" fill="#607184" text-anchor="start">elapsed</text>
<line x1="672" y1="472" x2="1226" y2="472" stroke="#d7e0e8" stroke-width="1"/>
<text x="672" y="500" font-family="Inter,Arial,sans-serif" font-size="12" font-weight="400" fill="#607184" text-anchor="start">Requested / written / read back</text>
<text x="995" y="500" font-family="Inter,Arial,sans-serif" font-size="12" font-weight="700" fill="#172536" text-anchor="start">10.1M / 10.1M / 10.1M</text>
<text x="672" y="532" font-family="Inter,Arial,sans-serif" font-size="12" font-weight="400" fill="#607184" text-anchor="start">Unique sequence IDs</text>
<text x="995" y="532" font-family="Inter,Arial,sans-serif" font-size="12" font-weight="700" fill="#172536" text-anchor="start">10,100,000</text>
<text x="672" y="564" font-family="Inter,Arial,sans-serif" font-size="12" font-weight="400" fill="#607184" text-anchor="start">Invalid bid/ask rows</text>
<text x="995" y="564" font-family="Inter,Arial,sans-serif" font-size="12" font-weight="700" fill="#087e78" text-anchor="start">0</text>
<text x="672" y="596" font-family="Inter,Arial,sans-serif" font-size="12" font-weight="400" fill="#607184" text-anchor="start">Database size</text>
<text x="995" y="596" font-family="Inter,Arial,sans-serif" font-size="12" font-weight="700" fill="#172536" text-anchor="start">136,065,024 bytes</text>
<line x1="40" y1="688" x2="1240" y2="688" stroke="#d7e0e8" stroke-width="1"/>
<text x="40" y="713" font-family="Inter,Arial,sans-serif" font-size="11" font-weight="400" fill="#607184" text-anchor="start">Host: 2× AMD EPYC 7742 · Ubuntu 22.04.4 · GCC 11.4 · CPU workload</text>
<text x="40" y="733" font-family="Inter,Arial,sans-serif" font-size="10" font-weight="400" fill="#607184" text-anchor="start">Native p99 is sampled hot-path time, not end-to-end order latency; one-way IPC and RTT are different measurements.</text>
</svg>''',
    "flash-crash-analysis.svg": r'''<svg xmlns="http://www.w3.org/2000/svg" width="1280" height="560" viewBox="0 0 1280 560"><defs><marker id="arrow" markerWidth="7" markerHeight="7" refX="5" refY="3.5" orient="auto"><path d="M0,0 L6,3.5 L0,7 Z" fill="#8291a2"/></marker></defs>
<rect x="0" y="0" width="1280" height="560" rx="0" fill="#ffffff" stroke="#ffffff" stroke-width="0"/>
<rect x="0" y="0" width="1280" height="1" rx="0" fill="#ffffff" stroke="#ffffff" stroke-width="0"/>
<text x="40" y="30" font-family="Inter,Arial,sans-serif" font-size="11" font-weight="700" fill="#275dad" text-anchor="start">SENTINEL STATARB / 03 · SEEDED REPLAY</text>
<text x="40" y="62" font-family="Inter,Arial,sans-serif" font-size="27" font-weight="700" fill="#172536" text-anchor="start">Crash gating &amp; stop-limit boundary</text>
<text x="40" y="86" font-family="Inter,Arial,sans-serif" font-size="13" font-weight="400" fill="#607184" text-anchor="start">100,000 base ticks + 1,030 duplicates · 180 bps gap at sequence 55,000 (55% of stream)</text>
<line x1="40" y1="101" x2="1240" y2="101" stroke="#d7e0e8" stroke-width="1"/>
<rect x="32" y="119" width="600" height="235" rx="5" fill="#ffffff" stroke="#d7e0e8" stroke-width="1"/>
<text x="54" y="148" font-family="Inter,Arial,sans-serif" font-size="12" font-weight="700" fill="#607184" text-anchor="start">WHOLE STREAM · ACCEPTED ENTRY SIGNALS</text>
<text x="54" y="173" font-family="Inter,Arial,sans-serif" font-size="12" font-weight="600" fill="#172536" text-anchor="start">Baseline: no debounce = 99,427</text>
<text x="54" y="209" font-family="Inter,Arial,sans-serif" font-size="12" font-weight="600" fill="#172536" text-anchor="start">No debounce</text>
<rect x="224" y="193" width="270" height="16" rx="2" fill="#f7f9fb" stroke="#f7f9fb" stroke-width="0"/>
<rect x="224" y="193" width="268.4529" height="16" rx="2" fill="#8a98a8" stroke="#8a98a8" stroke-width="0"/>
<text x="510" y="209" font-family="Inter,Arial,sans-serif" font-size="12" font-weight="700" fill="#172536" text-anchor="start">99,427</text>
<text x="54" y="248" font-family="Inter,Arial,sans-serif" font-size="12" font-weight="600" fill="#172536" text-anchor="start">Fixed</text>
<rect x="224" y="232" width="270" height="16" rx="2" fill="#f7f9fb" stroke="#f7f9fb" stroke-width="0"/>
<rect x="224" y="232" width="26.8731" height="16" rx="2" fill="#275dad" stroke="#275dad" stroke-width="0"/>
<text x="510" y="248" font-family="Inter,Arial,sans-serif" font-size="12" font-weight="700" fill="#172536" text-anchor="start">9,953</text>
<text x="54" y="287" font-family="Inter,Arial,sans-serif" font-size="12" font-weight="600" fill="#172536" text-anchor="start">Dynamic</text>
<rect x="224" y="271" width="270" height="16" rx="2" fill="#f7f9fb" stroke="#f7f9fb" stroke-width="0"/>
<rect x="224" y="271" width="26.8218" height="16" rx="2" fill="#087e78" stroke="#087e78" stroke-width="0"/>
<text x="510" y="287" font-family="Inter,Arial,sans-serif" font-size="12" font-weight="700" fill="#172536" text-anchor="start">9,934</text>
<text x="54" y="329" font-family="Inter,Arial,sans-serif" font-size="10" font-weight="400" fill="#607184" text-anchor="start">Signal reduction vs baseline: fixed 89.9896% · dynamic 90.00875%</text>
<rect x="650" y="119" width="598" height="235" rx="5" fill="#ffffff" stroke="#d7e0e8" stroke-width="1"/>
<text x="672" y="148" font-family="Inter,Arial,sans-serif" font-size="12" font-weight="700" fill="#607184" text-anchor="start">FIRST 200 SEQUENCE SLOTS AFTER GAP</text>
<text x="672" y="173" font-family="Inter,Arial,sans-serif" font-size="12" font-weight="600" fill="#172536" text-anchor="start">199 quotes passed quality checks</text>
<text x="672" y="209" font-family="Inter,Arial,sans-serif" font-size="12" font-weight="600" fill="#172536" text-anchor="start">No debounce</text>
<rect x="830" y="193" width="205" height="16" rx="2" fill="#f7f9fb" stroke="#f7f9fb" stroke-width="0"/>
<rect x="830" y="193" width="205" height="16" rx="2" fill="#8a98a8" stroke="#8a98a8" stroke-width="0"/>
<text x="1055" y="209" font-family="Inter,Arial,sans-serif" font-size="12" font-weight="700" fill="#172536" text-anchor="start">199 / 199</text>
<text x="672" y="248" font-family="Inter,Arial,sans-serif" font-size="12" font-weight="600" fill="#172536" text-anchor="start">Fixed</text>
<rect x="830" y="232" width="205" height="16" rx="2" fill="#f7f9fb" stroke="#f7f9fb" stroke-width="0"/>
<rect x="830" y="232" width="20.603015075376884" height="16" rx="2" fill="#275dad" stroke="#275dad" stroke-width="0"/>
<text x="1055" y="248" font-family="Inter,Arial,sans-serif" font-size="12" font-weight="700" fill="#172536" text-anchor="start">20 / 199</text>
<text x="672" y="287" font-family="Inter,Arial,sans-serif" font-size="12" font-weight="600" fill="#172536" text-anchor="start">Dynamic</text>
<rect x="830" y="271" width="205" height="16" rx="2" fill="#f7f9fb" stroke="#f7f9fb" stroke-width="0"/>
<text x="1055" y="287" font-family="Inter,Arial,sans-serif" font-size="12" font-weight="700" fill="#172536" text-anchor="start">0 / 199</text>
<text x="672" y="329" font-family="Inter,Arial,sans-serif" font-size="10" font-weight="700" fill="#087e78" text-anchor="start">Dynamic gating admitted 0 of 199 valid local-window entry opportunities.</text>
<rect x="32" y="371" width="1216" height="139" rx="5" fill="#f7f9fb" stroke="#d7e0e8" stroke-width="1"/>
<text x="54" y="399" font-family="Inter,Arial,sans-serif" font-size="12" font-weight="700" fill="#607184" text-anchor="start">OCO GAP-THROUGH CHECK</text>
<text x="54" y="430" font-family="Inter,Arial,sans-serif" font-size="14" font-weight="700" fill="#172536" text-anchor="start">STOP 25 bps</text>
<text x="54" y="456" font-family="Inter,Arial,sans-serif" font-size="12" font-weight="600" fill="#607184" text-anchor="start">LIMIT OFFSET 5 bps</text>
<line x1="260" y1="414" x2="260" y2="484" stroke="#d7e0e8" stroke-width="1"/>
<text x="286" y="430" font-family="Inter,Arial,sans-serif" font-size="11" font-weight="600" fill="#607184" text-anchor="start">Gap sweep (bps)</text>
<text x="286" y="454" font-family="Inter,Arial,sans-serif" font-size="13" font-weight="700" fill="#172536" text-anchor="start">0 · 1 · 2 · 5 · 7.5 · 10 · 25 · 50</text>
<text x="286" y="480" font-family="Inter,Arial,sans-serif" font-size="11" font-weight="700" fill="#275dad" text-anchor="start">Marketable: 0–5 bps  |  Not marketable: ≥7.5 bps</text>
<line x1="835" y1="414" x2="835" y2="484" stroke="#d7e0e8" stroke-width="1"/>
<text x="860" y="430" font-family="Inter,Arial,sans-serif" font-size="12" font-weight="700" fill="#172536" text-anchor="start">1 protective stop triggered / policy</text>
<text x="860" y="456" font-family="Inter,Arial,sans-serif" font-size="11" font-weight="700" fill="#c45b25" text-anchor="start">At the 180 bps gap: limit was not marketable</text>
<line x1="40" y1="528" x2="1240" y2="528" stroke="#d7e0e8" stroke-width="1"/>
<text x="40" y="549" font-family="Inter,Arial,sans-serif" font-size="11" font-weight="400" fill="#607184" text-anchor="start">Synthetic entry gating ≠ reduced realized loss. Marketability ≠ fill or execution confirmation.</text>
</svg>''',
}

for filename, markup in FIGURES.items():
    (OUT / filename).write_text(markup, encoding="utf-8")

print(f"Generated {len(FIGURES)} compact SVG figures in {OUT}")
