# R-049: native cost-sensitive threshold training and inference

**Full CI green:** https://github.com/joeyst8/witnora-core/actions/runs/41839685826

## Migration

The experimental `witnora_core/cost_sensitive_gate.py` now has a native implementation in `rust/witnora-ve/src/cost_sensitive_gate.rs`. It fits only the original five preregistered decision thresholds `(2,3,5,8,1000000)` using the original cost-weighted structural utility and applies a **frozen** learned threshold at inference time. It reuses the previously verified R-043 adaptive and bounded greedy elimination and R-044 cheap feature counts. Python defaults remain unchanged; Rust access is opt-in through the `_rust` adapters.

## Verification

`tests/test_cost_sensitive_gate_rust.py` compares **500** randomized training datasets and **960** randomized source-CNF inference cases against the Python outputs, including threshold selection, training utility, selected-case count, chosen formula, routing, and expansion metadata. Every chosen CNF was independently checked by exhaustive truth tables to preserve SAT/UNSAT. Invalid thresholds, empty training and negative cost weights were tested. Full Rust compiler/unit, Python and Ganak CI passed.

## Trust and scope

Threshold training is a conventional finite decision-stump heuristic. It does **not** imply improved solver runtime, predictive mathematical invariants, novelty or Lean-certified proof. Original Python and Lean acceptance paths remain intact.

Migration inventory: **37** parallel-reference Python modules, **523** not migrated, **0** removed.
