# Verifiable Intelligence Vision

Disclaimer: This is a forward-looking vision document. It does not describe current production capabilities. Current Witnora-Core capabilities are limited to the scoped claims in the public release and verification reports.

Witnora is moving from a single research artifact toward verifier-to-witness
infrastructure.

The core primitive is:

```text
claim -> evidence -> independent verification -> scoped trust
```

The first battlefield is SAT because SAT has unusually sharp notions of
witnesses, certificates, proof artifacts, independent checkers, and external
proof validation. That makes it a good place to build the habits needed for a
larger verification product: state the claim, collect the evidence, run the
checker, separate what is verified from what is not, and make the result legible
to a human.

## What Witnora Verifies Today

Witnora-Core currently verifies scoped SAT and UNSAT claims produced by its own
collapse-path framework. Its release verifier currently performs artifact
integrity checks, required-file/hash checks, and claim-boundary text scanning
for release packages. v1.2 adds partial replay for selected evidence already
inside a diagnostic artifact: proof syntax checks, recorded drat-trim log
checks, selected independent checker reruns, and optional selected drat-trim
reruns when a checker path is provided. Scientific proof reruns for every proof,
complete security audits, and general AI-agent verification are future
directions unless explicitly reported by a deeper verification run.

v1.3 packages those verifier capabilities as a GitHub Action / CI integration.
It can generate verification reports and trust cards during release workflows and
fail CI on selected evidence problems. It does not add solver logic, proof-export
logic, XOR-solving logic, or new benchmark claims.

v1.4 turns that local action into a marketplace-ready integration surface:
explicit fail-on-risk-flags and fail-on-verdict controls, selected-instance
replay, timeout risk flags, clearer CI summaries, and optional report/trust-card
artifact upload. These are workflow controls around the verifier, not broader
scientific proof claims.

v1.5 adds a dedicated Marketplace action package scaffold and dry-run release
trust-card automation. This helps outside repositories adopt the verifier and
attach scoped trust evidence to releases. It does not add SAT solving
capability, new proof export, new XOR reasoning, or new benchmark claims.

## Verification Depths

Witnora uses explicit depth labels:

1. `metadata_hash_checks_only`: checks release hashes, required files, manifest
   consistency, and claim-boundary text scanning.
2. `partial_replay`: verifies selected evidence already present in the artifact.
   It does not rerun the solver, regenerate CNFgen instances, or rerun the full
   benchmark diagnostic. When only selected proof evidence is replayed, Witnora
   records `PROOF_SELECTION_LIMITED`.
3. `full_replay`: future work. In v1.2, a full replay request returns
   `NOT_VERIFIED` with `FULL_REPLAY_NOT_IMPLEMENTED`.

The v1.1 verification kernel does not add solving power. It adds a reusable
audit layer that asks:

- What is being claimed?
- What files support the claim?
- Which checker evaluated the evidence?
- What is the certification level?
- What claims are explicitly not made?
- Is the artifact reproducible enough for an outside reviewer?

## Future Domains

Future domains may include software verification, AI-agent plan checking,
scheduling, hardware verification, and scientific constraints. These are future
directions, not current claims.

The product direction is not merely "solve more SAT instances." The broader
direction is to make technical claims checkable, bounded, and understandable.

## Claim Boundary

The verification kernel does not claim broad AI truth evaluation. It checks
structured evidence against explicit rules. It refuses to promote native-only or
unverified evidence into externally verified claims.

This discipline is the product: useful trust is scoped trust.
