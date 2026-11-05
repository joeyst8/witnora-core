# Compile Witnora-Core v1.0 Public Preprint on Overleaf

This bundle is for compiling the Witnora-Core public preprint when local LaTeX
tooling is unavailable.

## Files in This Bundle

- `witnora_tseitin_certified_collapse.tex`
- `references.bib`
- `figures/`

## Overleaf Steps

1. Create a new blank Overleaf project.
2. Upload all files from this bundle.
3. Set the main file to:
   `witnora_tseitin_certified_collapse.tex`
4. Compile with pdfLaTeX.
5. Download the generated PDF.
6. Rename the downloaded PDF to:
   `witnora_tseitin_certified_collapse.pdf`

## Expected Output

- `witnora_tseitin_certified_collapse.pdf`

## Claim Boundary Check

Before public release, inspect the generated PDF and confirm it contains no
affirmative claim of:

- parity support
- broad XOR extraction
- CryptoMiniSat-style extraction
- competitive SAT solving
- industrial benchmark performance
- full DRAT/RAT/LRAT/FRAT support
- P vs NP progress
- `HARD` or `UNKNOWN` statuses

The main claim should remain:

Witnora-Core externally DRAT-verifies the recorded official CNFgen Tseitin rows,
including `tseitin_20 c=2`, using exact CNF XOR extraction and deterministic
sparse/min-fill XOR proof export against `original.dimacs`.

## If Overleaf Fails

Copy the full Overleaf compile log. Fix only LaTeX/package/formatting issues.
Do not change solver logic, benchmark logic, proof logic, XOR logic, or claim
boundaries.
