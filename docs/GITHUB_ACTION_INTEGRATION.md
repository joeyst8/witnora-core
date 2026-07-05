# GitHub Action Integration

Witnora Verify can run in CI/CD as a scoped release-artifact verifier. It checks
release archive integrity, claim boundaries, selected proof evidence, and trust
card generation. It is not a solver extension and does not add new benchmark
claims.

## Action

Local action path:

```yaml
uses: ./.github/actions/witnora-verify
```

Action name: `Witnora Verify`

Purpose: verify release artifacts, claim boundaries, and selected proof evidence
using Witnora-Core.

## Inputs

- `source-zip`: required source archive path
- `diagnostic-zip`: required diagnostic artifact path
- `manifest`: required release asset manifest path
- `depth`: `metadata` or `partial`, default `metadata`
- `select`: partial replay selection policy, default `largest`
- `rerun-drat-trim`: optional `true` or `false`, default `false`
- `drat-trim`: optional path to `drat-trim`
- `max-replay-proofs`: optional replay cap, default `1`
- `fail-on`: comma-separated fail policy, default `hash_mismatch,overclaim,missing_file`
- `out-dir`: output directory, default `witnora-verify-out`

## Outputs

- `verdict`
- `certification_level`
- `verification_depth`
- `trust_card_path`
- `report_path`

## Example Workflow

```yaml
name: Witnora Verify Example

on:
  workflow_dispatch:

jobs:
  verify-release-artifacts:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: ./.github/actions/witnora-verify
        with:
          source-zip: witnora-core-v1.0-public-preprint-final.zip
          diagnostic-zip: witnora-core-v0.9.8-full-tseitin-minfill-diagnostic.zip
          manifest: RELEASE_ASSETS_MANIFEST_v1.0-public-preprint.md
          depth: partial
          select: largest
          rerun-drat-trim: "false"
          fail-on: hash_mismatch,overclaim,missing_file,partial_or_not_verified
```

The repository also includes `.github/workflows/witnora-verify-example.yml` as a
copyable example. It assumes the release assets are available in the workflow
workspace.

## Fail-On Policy

The CI wrapper exits nonzero only for selected conditions:

- `hash_mismatch`: a listed artifact SHA256 does not match
- `missing_file`: a required artifact is missing
- `overclaim`: claim-boundary scan failed or a requested artifact is not listed
- `partial_or_not_verified`: report is not a scoped positive verdict, or the
  report carries an unverified-claim flag
- `drat_replay_failed`: requested drat-trim replay failed or skipped
- `independent_checker_failed`: selected independent checker replay failed or skipped

Metadata depth does not fail just because `DRAT_TRIM_NOT_RERUN` is present.
Partial depth without `rerun-drat-trim` also does not fail merely because
`DRAT_TRIM_NOT_RERUN` is present.

## Metadata vs Partial Depth

`metadata` mode checks release hashes, manifest consistency, required-file
presence, and claim-boundary text scanning. It emits
`ARTIFACT_INTEGRITY_VERIFIED` when those scoped checks pass.

`partial` mode adds selected proof-evidence replay checks from the diagnostic
artifact. It emits `PARTIAL_REPLAY_VERIFIED_WITH_SCOPE_LIMITS` only for the
selected evidence actually checked.

## What Partial Replay Does and Does Not Do

Partial replay:

- re-checks selected proof evidence already present in the artifact
- validates proof syntax and existing drat-trim logs
- reruns independent checker on selected evidence
- optionally reruns drat-trim on selected `proof.drat` files

Partial replay does not:

- rerun the solver
- regenerate CNFgen instances
- rerun the full benchmark diagnostic
- regenerate DRAT proofs
- prove claims outside the selected evidence

When only a subset of proofs is replayed, reports include
`PROOF_SELECTION_LIMITED`.

## Providing drat-trim

To rerun selected DRAT proofs, provide both:

```yaml
rerun-drat-trim: "true"
drat-trim: /path/to/drat-trim
```

If `drat-trim` is not provided, partial replay still checks proof syntax,
recorded logs, and selected independent checker outputs, but it keeps the
`DRAT_TRIM_NOT_RERUN` risk flag.

## Limitations

This action is not a complete security audit, not a full scientific replay, and
not a SAT solver benchmark. It is a CI integration for scoped verification
reports and trust cards.
