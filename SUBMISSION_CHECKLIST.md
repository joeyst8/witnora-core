# Witnora-Core v1.0-public-preprint Submission Checklist

## Paper Files

- [x] Markdown paper source exists:
  `paper/witnora_tseitin_certified_collapse.md`
- [x] LaTeX paper source exists:
  `paper/witnora_tseitin_certified_collapse.tex`
- [x] Bibliography exists:
  `paper/references.bib`
- [x] PDF generated from LaTeX source:
  `paper/witnora_tseitin_certified_collapse.pdf`
- [x] PDF rendered for visual audit with Poppler.

PDF generation was completed locally with Tectonic 0.16.9:

```powershell
tools\tectonic\tectonic-0.16.9\tectonic.exe paper\witnora_tseitin_certified_collapse.tex --keep-logs --keep-intermediates -o paper
```

The generated PDF SHA256 is:

`A98910C817974D3D15F6847690CD197008362A06984FA38BE81194BE7D26DB9A`

Alternative full LaTeX command sequence for TeX Live/MiKTeX environments:

```powershell
cd paper
pdflatex witnora_tseitin_certified_collapse.tex
bibtex witnora_tseitin_certified_collapse
pdflatex witnora_tseitin_certified_collapse.tex
pdflatex witnora_tseitin_certified_collapse.tex
```

## Required References

- [x] CNFgen
- [x] Tseitin formulas
- [x] DRAT and drat-trim
- [x] CDCL and proof logging
- [x] XOR reasoning in SAT solvers
- [x] Structural SAT / bounded-width reasoning

## Reproducibility Package

- [x] Source archive SHA recorded.
- [x] Diagnostic artifact SHA recorded.
- [x] drat-trim executable SHA recorded.
- [x] Test command recorded.
- [x] Diagnostic rerun command recorded.
- [x] Expected public category counts recorded.
- [x] Claim boundary recorded.

## Validation

- [x] Full unit test command identified.
- [x] Real drat-trim environment variable identified.
- [x] Forbidden-claim scan pattern identified.
- [x] Source archive excludes `outputs/`.
- [x] Diagnostic artifact remains separate from source archive.

## Claim Boundary

Allowed:

- Witnora-Core externally DRAT-verifies the recorded official CNFgen Tseitin
  rows, including `tseitin_20 c=2`, using exact CNF XOR extraction and
  deterministic sparse/min-fill XOR proof export against `original.dimacs`.
- The v0.8.4 baseline reported no collapse on the corresponding recorded
  Tseitin diagnostic rows.
- The v0.9.8 diagnostic records seven externally verified Tseitin rows.

Forbidden:

- parity support claim
- broad XOR extraction claim
- CryptoMiniSat-equivalent extraction claim
- competitive SAT solver claim
- industrial benchmark claim
- full DRAT/RAT/LRAT/FRAT claim
- general SAT solving claim
- P vs NP claim
- `HARD` or `UNKNOWN` statuses

## Final Outside Review Prompt

Before public posting, send the paper PDF and artifact manifest to an outside
reviewer with these questions:

1. Would you reject this short systems note on claim-boundary grounds?
2. Which related-work citation is still missing?
3. Is any table unclear or misleading?
4. Is the `tseitin_20 c=2` cap-profile explanation sufficient?
5. Does the artifact appendix contain enough information to reproduce the
   recorded diagnostic?
