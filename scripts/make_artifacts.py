#!/usr/bin/env python3
"""Generate the project's eight conventional, data-backed Matplotlib plots.

Kept as a compatibility entry point for the existing CI workflow.
"""
from make_plots import main

if __name__ == "__main__":
    raise SystemExit(main())
