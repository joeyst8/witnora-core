# R-033: independent native component-certificate checker

**Verified green:** https://github.com/joeyst8/witnora-core/actions/runs/41767084650

## Scope

The native Rust `component_proof::verify_evidence` independently recomputes
canonical CNF source hash, component count, incidence edges, complete component
records, hashes, and original clause indices. It returns the first mismatch
reason. The PyO3 function `verify_component_evidence_native` and opt-in
`witnora_core.components.verify_component_evidence_in_rust` adapter expose
the checker without changing Python's default verifier.

## Evidence

`tests/test_component_verify_rust.py` performs 1,200 deterministic random
CNF inputs, valid native-versus-Python comparisons, and adversarial tampering
of component count, incidence edges, component formula hash, component clause
indices and source output hash. Exact first-error parity is checked against
`witnora_core.verifier._verify_cd_step`. Rust unit tests cover accepted
and wrong-count evidence. The complete Rust/Python/Ganak gate passed.

## Trust boundary

This milestone is **parallel reference**, not a complete verifier replacement.
It checks well-formed component metadata but does not yet return verified child
states, validate the entire certificate DAG, or replace Python's authoritative
SAT/UNSAT outcome verifier. No Python modules were removed, and no Lean
proof definitions or trust assumptions were modified.
