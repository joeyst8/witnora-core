# Witnora-Core v0.9.8 Reproducibility Package

This package documents the artifacts for the paper draft:
`Certified Collapse of Tseitin Formulas via XOR Detection and Sparse Elimination`.

## Frozen Source

- source archive: `witnora-core-v0.9.8.zip`
- source SHA256: `26557CD73DC45DF60EF5E056699AFC34E3402645DE60EFE050C5CE2ADADC267F`
- tag: `v0.9.8`
- commit: `27e1876b5d815e3f3ba21392395b0e0e9dbcd025`

## Diagnostic Artifact

- artifact: `witnora-core-v0.9.8-full-tseitin-minfill-diagnostic.zip`
- artifact SHA256: `4702299E28CDB4E3B16B0CD1CBFE9BA96018E625C0E8864A1C0476C2AEC3FA2C`

## External Tools Used

- CNFgen: `CNFgen (0.9.5)`
- CNFgen path used:
  `C:\Users\maham\AppData\Local\hermes\hermes-agent\venv\Scripts\cnfgen.exe`
- drat-trim path used:
  `C:\Users\maham\AppData\Local\Temp\witnora-drat-trim-real\drat-trim\drat-trim.exe`

`drat-trim` is used only as an external proof checker, not as a SAT solver.

## Run Tests

From a clean extraction of `witnora-core-v0.9.8.zip`:

```powershell
$env:WITNORA_DRAT_TRIM='C:\Users\maham\AppData\Local\Temp\witnora-drat-trim-real\drat-trim\drat-trim.exe'
python -m unittest discover -s tests -v
```

Expected result:

- 188 tests passing
- real drat-trim tests run and pass
- min-fill determinism and trace replay tests pass
- public category tests pass
- v0.9.8 diagnostic tests pass

## Rerun v0.9.8 Diagnostic

```powershell
$env:WITNORA_DRAT_TRIM='C:\Users\maham\AppData\Local\Temp\witnora-drat-trim-real\drat-trim\drat-trim.exe'
python -m witnora_core.xor_drat_diagnostic --matrix-preset full-tseitin-v098 --detect-xor-max-k 6 --xor-drat --elim-orders sparse-min-fill --profiles default medium-v098 --drat-trim 'C:\Users\maham\AppData\Local\Temp\witnora-drat-trim-real\drat-trim\drat-trim.exe' --cnfgen-path 'C:\Users\maham\AppData\Local\hermes\hermes-agent\venv\Scripts\cnfgen.exe' --out-root outputs\v0.9.8-full-tseitin-minfill-diagnostic --zip witnora-core-v0.9.8-full-tseitin-minfill-diagnostic.zip
```

## Expected Best-Matrix Public Category Counts

- `UNSAT_DRAT_EXPORTED_VERIFIED`: 7
- `UNSAT_XOR_NATIVE_ONLY`: 0
- `NO_COLLAPSE_FOUND`: 0
- `TIMEOUT`: 0
- `ERROR`: 0

## Artifact Locations

Inside `outputs/v0.9.8-full-tseitin-minfill-diagnostic/`:

- `per_instance_results.csv`: per-row result table.
- `best_matrix_public_category_summary.json`: best unique matrix category counts.
- `drat_verification_summary.json`: externally verified rows and proof paths.
- `FULL_TSEITIN_MINFILL_DIAGNOSTIC_REPORT.md`: human-readable report.
- `certs/`: certificate bundles.
- `certs/**/proof.drat`: DRAT proofs for verified rows.
- `drat_logs/`: drat-trim stdout/stderr excerpts.
- `independent_checks/`: independent checker outputs.

## Notes

The diagnostic artifact is separate from the source archive. The source archive
does not include `outputs/` or generated benchmark roots.
