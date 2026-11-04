# R-034: native CD child-state replay

**Verified green:** https://github.com/joeyst8/witnora-core/actions/runs/41767676653

## Scope

This milestone extends the independent Rust component-evidence verifier.
`component_proof::verify_evidence_and_children` returns canonical
component child states **only after** the entire logged CD record passes
the source-hash, component count, incidence edge, and full per-component
content checks. An invalid record returns a reason and **no children**.

The `verify_cd_children_native` PyO3 export and opt-in
`witnora_core.verifier_rust.verify_cd_step_in_rust` adapter produce the
same `(verified, child_formula_map, error)` shape as the original
Python `_verify_cd_step`.

## Independent regression evidence

`tests/test_component_children_rust.py` compares Rust versus Python
on **1,440** deterministic random CNFs, both complete authentic
component children and tampered count/edge/clause-index/output-hash
proofs. It also tests the real multi-component DIMACS fixture.
Rust unit tests verify canonicalized child contents. Full CI, including
prior Rust/Python/Ganak and R-033 adversarial checks, passed.

## Exclusions

No arbitrary certificate DAG component routing, complete SAT/UNSAT
certification, or original Python deletion. The Python verifier and Lean
trust boundary stay unchanged. The migration manifest still has 24
parallel-reference and 536 not-migrated original Python files.
