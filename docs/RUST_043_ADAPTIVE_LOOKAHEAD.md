# R-043: native adaptive bounded lookahead

**Full CI green:** https://github.com/joeyst8/witnora-core/actions/runs/41773562386

## Port

Ported `witnora_core/adaptive_lookahead_prototype.py` to `rust/witnora-ve/src/adaptive_lookahead.rs`, sharing exact Davis-Putnam elimination, strict greedy baseline, and deterministic Python-compatible ranking. The native PyO3 `adaptive_pivot_native` preserves all modes (`no_pivots`, `greedy_confident`, `adaptive_search`), candidate selection, search budget and depth, and numeric scores. The original default Python function is unchanged. The new `adaptive_pivot_rust` is opt-in.

## Verification

`tests/test_adaptive_lookahead_rust.py` compared **960** seeded random sources across variable counts 1–8, pair/growth/beam/expansion/depth/margin budgets, every resulting formula and complete metadata dictionary. Each transformed formula was independently checked with exhaustive assignment SAT/UNSAT evaluation. Contradictions, empty CNFs, and nine invalid-budget classes were checked. Rust unit tests and full Rust/Python/Ganak gate passed.

## Trust and limitations

These transformations are exact **equisatisfiable** variable eliminations but not generally model-count preserving. The search score is heuristic and does not predict general SAT runtime; no novelty or polynomial-time claim. The separate Lean proof verification remains the only trusted formal gate. No original Python code was deleted.

Migration inventory: **31** parallel-reference original Python modules, **529** not migrated, **0** removed.
