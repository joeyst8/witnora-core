# Release Notes v2.26

## What v2.26 Finalizes

v2.26 finalizes the public release/submission packet for Witnora after v2.25 public preprint preparation.

## Citation Hardening

The main related-work citation placeholders are replaced with bibliography-backed references covering SAT preprocessing, proof logging, affine/XOR reasoning, bounded treewidth and separators, circuit CNF encodings, SAT portfolios, and proof complexity/proof motifs.

## What Is Claimed

Witnora is framed as a certified collapse hierarchy for verifier-to-witness SAT reasoning with native certificates, obstruction-to-operator planning, planner-guided finite execution, G9-G13 soundness sketches, and TC-063 as a restricted theorem with proof obligations over SAF(c,r).

## What Is Not Claimed

No P-vs-NP proof, no P-vs-NP progress, no polynomial-time SAT algorithm, no all-SAT coverage, no hierarchy completeness, no unqualified theorem-proven status, and no external DRAT/LRAT/FRAT proof claim.

## How to Reproduce

Set `WITNORA_DRAT_TRIM` to a real `drat-trim.exe` and run `python -m unittest discover -s tests -v`.

## Artifact and Source Archive Expectations

The generated package artifact is `witnora-core-v2.26-submit-release-checklist-finalization.zip`. The source archive SHA is recorded after the source release archive is frozen.

## Reviewer Instructions

Reviewers should attack the bibliography, TC-063 assumptions, G5 affine soundness dependency, native-certificate boundary, finite-vs-family boundary, and forbidden-claim scan.

## Venue Strategy

The package is arXiv-ready after user approval. Workshop submission is ready after the user chooses a target and venue-specific formatting is applied.
