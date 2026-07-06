# Reviewer Guide v2.24

## What to Inspect First

Read the external review draft, TC-063 appendix, G9-G13 appendix, claim-boundary table, and evidence manifest.

## How to Reproduce Tests

Set `WITNORA_DRAT_TRIM` to a real `drat-trim.exe`, then run `python -m unittest discover -s tests -v`.

## Where TC-063 Lives

Inspect `TC063_THEOREM_APPENDIX.md`, `tc063_obligation_manifest.json`, and `theory/TC063_BOUNDED_SEPARATOR_AFFINE_HARDENED_THEOREM.md`.

## Where Proof Obligations Live

Read `tc063_obligation_manifest.json`, `G9_G13_SOUNDNESS_APPENDIX.md`, and the theory lemma files.

## What Claims Are Not Made

No P vs NP proof, no P vs NP progress, no all-SAT coverage, no hierarchy completeness, no polynomial-time arbitrary SAT claim, no fake DRAT claim, and no unqualified theorem-proven claim.

## How to Verify Archives and SHAs

Compare release entries in `artifact_sha_manifest.json` and `evidence_manifest.json` against local source and artifact zips.

## How to Inspect Native Certificates

Inspect native checker modules and their tests. Native means Witnora-checkable, not external DRAT/LRAT/FRAT.

## How to Attack the Framework

Attack G5 affine soundness, separator decomposition, UNSAT cover, native certificate boundary, finite-vs-family boundary, and claim-boundary wording.

## How to Audit Claim Boundaries

Read `CLAIM_BOUNDARY_TABLE.md` and `claim_boundary_manifest.json`, then compare against the paper draft and appendices.

## Known Limitations

Native checkers are not proof-assistant verified. TC-063 has proof obligations. Finite tests support implementation only. The hierarchy may need a lattice formalization.
