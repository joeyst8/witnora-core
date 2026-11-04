# R-042: native bounded two-ply Davis-Putnam lookahead

**Verified green:** https://github.com/joeyst8/witnora-core/actions/runs/41772953474

## Migration

The previously unported experimental source
`witnora_core/lookahead_pivot_prototype.py` now has an independent
Rust implementation in `rust/witnora-ve/src/two_ply_lookahead.rs`.

The Rust code implements complete bounded Davis-Putnam pivot elimination,
canonical tautology removal, growth-budget and pair-budget filters, Python's
two-step ranking, beam truncation, and deterministic score/tie rules. It
exposes PyO3 `elimination_options_native` and `two_ply_pivot_native`.

The original Python entry points are **unchanged**. Only the new explicit
`elimination_options_rust` and `two_ply_pivot_rust` wrappers use the native
implementation.

## Independent verification

`tests/test_two_ply_rust.py` compares **1,200** deterministic randomized
source CNFs (1–8 variables) at randomized pair, growth, and beam budgets,
checking the complete pivot-option lists and final chosen formula exactly
against the original Python functions.

Each intermediate and final candidate is additionally checked with
independent exhaustive truth assignments to preserve SAT/UNSAT against
the original. Negative controls cover conflicting units, tautological
resolvents, empty source/contradiction, and invalid budgets. Rust unit
tests and the full Rust/Python/Ganak CI gate passed.

## Scope and trust

This implements a standard resolution-elimination heuristic. Eliminating
a variable existentially preserves **satisfiability**, not its original
model count or assignment space. Neither faster solving, a new algorithm,
nor Lean verification follows from these tests. No trusted Lean proof gate
or production default changed.

Inventory after R-042: **30** parallel-reference original Python modules,
**530** not yet migrated, **0** removed.
