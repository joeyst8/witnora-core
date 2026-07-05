# Product Wedge: Witnora Verify

Disclaimer: This is a forward-looking vision document. It does not describe current production capabilities. Current Witnora-Core capabilities are limited to the scoped claims in the public release and verification reports.

Witnora Verify is a verification layer for AI-generated technical claims and
proof artifacts.

## Target Users

- researchers who need artifact and claim-boundary audits
- engineering teams shipping proof-carrying tools
- security and verification teams evaluating generated technical evidence
- enterprise buyers who need concise trust summaries before adopting an artifact

## Why They Care

Technical systems increasingly produce answers, proofs, logs, plans, and
release bundles faster than humans can inspect them manually. The painful
question is not only "what did the system say?" but "what evidence makes this
safe to believe?"

Witnora Verify turns that into a structured report:

- claim being audited
- evidence files
- independent checks
- external checkers
- artifact hashes
- allowed claims
- forbidden claims
- scoped verdict

## What It Checks

The first implementation checks Witnora SAT certificates, release packages,
SHA256 evidence, claim boundaries, and trust-card summaries. The v1.1.1 release
verification path is an artifact-integrity and metadata check; it does not rerun
the full scientific proof pipeline unless a future report explicitly says a
deeper replay was performed.

v1.2 adds a partial replay mode for release artifacts. Partial replay verifies
selected evidence already present in the artifact, including proof-file syntax,
recorded drat-trim logs, selected independent checker replay, and optional
selected drat-trim replay when a checker path is provided. It does not rerun the
solver, regenerate public benchmark inputs, or rerun the full benchmark
diagnostic.

v1.3 adds GitHub Action / CI integration for the verification kernel. The action
generates release verification reports and trust cards, can fail a workflow on
selected conditions such as hash mismatch or overclaim detection, and records
`PROOF_SELECTION_LIMITED` when only a selected subset of proof evidence is
replayed. This is CI packaging for the existing verifier, not a new SAT
capability and not a new benchmark result.

v1.4 makes the Action easier to use outside this repository: marketplace-style
metadata, risk-flag and verdict fail policies, selected-instance controls,
drat-trim replay timeouts, clearer CI log summaries, and optional report/trust
card upload. It remains a scoped artifact verification integration, not a
complete security audit or production proof-verification product.

v1.5 prepares a dedicated Marketplace action scaffold and release trust-card
automation. The scaffold is intended for a future public action repository with
`action.yml` at the repository root. The release helper prepares upload plans
and release-note snippets for trust cards and verification reports; it does not
require a GitHub token in dry-run mode and does not create new scientific
claims.

v1.7 adds a Docker action package for the same verifier. The Docker runner is
self-contained in the sense that the image installs Python dependencies and
Witnora-Core from a tagged source ref, so external workflows do not need to
prepare Witnora-Core manually. This improves packaging reproducibility, but it
does not add solver capability, benchmark coverage, proof-export capability, or
new scientific claims.

The current depth ladder is:

- `metadata_hash_checks_only`: artifact integrity and claim-boundary scanning
- `partial_replay`: selected proof evidence replay/checks from the artifact
- `full_replay`: future work, explicitly unsupported in v1.2

The same shape can later support other technical outputs:

- generated code with tests and static-analysis evidence
- AI-agent plans with constraints and execution logs
- scientific or scheduling claims with reproducibility files
- hardware or protocol artifacts with checker outputs

## What It Refuses To Claim

Witnora Verify does not claim unsupported capability, broad benchmark success,
general intelligence, or domain authority. It reports what the evidence supports
and records risk flags when the evidence is incomplete.

## Infrastructure Path

The wedge is a small but durable API:

```text
submit claim + evidence -> receive verification report + trust card
```

That is the bridge from a research prototype to a product primitive.
