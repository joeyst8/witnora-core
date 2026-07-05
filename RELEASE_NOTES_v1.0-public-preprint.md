# Witnora-Core v1.0-public-preprint Release Notes

## Purpose

This package prepares the frozen Witnora-Core v0.9.9-paper-rev1 result for
public preprint review. It does not add solver logic, new benchmark families,
parity support, broader XOR extraction, or new proof claims.

## Included Public-Facing Materials

- LaTeX paper source:
  `paper/witnora_tseitin_certified_collapse.tex`
- Bibliography:
  `paper/references.bib`
- Markdown paper source:
  `paper/witnora_tseitin_certified_collapse.md`
- Reproducibility package:
  `reproducibility/README.md`
  `reproducibility/ARTIFACT_MANIFEST.md`
  `reproducibility/CLAIM_BOUNDARY.md`
- Submission checklist:
  `SUBMISSION_CHECKLIST.md`

## Frozen Inputs

- Source archive: `witnora-core-v0.9.9-paper-rev1.zip`
- Source SHA256:
  `9217E14D16DCF87A8A9F14BEC7DE24C52EB3F6C2C7CF4DDF88415D73D0F3B49D`
- Source tag: `v0.9.9-paper-rev1`
- Source commit: `6039db406451f60143586060b5773db6bfa6d216`
- Diagnostic artifact:
  `witnora-core-v0.9.8-full-tseitin-minfill-diagnostic.zip`
- Diagnostic artifact SHA256:
  `4702299E28CDB4E3B16B0CD1CBFE9BA96018E625C0E8864A1C0476C2AEC3FA2C`
- drat-trim executable SHA256:
  `74D6D8FA2330C8D633B4E380CFFAD22517546C94963D4D2C381FEDF16641E1A8`

## Main Allowed Claim

Witnora-Core externally DRAT-verifies the recorded official CNFgen Tseitin
rows, including `tseitin_20 c=2`, using exact CNF XOR extraction and
deterministic sparse/min-fill XOR proof export against `original.dimacs`.

## Claim Boundary

This release does not claim:

- parity support
- broad XOR extraction
- CryptoMiniSat-equivalent extraction
- competitive SAT solver performance
- industrial benchmark performance
- full DRAT/RAT/LRAT/FRAT support
- general SAT solving
- P vs NP progress

## Validation Command

```powershell
$env:WITNORA_DRAT_TRIM='C:\Users\maham\AppData\Local\Temp\witnora-drat-trim-real\drat-trim\drat-trim.exe'
python -m unittest discover -s tests -v
```

Expected result: 188 tests passing with real `drat-trim` tests running and
passing.

## PDF Status

The LaTeX source is included. A PDF should be generated with a local LaTeX
installation, for example:

```powershell
cd paper
pdflatex witnora_tseitin_certified_collapse.tex
bibtex witnora_tseitin_certified_collapse
pdflatex witnora_tseitin_certified_collapse.tex
pdflatex witnora_tseitin_certified_collapse.tex
```

In the Codex execution environment used for this package, `pdflatex`,
`bibtex`, `latexmk`, `xelatex`, `lualatex`, `tectonic`, and `pandoc` were not
available, so the PDF was not generated there.
