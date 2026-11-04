# Witnora R-018/R-019: Native Deterministic Simplification

Research branch: `research/w-crc-001-asymmetric-v1`, draft PR #122.
Lean TC-063 PR #121 and main remain untouched.

## R-018 — verified blocked-clause elimination witnesses

The native Rust module `rust/witnora-ve/src/bce.rs` reproduces
deterministic first blocked-clause selection, pivot ordering,
all opposite-clause resolvents, and tautology checks.

The opt-in `backend="rust"` paths in
`blocked_clause_proof` and `find_first_blocked_clause`
return the same proof records. During the transition, Python
still performs the small SHA-256 digest/serialization step
on the Rust-produced resolvent witness. This ensures all
legacy proof hashes are unchanged without silently claiming
the hash implementation has migrated.

[Green R-018 CI #41751079781](https://github.com/joeyst8/witnora-core/actions/runs/41751079781)
passed native Rust unit tests and **1,000 seeded original-Python
comparisons**, including exact digest equality.

## R-019 — verified complete mathematical simplifier path

`rust/witnora-ve/src/simplifier.rs` implements exact deterministic
unit-propagation and pure-literal steps with all source clause
transformation data. The full Python
`simplify(formula, logger, backend="rust")` opt-in
route then uses native backends for:

1. unit propagation;
2. pure-literal elimination;
3. deterministic subsumption;
4. blocked-clause elimination;
5. graph component decomposition.

The existing Python `StepLogger` and immutable formula hashes are
retained for the transitional proof/certificate trust boundary.
[Green R-019 CI #41751421413](https://github.com/joeyst8/witnora-core/actions/runs/41751421413)
passed **1,000 seeded full-source differentials**: exact source
status, output CNF, unit and pure step decisions, and **every
logged certificate event** matched the unchanged all-Python route.
This does not port the underlying Python SHA-256 and logger
serialization; these remain transitional proof-boundary components.

## Limits and next work

This port is deterministic conventional CNF simplification, not
a new complexity theorem. It does not port SHA-256 proof digest
generation, `StepLogger` serialization, the full collapse
planner, general RAT/DRAT checking, Lean formal proof kernels,
or the 117 scripts/295 tests counted at the original audit.
No original Python file has been deleted.

The per-file checkpoint is
`research/python_to_rust_manifest.json`.
