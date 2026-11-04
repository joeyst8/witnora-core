# R-030 — native replay of five deterministic certificate operators

Status: **GREEN**, [dedicated full Rust gate #41765312867](https://github.com/joeyst8/witnora-core/actions/runs/41765312867).

The new independent Rust engine in
`rust/witnora-ve/src/local_replay.rs` replays five supported
non-component proof steps directly from the source formula:
`UP`, `PLE`, `SUB`, `BCE`, `VE`.
It checks sequential step IDs and each input/output formula SHA-256
and independently recomputes each source transformation. It checks
the logged removed/added clauses, assigned literals, subsuming
clauses, BCE digest and pivot, and VE width cap.

The strict opt-in adapter
`witnora_core/verifier_rust.py:replay_local_certificate_in_rust`
returns a verified local formula state or a reproducible error.
It refuses component contexts and unsupported step types, rather
than treating missing proof support as successful verification.

## Differential tests

- 1,000 seeded valid individual operator-step replays against
  the original Python `_verify_up/_verify_ple/_verify_sub/_verify_bce/_verify_ve`.
- 1,000 deliberately altered output hashes required exactly matching
  rejection, including Python reference failure reason.
- Complete deterministic `simplify` step sequences, without
  component decomposition, were replayed natively and matched
  the original final CNF.
- All earlier native Rust, original Python and Ganak comparison
  steps passed the same full CI gate.

## Scope and limitations

This is **not** a complete `verify_collapse_path` replacement:
`CD`, `2SAT_SOLVE`, `TREEWIDTH_SOLVE`, component/local state
routing, overall SAT/UNSAT classification, and full certificate
bundle trust remain separate stages. The Python verifier remains
the independent default and Lean remains the formal checker.
No original Python source was deleted and PR #122 is still draft.
