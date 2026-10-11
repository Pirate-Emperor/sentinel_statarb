# Contributing

Keep changes focused on the Sentinel StatArb simulation, tests, reports, and documentation.

Before submitting a change:

1. Run `python -m compileall -q sentinel_runtime scripts tests`.
2. Run `python -m unittest discover -s tests -v`.
3. Build and run the C++ tests with CMake and CTest.
4. Run `python scripts/validate_reports.py` after refreshing reports.
5. Describe which commands ran and whether any optional checks were skipped.

For performance changes, use a warm-up run before collecting measured timing. Record the machine-dependent nature of the result, and keep round-trip latency separate from per-event processing latency.
