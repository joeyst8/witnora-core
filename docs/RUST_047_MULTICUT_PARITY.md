# R-047: native bounded parity incidence multi-cut search

**Full CI green:** https://github.com/joeyst8/witnora-core/actions/runs/41837865088

## Migration

Ported `witnora_core/multicut_parity_separator.py` into `rust/witnora-ve/src/multicut_parity_separator.rs`. It uses the R-045 source-exact parity supports and component computation, identifies the highest-occurrence shared variables, tests lexicographically ordered 1..3-variable cuts under exact `max_shared` and `max_trials` limits, rejects cuts that leave empty-support groups, and preserves nonredundant candidate ordering.

The PyO3 function `bounded_parity_separators_native` is accessed through the new opt-in `bounded_parity_separators_rust` adapter; the Python default remains untouched.

## Independent validation

The `tests/test_multicut_parity_rust.py` gate compared **960** seeded random source formulas on all candidate cuts and metadata, plus **120** deliberately constructed minimal single-, double-, and triple-variable cuts. Exact trial count, exhaustion flag, invalid budget validation and full source formula hash were checked. Rust unit tests and the complete Python/Ganak CI passed.

## Trust limitations

The result describes parity-equation incidence. Full-CNF separation was **not verified**, no CNF rewrite or solver decision was made, and no Lean proof was produced. Its result explicitly retains `full_cnf_separation_verified=False`, `lean_verified=False`, `novelty_verified=False`, and `promoted=False`.

Migration inventory: **35** parallel Rust counterparts, **525** original Python files not migrated, **0** removed.
