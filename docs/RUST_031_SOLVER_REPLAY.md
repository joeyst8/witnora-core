# R-031 — native 2-SAT and treewidth certificate replay

Status: **GREEN**,
[GitHub Actions #41765848855](https://github.com/joeyst8/witnora-core/actions/runs/41765848855).

The native local certificate replay engine now accepts the additional
`2SAT_SOLVE` and `TREEWIDTH_SOLVE` steps in addition to R-030's
`UP`, `PLE`, `SUB`, `BCE`, and `VE`.

- The 2-SAT branch recomputes SCC satisfiability and its assignment
  from the current CNF in Rust and checks the logged decision,
  witness assignment, and unchanged formula hash.
- The treewidth branch independently reconstructs the primal graph,
  verifies the logged elimination order and achieved width cap, and
  checks logged source graph edges and unchanged formula hash.
- Unsupported component contexts remain rejected by the strict
  Rust adapter. Full status-level certificate claims still require
  existing independent proof checking.

## Differential and adversarial checks

- 1,200 random two-CNF cases using independently produced Python
  `solve_2sat` log evidence, including SAT and UNSAT cases. Altered
  status claims must fail with the expected error.
- 250 independent Python treewidth-search orders verified natively;
  truncated/invalid orders must be rejected.
- The previous 2,000 native deterministic local replays and tampering
  tests (R-030) plus all earlier proof, arithmetic and Ganak checks
  remained green in the same gate.

## Trust and limits

Component decomposition/ownership, global status validation,
complete `verify_collapse_path`, and external proof replay are still
separate work. The original Python verifier remains the independent
default and the Lean proof checker has not been modified. This is
not a claim to have replaced all 560 original Python files.
