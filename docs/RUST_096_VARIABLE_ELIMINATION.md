# R-096: exact bounded CRC variable elimination in Rust

Native Rust now carries the reference source-order factor-table construction,
deterministic min-resulting-scope elimination, exact arbitrary-precision model
counts, operation accounting, and fail-closed factor-width/work budgets.
Violation masks cross the Python boundary as decimal strings to avoid 64-bit
truncation. The Python function defaults to its original implementation; an
explicit `backend="rust"` selects the native implementation.

The differential gate checks 360 seeded signed CNF sources (including
unsorted component-variable order), all budget combinations, empty and
out-of-range masks, and high bit masks up to variable ID 256. The algorithm remains
exponential in intermediate factor width and makes no general #SAT
performance breakthrough claim.

Status: native library compilation, extension build and exact differential
tests passed in GitHub Actions #41931233354. The earlier run #41930825246
found an out-of-contract variable-ID-257 fixture, corrected to ID 256 before
the successful rerun.
