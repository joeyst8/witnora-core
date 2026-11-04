# R-048: graph-invariant elimination policies in native Rust

**Full CI green:** https://github.com/joeyst8/witnora-core/actions/runs/41838667472

## Port

Reproduced all of `witnora_core/structural_operator_invention.py` in `rust/witnora-ve/src/structural_operator_invention.rs`: primal degree, missing fill edges, exact complete binary-XOR degree, and the three experimental pivot policies (`min_fill`, `xor_boundary`, `max_release`). The native code reuses R-042's exact Davis-Putnam elimination and R-046's source-bound XOR detector, and preserves Python's priority/tie rules. The original Python defaults remain unchanged; Rust wrappers are opt-in.

## Verification

`tests/test_invariant_policies_rust.py` compared **1,200** seeded random source CNFs, all graph invariant dictionaries, and the exact final CNFs for each of three policies under randomized pair/growth budgets. Every candidate was independently checked by complete truth-table evaluation to preserve SAT/UNSAT. Named wrappers and invalid policy controls passed. The full Rust compiler, Python differential and Ganak CI gate passed.

## Interpretation

All three policies are scheduling heuristics over established exact resolution. They do not establish a runtime speedup, new inference rule, complexity theorem, or Lean proof. The separate Lean source certificate boundary remains unchanged.

Migration inventory: **36** parallel-reference original Python modules, **524** not migrated, **0** removed.
