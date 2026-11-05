# Partial Replay Verification Demo

This demo shows the v1.2 verification depth ladder. It does not introduce a new
benchmark claim and does not rerun the full solver or regenerate the diagnostic
artifact.

## Metadata Depth

```powershell
python -m witnora_core.verify release `
  --source-zip witnora-core-v1.0-public-preprint.zip `
  --diagnostic-zip witnora-core-v0.9.8-full-tseitin-minfill-diagnostic.zip `
  --manifest RELEASE_ASSETS_MANIFEST_v1.0-public-preprint.md `
  --depth metadata `
  --out-dir out_metadata
```

Expected depth:

```json
{
  "verification_depth": "metadata_hash_checks_only",
  "verdict": "ARTIFACT_INTEGRITY_VERIFIED"
}
```

## Partial Depth

```powershell
python -m witnora_core.verify release `
  --source-zip witnora-core-v1.0-public-preprint.zip `
  --diagnostic-zip witnora-core-v0.9.8-full-tseitin-minfill-diagnostic.zip `
  --manifest RELEASE_ASSETS_MANIFEST_v1.0-public-preprint.md `
  --depth partial `
  --select largest `
  --out-dir out_partial
```

Expected depth:

```json
{
  "verification_depth": "partial_replay",
  "selection_policy": "largest",
  "verdict": "PARTIAL_REPLAY_VERIFIED_WITH_SCOPE_LIMITS"
}
```

## Partial Depth With drat-trim Rerun

```powershell
python -m witnora_core.verify release `
  --source-zip witnora-core-v1.0-public-preprint.zip `
  --diagnostic-zip witnora-core-v0.9.8-full-tseitin-minfill-diagnostic.zip `
  --manifest RELEASE_ASSETS_MANIFEST_v1.0-public-preprint.md `
  --depth partial `
  --select largest `
  --rerun-drat-trim `
  --drat-trim C:\path\to\drat-trim.exe `
  --max-replay-proofs 1 `
  --out-dir out_partial_drat
```

This reruns drat-trim only on selected proof evidence. It still does not rerun
the solver or full benchmark diagnostic.
