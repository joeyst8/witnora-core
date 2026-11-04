# R-029 — native SAT-assignment reconstruction

Status: **GREEN**, [GitHub Actions #41761548922](https://github.com/joeyst8/witnora-core/actions/runs/41761548922).

The Rust `rust/witnora-ve/src/reconstruction.rs` reconstructs full
SAT witnesses by reversing certificate steps. It handles unit and pure
literal assignments, blocked-clause reinsertion, proof-aware
variable-elimination reconstruction, ignored solver/subsumption/component
records, unsupported-step rejection, assignment conflicts, original
variable completion, and full source-formula satisfaction.

The `reconstruct_assignment_native` PyO3 entry point is available
through `reconstruct_assignment(..., backend="rust")`. The default
Python path and `ReconstructionResult` interface are unchanged.

## Differential controls

- 1,600 seeded randomized source CNFs with mixed reconstruction
  records, partial assignments, intentional contradictions and
  unsupported event kinds. Full `ok`, final assignment and error
  text match the original Python implementation.
- Real SAT, UNSAT and multi-component `.wcert` result paths have
  matching reconstruction results on both engines.
- Native Rust unit tests and all preceding independent arithmetic,
  witness, certificate and Ganak gates passed.

## Trust and limits

Reconstruction only addresses *SAT witnesses*. It is not a
complete logical certificate replay checker, not a DRAT/LRAT proof,
and does not replace Lean validation. Python remains the default
and independent reference; no original Python file has been deleted.
This is one core migration milestone within the 560-file inventory.
