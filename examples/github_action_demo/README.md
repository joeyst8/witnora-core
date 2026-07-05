# GitHub Action Demo

This demo shows the intended CI shape for Witnora Verify. The files are small
examples, not generated benchmark outputs.

## Sample Action Invocation

```yaml
- uses: ./.github/actions/witnora-verify
  with:
    source-zip: witnora-core-v1.0-public-preprint.zip
    diagnostic-zip: witnora-core-v0.9.8-full-tseitin-minfill-diagnostic.zip
    manifest: RELEASE_ASSETS_MANIFEST_v1.0-public-preprint.md
    depth: partial
    select: instance
    select-instance: tseitin_20:c=2
    fail-on-risk-flags: HASH_MISMATCH,MISSING_FILE,UNVERIFIED_CLAIM,DRAT_TRIM_TIMEOUT
    fail-on-verdict: NOT_VERIFIED,PARTIALLY_VERIFIED,OVERCLAIM
    upload-artifacts: "true"
```

## Expected Outputs

- `verdict`
- `certification_level`
- `verification_depth`
- `replay_depth`
- `risk_flags`
- `selected_evidence`
- `report_path`
- `trust_card_path`

## Expected Trust Card Summary

Partial replay produces a scoped trust card. If only one proof is replayed from
a larger verified set, the card includes `PROOF_SELECTION_LIMITED`.

## What It Does Not Do

Witnora Verify does not rerun the solver, regenerate CNFgen instances,
regenerate DRAT proofs, rerun the full benchmark diagnostic, or prove claims
outside selected evidence.
