# Witnora Verify GitHub Action

Witnora Verify is a scoped CI/CD verification action for release artifacts,
claim boundaries, selected proof evidence, and trust-card generation.

GitHub Marketplace listing requires a public repository with `action.yml` or
`action.yaml` at the repository root. This `marketplace-action/` directory is a
ready-to-copy scaffold for that dedicated action repository.

Warning: Witnora Verify does not rerun the solver, regenerate CNFgen instances,
regenerate DRAT proofs, or rerun the full benchmark diagnostic.

## Quick Start

```yaml
- uses: your-org/witnora-verify@v1
  with:
    source-zip: witnora-core-v1.0-public-preprint.zip
    diagnostic-zip: witnora-core-v0.9.8-full-tseitin-minfill-diagnostic.zip
    manifest: RELEASE_ASSETS_MANIFEST_v1.0-public-preprint.md
    depth: partial
    select: largest
    fail-on-risk-flags: HASH_MISMATCH,MISSING_FILE,ACTION_INPUT_MISMATCH,UNVERIFIED_CLAIM
    fail-on-verdict: NOT_VERIFIED,PARTIALLY_VERIFIED,OVERCLAIM
```

## What It Verifies

Metadata mode checks artifact hashes, file presence, manifest consistency, and
the heuristic claim-boundary scanner.

Partial mode checks selected proof evidence already present in the diagnostic
artifact: proof syntax, existing drat-trim logs, independent checker replay, and
optional drat-trim replay when a checker path is provided.

## What It Does Not Verify

- does not rerun the solver
- does not regenerate CNFgen instances
- does not rerun the full benchmark diagnostic
- does not regenerate DRAT proofs
- does not prove claims outside selected evidence
- does not replace human review

## Depth Modes

- `metadata`: fast artifact integrity and claim-boundary check
- `partial`: selected evidence replay from the artifact
- `full`: not supported yet

## Selection Policies

- `largest`: deterministic selection of the externally verified row with the
  largest proof size when recorded, then variables, clauses, instance number,
  `c` value, and cap profile as stable tie-breakers.
- `first`: first externally verified row in deterministic sorted order.
- `all`: all externally verified rows for syntax, log, and independent checker
  replay. Optional drat-trim replay remains bounded by `max-replay-proofs`.
- `instance`: selected by instance ID and c value, for example
  `tseitin_20:c=2`.

Selected evidence is not all evidence unless `select: all` is used. Partial
replay never implies full benchmark replay. `PROOF_SELECTION_LIMITED` appears
when selected proofs are fewer than externally verified proof rows.

## Fail-On Policies

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

## Outputs

- `verdict`
- `certification_level`
- `verification_depth`
- `replay_depth`
- `risk_flags`
- `selected_evidence`
- `trust_card_path`
- `report_path`

## Risk Flags

| Risk flag | Meaning | Typical cause | Recommended action |
| --- | --- | --- | --- |
| `METADATA_ONLY` | Metadata checks only were performed. | `depth: metadata`. | Use `depth: partial` for selected evidence replay. |
| `DRAT_TRIM_NOT_RERUN` | drat-trim was not rerun. | Partial replay without `rerun-drat-trim`. | Enable drat-trim replay if needed. |
| `INDEPENDENT_CHECKER_NOT_RERUN` | Independent checker did not rerun. | Metadata mode or missing selected evidence. | Use partial mode with valid evidence. |
| `CLAIM_SCAN_HEURISTIC_ONLY` | Claim scan is heuristic text scanning. | Always present. | Keep human review. |
| `PROOF_SELECTION_LIMITED` | Only selected proofs were replayed. | `select: largest`, `first`, or bounded replay. | Use `select: all` if appropriate. |
| `PROOF_SELECTION_NONE` | No proof evidence was selected. | Bad `select-instance` or missing artifact rows. | Check selection inputs. |
| `PROOF_FILE_MISSING` | A selected verified row lacks `proof.drat`. | Corrupt or incomplete artifact. | Rebuild or reattach the diagnostic artifact. |
| `DRAT_TRIM_TIMEOUT` | Optional drat-trim replay timed out. | Tight timeout or expensive proof. | Increase timeout or inspect proof. |
| `ACTION_INPUT_MISMATCH` | Action asset input did not match manifest expectations. | Wrong file name/path. | Use the manifest-listed assets. |
| `CHECKER_VERSION_NOT_RECORDED` | Checker version could not be recorded. | Checker has no version metadata. | Record checker build details separately. |
| `UNVERIFIED_CLAIM` | Claim boundary or manifest evidence gap. | Missing manifest entry or flagged text. | Fix manifest or claim text. |
| `HASH_MISMATCH` | Actual asset hash differs from manifest. | Wrong or modified asset. | Use the correct release asset. |
| `MISSING_FILE` | Required asset is absent. | Missing artifact path. | Attach or download the missing file. |
| `REPORT_ARTIFACT_NOT_UPLOADED` | Report upload failed when requested. | Workflow upload issue. | Inspect Actions logs. |
| `GITHUB_CLI_NOT_AVAILABLE` | Release upload helper could not find `gh`. | `gh` not installed. | Install `gh` or use dry-run output manually. |

## Troubleshooting

- If the action returns `ACTION_INPUT_MISMATCH`, verify the filenames are listed
  exactly in the release manifest.
- If `PROOF_FILE_MISSING` appears, the diagnostic artifact is incomplete for the
  selected externally verified row.
- If `DRAT_TRIM_TIMEOUT` appears, rerun with a larger `replay-timeout-seconds`
  value or replay fewer proofs.
- If `PROOF_SELECTION_NONE` appears, check `select-instance` formatting:
  `instance_id:c=value`, for example `tseitin_20:c=2`.

## Example Trust Card

```text
Verdict: PARTIAL_REPLAY_VERIFIED_WITH_SCOPE_LIMITS
Verification depth: partial_replay
Replay depth: independent_checker_replay
Risk flags: CLAIM_SCAN_HEURISTIC_ONLY, PROOF_SELECTION_LIMITED
Not claimed: parity support, competitive SAT solving, P vs NP progress
```
