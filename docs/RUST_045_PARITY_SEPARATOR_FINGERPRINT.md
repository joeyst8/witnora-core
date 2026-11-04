# R-045: native source-exact parity separator fingerprint

**Full CI green:** https://github.com/joeyst8/witnora-core/actions/runs/41774804239

## Migration

Ported the observational `witnora_core/parity_separator_fingerprint.py` to the independent `rust/witnora-ve/src/parity_separator_fingerprint.rs`. It scans the canonical source CNF for **complete** parity clause groups of arity 2–6, computes exact equation-support connectivity and cut-variable candidates, and reproduces the candidate index groups and source SHA-256. The new `parity_separator_fingerprint_rust` Python wrapper is opt-in; the original Python call remains default.

## Verification

The new `tests/test_parity_separator_fingerprint_rust.py` checks **1,050** seeded random CNFs and **100** planted two-spoke parity hubs against the original Python dictionary. More controls cover complete and incomplete six-variable parity groups, every `max_k` cutoff, empty CNF, invalid arities, and non-XOR clauses that cross the putative parity separator. The Rust compiler/unit tests and full Rust/Python/Ganak gate passed.

## Interpretation

This is **not** a separator of the entire CNF: non-XOR clauses may connect both sides. The `non_xor_cross_edges_audited` field remains false. No CNF was rewritten, no SAT/UNSAT was inferred, and no Lean proof or novelty claim was promoted. The result is a descriptive structural fingerprint only.

Inventory after R-045: **33** parallel-reference original Python modules, **527** not migrated, **0** removed.
