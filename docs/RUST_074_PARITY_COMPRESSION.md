# R-074 — Restricted binary-XOR component compression (native CI pending)

The opt-in Rust backend now extracts complete source 2-XOR patterns,
constructs deterministic BFS root-offset components, reports the first
inconsistent edge, reconstructs assignments from root values and rewrites
source CNF clauses under the offsets. The default Python functions and
metadata are preserved; all results remain `NOT_LEAN_VERIFIED` until the
independent formal checks establish them.

The focused gate covers 300 seeded sources with full report, witness
reconstruction and residual-CNF equality; explicit empty and inconsistent
cycle controls; and Rust unit tests. Exact Python object/digest parity is
checked where applicable. This is an experimental transformation of the
detected XOR part, not a proof of general CNF equivalence.
