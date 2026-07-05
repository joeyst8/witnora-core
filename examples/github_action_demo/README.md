# GitHub Action Demo

This demo shows the intended CI shape for Witnora Verify. It is deliberately
small: the files are static examples, not generated benchmark outputs.

## Commands

Metadata-only:

```powershell
python -m witnora_core.ci --source-zip witnora-core-v1.0-public-preprint-final.zip --diagnostic-zip witnora-core-v0.9.8-full-tseitin-minfill-diagnostic.zip --manifest RELEASE_ASSETS_MANIFEST_v1.0-public-preprint.md --depth metadata --out-dir witnora-verify-out
```

Partial replay:

```powershell
python -m witnora_core.ci --source-zip witnora-core-v1.0-public-preprint-final.zip --diagnostic-zip witnora-core-v0.9.8-full-tseitin-minfill-diagnostic.zip --manifest RELEASE_ASSETS_MANIFEST_v1.0-public-preprint.md --depth partial --select largest --out-dir witnora-verify-out
```

Partial replay with selected drat-trim rerun:

```powershell
python -m witnora_core.ci --source-zip witnora-core-v1.0-public-preprint-final.zip --diagnostic-zip witnora-core-v0.9.8-full-tseitin-minfill-diagnostic.zip --manifest RELEASE_ASSETS_MANIFEST_v1.0-public-preprint.md --depth partial --select largest --rerun-drat-trim --drat-trim C:\path\to\drat-trim.exe --max-replay-proofs 1 --out-dir witnora-verify-out
```

## Expected Behavior

- Metadata mode checks archive hashes and claim boundaries.
- Partial mode checks selected proof evidence already present in the artifact.
- If only one proof is replayed from a larger verified set, the report includes
  `PROOF_SELECTION_LIMITED`.
- Neither mode reruns the solver, regenerates benchmark inputs, or creates new
  SAT benchmark claims.
