# R-044: native selective adaptive/greedy pivot gate

**Full CI green:** https://github.com/joeyst8/witnora-core/actions/runs/41774007601

## Migration

The original `witnora_core/selective_lookahead_prototype.py` has an independent Rust counterpart in `rust/witnora-ve/src/selective_lookahead.rs`. It computes the exact cheap positive/negative occurrence counts, chooses the adaptive search only when structural/budget gates allow it, and otherwise runs two exact greedy Davis-Putnam elimination passes. Both PyO3 interfaces (`cheap_pivot_features_native`, `selective_pivot_native`) are opt-in; the Python default is unchanged.

## Verification

The native wrapper exactly matched original Python on **1,120** seeded randomized CNFs (1–8 variables), including all cheap feature counts, selection mode, expanded states, and resulting clauses. Every resulting candidate was independently checked by exhaustive assignments for SAT/UNSAT preservation. A deliberately eligible and ineligible formula confirms both routing paths; invalid gate inputs and the original's late nested expansion-budget validation are covered. Rust compiler/unit tests and full Python/Ganak CI passed.

## Limits

This remains a speculative scheduler using established exact variable elimination. No benchmarked solver speedup, new SAT inference theorem, or Lean certificate is asserted. Python and Lean source/trust boundaries are unchanged.

Inventory after R-044: **32** parallel-reference original Python modules, **528** not migrated, **0** originals removed.
