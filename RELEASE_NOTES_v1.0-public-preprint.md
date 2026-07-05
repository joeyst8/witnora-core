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
- Compiled paper PDF release asset:
  `paper/witnora_tseitin_certified_collapse.pdf`
- Reproducibility package:
  `reproducibility/README.md`
  `reproducibility/ARTIFACT_MANIFEST.md`
  `reproducibility/CLAIM_BOUNDARY.md`
- Submission checklist:
  `SUBMISSION_CHECKLIST.md`

## Frozen Inputs

- Public source archive: `witnora-core-v1.0-public-preprint.zip`
- Public source archive SHA256:
  `D79E4FCD48A18C395584EF04199D7156C63503B66F20385451E4B3F31176EFB2`
- Public source tag: `v1.0-public-preprint`
- Public source tag commit: `106904a91693ae672712c4818ef10790ff919e15`
- Paper-revision source archive: `witnora-core-v0.9.9-paper-rev1.zip`
- Paper-revision source SHA256:
  `9217E14D16DCF87A8A9F14BEC7DE24C52EB3F6C2C7CF4DDF88415D73D0F3B49D`
- Paper-revision source tag: `v0.9.9-paper-rev1`
- Paper-revision source commit: `6039db406451f60143586060b5773db6bfa6d216`
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

The PDF was generated locally with Tectonic 0.16.9 after installing the
official Windows MSVC binary in the workspace.

- PDF: `paper/witnora_tseitin_certified_collapse.pdf`
- PDF SHA256:
  `A98910C817974D3D15F6847690CD197008362A06984FA38BE81194BE7D26DB9A`
- Tectonic binary archive SHA256:
  `131A24604785A9600989A3D91225F597DF52AC06F00AEFFE86FD529F99EE5CDD`

Compile command used:

```powershell
tools\tectonic\tectonic-0.16.9\tectonic.exe paper\witnora_tseitin_certified_collapse.tex --keep-logs --keep-intermediates -o paper
```

The LaTeX log has no overfull hbox warnings, undefined citations, or fatal
errors after the final formatting pass. A Windows fontconfig notice was emitted
by the PDF backend, but the PDF was produced and visually rendered for audit.
