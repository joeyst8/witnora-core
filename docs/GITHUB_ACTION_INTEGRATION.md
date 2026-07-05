# GitHub Action Integration

Witnora Verify can run in CI/CD as a scoped release-artifact verifier. It checks
release archive integrity, claim boundaries, selected proof evidence, and trust
card generation. It is not a solver extension and does not add new benchmark
claims.

## Quick Start Workflow

```yaml
name: Verify Release Evidence

on:
  workflow_dispatch:

jobs:
  verify:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: ./.github/actions/witnora-verify
        with:
          source-zip: witnora-core-v1.0-public-preprint.zip
          diagnostic-zip: witnora-core-v0.9.8-full-tseitin-minfill-diagnostic.zip
          manifest: RELEASE_ASSETS_MANIFEST_v1.0-public-preprint.md
          depth: partial
          select: largest
          fail-on-risk-flags: HASH_MISMATCH,MISSING_FILE,UNVERIFIED_CLAIM
          fail-on-verdict: NOT_VERIFIED,PARTIALLY_VERIFIED
          upload-artifacts: "true"
```

## Action Metadata

Local action path:

```yaml
uses: ./.github/actions/witnora-verify
```

Action name: `Witnora Verify`

Purpose: scoped artifact verification and partial replay trust cards for
technical releases.

## Inputs

Required:

- `source-zip`: source archive path
- `diagnostic-zip`: diagnostic artifact path
- `manifest`: release asset manifest path

Optional:

- `depth`: `metadata` or `partial`, default `metadata`
- `select`: `largest`, `first`, `all`, or `instance`, default `largest`
- `select-instance`: selected instance when `select: instance`, for example `tseitin_20:c=2`
- `rerun-drat-trim`: optional `true` or `false`, default `false`
- `drat-trim`: optional path to `drat-trim`
- `max-replay-proofs`: optional replay cap, default `1`
- `replay-timeout-seconds`: optional per-proof replay timeout, default `120`
- `fail-on-risk-flags`: comma-separated risk flags that fail the action
- `fail-on-verdict`: comma-separated verdicts that fail the action
- `fail-on`: backward-compatible shorthand policy
- `out-dir`: output directory, default `witnora-verify-out`
- `upload-artifacts`: upload report/trust card with `actions/upload-artifact`, default `false`

## Outputs

- `verdict`
- `certification_level`
- `verification_depth`
- `replay_depth`
- `risk_flags`
- `selected_evidence`
- `trust_card_path`
- `report_path`

## What This Action Verifies

Metadata mode verifies:

- artifact hashes
- file presence
- manifest consistency
- claim-boundary scan

Partial mode verifies selected evidence already present in the diagnostic
artifact:

- selected proof syntax
- existing drat-trim log status
- independent checker replay
- optional drat-trim replay

## What This Action Does Not Verify

Required scope boundary:

- does not rerun the solver
- does not regenerate CNFgen instances
- does not rerun the full benchmark diagnostic
- does not regenerate DRAT proofs
- does not prove claims outside selected evidence
- does not replace human review

## Choosing Depth

- `metadata`: fast artifact integrity and claim-boundary check
- `partial`: selected evidence replay from the diagnostic artifact
- `full`: not supported yet; full replay requests return `NOT_VERIFIED`

## Selection Policies

- `largest`: select the largest externally verified row by deterministic row sort
- `first`: select the first externally verified row
- `all`: select all externally verified rows for syntax/log/checker replay
- `instance`: select the row named by `select-instance`, for example `tseitin_20:c=2`

When only a subset of externally verified proof evidence is selected, reports
include `PROOF_SELECTION_LIMITED`. If partial mode selects no proof evidence,
reports include `PROOF_SELECTION_NONE`.

## Fail-On Policy Examples

Fail on missing file or hash mismatch:

```yaml
fail-on-risk-flags: HASH_MISMATCH,MISSING_FILE
```

Fail on any unverified claim:

```yaml
fail-on-risk-flags: UNVERIFIED_CLAIM,ACTION_INPUT_MISMATCH
```

Fail if drat-trim replay times out:

```yaml
fail-on-risk-flags: DRAT_TRIM_TIMEOUT
```

Fail unless the result is a scoped positive partial replay verdict:

```yaml
fail-on-verdict: NOT_VERIFIED,PARTIALLY_VERIFIED,OVERCLAIM
```

Metadata depth does not fail merely because `DRAT_TRIM_NOT_RERUN` is present.
Partial depth without `rerun-drat-trim` also does not fail merely because
`DRAT_TRIM_NOT_RERUN` is present.

## Enterprise CI Example

This release workflow assumes assets have already been downloaded or checked
into the workflow workspace:

```yaml
name: Release Evidence Gate

on:
  workflow_dispatch:

jobs:
  witnora-verify:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Verify release evidence
        uses: ./.github/actions/witnora-verify
        with:
          source-zip: dist/source.zip
          diagnostic-zip: dist/diagnostic.zip
          manifest: dist/RELEASE_ASSETS_MANIFEST.md
          depth: partial
          select: instance
          select-instance: tseitin_20:c=2
          rerun-drat-trim: "false"
          fail-on-risk-flags: HASH_MISMATCH,MISSING_FILE,UNVERIFIED_CLAIM,DRAT_TRIM_TIMEOUT
          fail-on-verdict: NOT_VERIFIED,PARTIALLY_VERIFIED,OVERCLAIM
          upload-artifacts: "true"
```

## Limitations

This action is not a complete security audit, not a full scientific replay, and
not a SAT solver benchmark. It is a CI integration for scoped verification
reports and trust cards.
