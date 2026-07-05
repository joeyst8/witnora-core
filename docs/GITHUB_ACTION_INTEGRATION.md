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

Marketplace packaging note: GitHub Marketplace listing expects a public action
repository with `action.yml` or `action.yaml` at the repository root. The
`marketplace-action/` directory in this repository is a ready-to-copy scaffold
for that dedicated public action repository.

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

- `largest`: select the largest externally verified row by deterministic row
  sort. The primary metric is recorded proof size in bytes when available,
  followed by variable count, clause count, numeric instance suffix, `c` value,
  and cap profile as stable tie-breakers.
- `first`: select the first externally verified row in deterministic sorted order
- `all`: select all externally verified rows for syntax/log/checker replay.
  Optional drat-trim replay remains bounded by `max-replay-proofs`.
- `instance`: select the row named by `select-instance`, for example `tseitin_20:c=2`

When only a subset of externally verified proof evidence is selected, reports
include `PROOF_SELECTION_LIMITED`. If partial mode selects no proof evidence,
reports include `PROOF_SELECTION_NONE`.

Selected evidence is not all evidence unless `select: all` is used. Partial
replay never implies full benchmark replay.

## Risk Flag Table

| Risk flag | Meaning | Typical cause | Recommended action |
| --- | --- | --- | --- |
| `METADATA_ONLY` | Metadata checks only were performed. | `depth: metadata`. | Use `depth: partial` for selected evidence replay. |
| `DRAT_TRIM_NOT_RERUN` | drat-trim was not rerun. | Partial replay without `rerun-drat-trim`. | Enable drat-trim replay if needed. |
| `INDEPENDENT_CHECKER_NOT_RERUN` | Independent checker did not rerun. | Metadata mode or missing selected evidence. | Use partial mode with valid evidence. |
| `CLAIM_SCAN_HEURISTIC_ONLY` | Claim scan is heuristic text scanning. | Always present. | Keep human review. |
| `PROOF_SELECTION_LIMITED` | Only selected proofs were replayed. | `select: largest`, `first`, or bounded replay. | Use `select: all` if appropriate. |
| `PROOF_SELECTION_NONE` | No proof evidence was selected. | Bad `select-instance` or missing artifact rows. | Check selection inputs. |
| `PROOF_FILE_MISSING` | A selected verified row lacks `proof.drat`. | Incomplete diagnostic artifact. | Rebuild or reattach the diagnostic artifact. |
| `DRAT_TRIM_TIMEOUT` | Optional drat-trim replay timed out. | Tight timeout or expensive proof. | Increase timeout or inspect proof. |
| `ACTION_INPUT_MISMATCH` | Action input artifact names do not match manifest expectations. | Wrong file name/path. | Use manifest-listed assets. |
| `CHECKER_VERSION_NOT_RECORDED` | Checker version could not be recorded. | Checker has no version metadata. | Record checker build details separately. |
| `UNVERIFIED_CLAIM` | Claim boundary or manifest evidence gap. | Missing manifest entry or flagged text. | Fix manifest or claim text. |
| `HASH_MISMATCH` | Actual asset hash differs from manifest. | Wrong or modified asset. | Use the correct release asset. |
| `MISSING_FILE` | Required asset is absent. | Missing artifact path. | Attach or download the missing file. |
| `REPORT_ARTIFACT_NOT_UPLOADED` | Report upload failed when requested. | Workflow upload issue. | Inspect Actions logs. |
| `GITHUB_CLI_NOT_AVAILABLE` | Release upload helper could not find `gh`. | `gh` not installed. | Install `gh` or use dry-run output manually. |
| `RELEASE_TAG_NOT_FOUND` | Upload mode requested but the GitHub Release tag was not found. | Release was not created or tag name is wrong. | Create the release first or check the tag name before uploading trust-card assets. |

## Fail-On Policy Examples

Strict artifact integrity:

```yaml
fail-on-risk-flags: HASH_MISMATCH,MISSING_FILE,ACTION_INPUT_MISMATCH,UNVERIFIED_CLAIM
```

Require partial replay:

```yaml
fail-on-verdict: NOT_VERIFIED,PARTIALLY_VERIFIED
```

Require drat-trim rerun:

```yaml
fail-on-risk-flags: DRAT_TRIM_NOT_RERUN,DRAT_TRIM_TIMEOUT
```

Require no limited proof selection:

```yaml
fail-on-risk-flags: PROOF_SELECTION_LIMITED,PROOF_SELECTION_NONE
```

Metadata depth does not fail merely because `DRAT_TRIM_NOT_RERUN` is present.
Partial depth without `rerun-drat-trim` also does not fail merely because
`DRAT_TRIM_NOT_RERUN` is present.

## Troubleshooting

- `ACTION_INPUT_MISMATCH`: the asset filename/path is not listed in the
  manifest. Use the manifest-listed file names.
- `PROOF_FILE_MISSING`: the selected externally verified row references a
  proof path that is absent from the diagnostic artifact. Rebuild or reattach
  the artifact.
- `PROOF_SELECTION_NONE`: the selection policy found no externally verified
  rows. Check `select-instance` format, for example `tseitin_20:c=2`.
- `DRAT_TRIM_TIMEOUT`: increase `replay-timeout-seconds`, replay fewer proofs,
  or inspect the proof manually.
- `CHECKER_VERSION_NOT_RECORDED`: the checker ran but its version could not be
  recorded. Keep external build notes with the release.

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

## Release Trust-Card Automation

The dry-run helper prepares upload plans without requiring network access or a
GitHub token:

```powershell
python scripts/attach_release_trust_card.py `
  --tag v1.0-public-preprint-final `
  --trust-card witnora-verify-out/trust_card.md `
  --report witnora-verify-out/release_verification_report.json `
  --manifest RELEASE_ASSETS_MANIFEST_v1.0-public-preprint.md `
  --out-dir release-trust-plan
```

Optional upload mode uses `gh release upload <tag> <files>...` if the GitHub CLI
is available. If `gh` is unavailable, the helper reports
`GITHUB_CLI_NOT_AVAILABLE` rather than pretending upload succeeded.
If `gh release view <tag>` cannot find the target release, the helper reports
`RELEASE_TAG_NOT_FOUND` and does not attempt upload.

## Limitations

This action is not a complete security audit, not a full scientific replay, and
not a SAT solver benchmark. It is a CI integration for scoped verification
reports and trust cards.
