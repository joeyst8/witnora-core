# Artifact Manifest

## Source Archive

- name: `witnora-core-v0.9.8.zip`
- SHA256: `26557CD73DC45DF60EF5E056699AFC34E3402645DE60EFE050C5CE2ADADC267F`
- tag: `v0.9.8`
- commit: `27e1876b5d815e3f3ba21392395b0e0e9dbcd025`

## Benchmark Artifact

- name: `witnora-core-v0.9.8-full-tseitin-minfill-diagnostic.zip`
- SHA256: `4702299E28CDB4E3B16B0CD1CBFE9BA96018E625C0E8864A1C0476C2AEC3FA2C`
- artifact root: `outputs/v0.9.8-full-tseitin-minfill-diagnostic/`

## Required External Tools

- Python 3
- official CNFgen `0.9.5`
- real `drat-trim`

Paths used in the recorded run:

- CNFgen:
  `C:\Users\maham\AppData\Local\hermes\hermes-agent\venv\Scripts\cnfgen.exe`
- drat-trim:
  `C:\Users\maham\AppData\Local\Temp\witnora-drat-trim-real\drat-trim\drat-trim.exe`
- drat-trim executable SHA256:
  `74D6D8FA2330C8D633B4E380CFFAD22517546C94963D4D2C381FEDF16641E1A8`

The recorded local `drat-trim` binary responds to `drat-trim -h` with the usage
banner but does not print a version string. Reproduction should therefore record
the binary path and SHA256 hash, or replace it with a clearly identified
`drat-trim` build and rerun the diagnostic.

Availability and identity check:

```powershell
& 'C:\Users\maham\AppData\Local\Temp\witnora-drat-trim-real\drat-trim\drat-trim.exe' -h
Get-FileHash -Algorithm SHA256 'C:\Users\maham\AppData\Local\Temp\witnora-drat-trim-real\drat-trim\drat-trim.exe'
```

Environment variable used for tests and diagnostics:

```powershell
$env:WITNORA_DRAT_TRIM='C:\Users\maham\AppData\Local\Temp\witnora-drat-trim-real\drat-trim\drat-trim.exe'
```

Test command:

```powershell
python -m unittest discover -s tests -v
```

Diagnostic rerun command:

```powershell
python -m witnora_core.xor_drat_diagnostic --matrix-preset full-tseitin-v098 --detect-xor-max-k 6 --xor-drat --elim-orders sparse-min-fill --profiles default medium-v098 --drat-trim 'C:\Users\maham\AppData\Local\Temp\witnora-drat-trim-real\drat-trim\drat-trim.exe' --cnfgen-path 'C:\Users\maham\AppData\Local\hermes\hermes-agent\venv\Scripts\cnfgen.exe' --out-root outputs\v0.9.8-full-tseitin-minfill-diagnostic --zip witnora-core-v0.9.8-full-tseitin-minfill-diagnostic.zip
```

## Expected Test Count

- `188` tests passing from clean extraction

## Expected Benchmark Summary

Best unique matrix rows:

- `UNSAT_DRAT_EXPORTED_VERIFIED`: 7
- `UNSAT_XOR_NATIVE_ONLY`: 0
- `NO_COLLAPSE_FOUND`: 0
- `TIMEOUT`: 0
- `ERROR`: 0

All cap-profile attempts:

- `UNSAT_DRAT_EXPORTED_VERIFIED`: 13
- `UNSAT_XOR_NATIVE_ONLY`: 1
- `false_drat_claims`: 0

The one native-only cap-profile attempt is `tseitin_20 c=2` under the default
row-width cap 8. The medium profile raises the row cap to 10 and verifies the
same instance against `original.dimacs`.
