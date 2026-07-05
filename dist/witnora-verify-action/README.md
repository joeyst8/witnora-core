# Witnora Verify Action

Witnora Verify is a scoped GitHub Action for release artifact integrity checks,
claim-boundary scanning, selected proof-evidence replay, and trust-card
generation.

Witnora Verify checks release artifact integrity and optionally replays selected
proof evidence. It does not rerun the solver, regenerate benchmark instances,
regenerate DRAT proofs, or replace human review.

## Quick Start

```yaml
- uses: joeyst8/witnora-verify-action@v1
  with:
    source-zip: witnora-core-v1.0-public-preprint.zip
    diagnostic-zip: witnora-core-v0.9.8-full-tseitin-minfill-diagnostic.zip
    manifest: RELEASE_ASSETS_MANIFEST_v1.0-public-preprint.md
    depth: partial
    select: largest
    fail-on-risk-flags: HASH_MISMATCH,MISSING_FILE,ACTION_INPUT_MISMATCH,UNVERIFIED_CLAIM
    fail-on-verdict: NOT_VERIFIED,PARTIALLY_VERIFIED,OVERCLAIM
```

## Install Witnora-Core

The action is a thin wrapper around `python -m witnora_core.ci`. For this MVP,
install Witnora-Core before invoking the action:

```yaml
- name: Install Witnora-Core
  run: python -m pip install git+https://github.com/joeyst8/witnora-core.git@v1.5.1-release-trust-polish
```

If `python -m witnora_core.ci` is unavailable, the action reports a setup error
equivalent to `WITNORA_CORE_NOT_INSTALLED`. This repository does not claim a PyPI package exists.

## Inputs

- `source-zip`: source archive path.
- `diagnostic-zip`: diagnostic artifact path.
- `manifest`: release asset manifest path.
- `depth`: `metadata` or `partial`, default `metadata`.
- `select`: `largest`, `first`, `all`, or `instance`.
- `select-instance`: selected row, for example `tseitin_20:c=2`.
- `rerun-drat-trim`: optional selected proof replay with drat-trim.
- `drat-trim`: path to drat-trim.
- `max-replay-proofs`: cap for optional drat-trim replay.
- `replay-timeout-seconds`: timeout for optional drat-trim replay.
- `fail-on-risk-flags`: comma-separated risk flags that fail the action.
- `fail-on-verdict`: comma-separated verdicts that fail the action.
- `out-dir`: output directory.
- `upload-artifacts`: upload report and trust card as workflow artifacts.

## Outputs

- `verdict`
- `certification_level`
- `verification_depth`
- `replay_depth`
- `risk_flags`
- `selected_evidence`
- `trust_card_path`
- `report_path`

## Depth Modes

- `metadata`: artifact hashes, file presence, manifest consistency, and
  claim-boundary scan.
- `partial`: selected proof syntax, existing drat-trim logs, selected
  independent checker replay, and optional selected drat-trim replay.
- `full`: not supported yet.

## Selection Policies

- `largest`: deterministic selection of the externally verified row with the
  largest recorded proof size, then variables, clauses, instance suffix, c
  value, and cap profile as tie-breakers.
- `first`: first externally verified row in deterministic sorted order.
- `all`: all externally verified rows for syntax/log/checker replay. Optional
  drat-trim replay remains bounded by `max-replay-proofs`.
- `instance`: selected by `select-instance`, for example `tseitin_20:c=2`.

Selected evidence is not all evidence unless `select: all` is used. Partial
replay never implies full benchmark replay.

## Risk Flags

| Risk flag | Meaning | Recommended action |
| --- | --- | --- |
| `METADATA_ONLY` | Metadata checks only were performed. | Use partial mode for selected replay. |
| `DRAT_TRIM_NOT_RERUN` | drat-trim was not rerun. | Enable selected drat-trim replay if required. |
| `INDEPENDENT_CHECKER_NOT_RERUN` | Independent checker did not rerun. | Use partial mode with valid evidence. |
| `CLAIM_SCAN_HEURISTIC_ONLY` | Claim scan is heuristic. | Keep human review. |
| `PROOF_SELECTION_LIMITED` | Only selected proofs were replayed. | Use `select: all` if appropriate. |
| `PROOF_SELECTION_NONE` | No proof evidence was selected. | Check selection inputs. |
| `PROOF_FILE_MISSING` | Selected proof file is absent. | Rebuild or reattach artifact. |
| `DRAT_TRIM_TIMEOUT` | Optional drat-trim replay timed out. | Increase timeout or replay fewer proofs. |
| `ACTION_INPUT_MISMATCH` | Input asset names do not match manifest. | Use manifest-listed assets. |
| `CHECKER_VERSION_NOT_RECORDED` | Checker version unavailable. | Record checker build details. |
| `UNVERIFIED_CLAIM` | Claim or manifest evidence gap. | Fix manifest or claim text. |
| `HASH_MISMATCH` | Asset hash differs from manifest. | Use the correct release asset. |
| `MISSING_FILE` | Required file is absent. | Attach or download the missing asset. |
| `GITHUB_CLI_NOT_AVAILABLE` | Release helper could not find gh. | Install gh or use dry-run output. |
| `RELEASE_TAG_NOT_FOUND` | Target release tag was not found. | Create release first or fix tag. |

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

Require full proof selection:

```yaml
fail-on-risk-flags: PROOF_SELECTION_LIMITED,PROOF_SELECTION_NONE
```

## Release Trust-Card Automation

Generate report and trust card with the action, then prepare upload plans with
the Witnora-Core helper:

```powershell
python scripts/attach_release_trust_card.py --release-tag v1 --trust-card trust_card.md --report release_verification_report.json --manifest RELEASE_ASSETS_MANIFEST.md --out-dir release-trust-plan
```

Upload mode is optional and uses `gh release view <tag>` before any upload. If
the release tag does not exist, it reports `RELEASE_TAG_NOT_FOUND` and does not
attempt upload. The helper does not use `--clobber` by default.

## What This Action Verifies

- artifact hashes
- required file presence
- manifest consistency
- claim-boundary scan
- selected proof syntax in partial mode
- existing drat-trim logs in partial mode
- selected independent checker replay in partial mode
- optional selected drat-trim replay

## What This Action Does Not Verify

- does not rerun the solver
- does not regenerate benchmark instances
- does not regenerate DRAT proofs
- does not rerun the full benchmark diagnostic
- does not prove claims outside selected evidence
- does not replace human review

## Example Workflows

See `examples/metadata.yml`, `examples/partial-replay.yml`,
`examples/partial-replay-drat.yml`, and `examples/release-trust-card.yml`.

## Security / Trust Model

This action reports scoped evidence checks. It can block workflows on configured
risk flags or verdicts. It is not a complete security audit, not a general proof
verifier, and not a competitive SAT solver.

## Limitations

No general SAT solving claim, no parity support claim, no broad XOR extraction
claim, no competitive SAT solver claim, no P vs NP claim, and no HARD or UNKNOWN
status claims are made by this action.

## Versioning

Use pinned tags such as `joeyst8/witnora-verify-action@v1`. The package is
prepared from Witnora-Core v1.6 marketplace distribution files.
