# R-127: bounded native canonical XOR-to-CNF encoding

`canonical_xor_cnf_clauses(..., backend="rust")` now enumerates and sorts
the exact forbidden parity assignments inside Rust and returns the same
set of signed CNF clauses as Python. Duplicate XOR input variables cancel;
empty-variable parity 0 produces no clauses while parity 1 produces the
empty contradiction clause.

The native path fails closed when the canonical support exceeds 16
variables by default to avoid accidental exponential memory use. The
legacy unbounded Python reference remains unchanged. Focused native CI
compares widths 0–8 exhaustively across both parity RHSs and 240 seeded
supports, including nonconsecutive large variable IDs. No solver
complexity or source-equivalence claim follows from this encoding alone.
