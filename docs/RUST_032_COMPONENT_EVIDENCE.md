# R-032 — exact native component decomposition evidence

Status: **GREEN** in full
[GitHub Actions #41766349609](https://github.com/joeyst8/witnora-core/actions/runs/41766349609).

`rust/witnora-ve/src/component_proof.rs` now builds every
field of Python's `component_details` proof record from the original
canonical CNF: component count, incidence edges, stable component IDs,
SHA-256 formula digests, variable sets, canonical child clauses, and
original clause indices. The PyO3 entry point
`component_evidence_native` is opt-in via
`component_details(..., backend="rust_details")`.

## Controls

- 1,400 seeded random raw CNFs including tautologies, duplicate
  literals and empty clauses matched every Python component-evidence
  field.
- The unchanged Python `_verify_cd_step` independently accepted the
  native-generated evidence and child states.
- A real multi-component example matched Python exactly; corrupting
  the logged clause index was rejected by the original checker.
- The full Rust native, Ganak, proof and earlier certificate gates
  remained green in the same run.

## Limitations

This ports the **production of CD evidence**, not the complete
stateful component-routing verifier. The Python verifier and Lean
formal trust boundaries remain unchanged. No original Python source
was removed or claimed fully retired.
