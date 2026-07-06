# Release Notes v2.25

## What v2.25 Is

v2.25 prepares a public preprint and external submission package for Witnora.

## What Changed From v2.24

It adds a public title, polished abstract, contribution list, related work, limitations, release notes, reviewer outreach email, submission checklist, and validation tests.

## What Is Claimed

Witnora is presented as a certified collapse hierarchy for verifier-to-witness SAT reasoning, with native certificates, obstruction-to-operator planning, planner-guided finite execution, G9-G13 proof sketches, and TC-063 as a restricted theorem with proof obligations.

## What Is Not Claimed

No P-vs-NP proof, no P-vs-NP progress, no polynomial-time SAT algorithm, no all-SAT coverage, no hierarchy completeness, no unqualified theorem-proven status, and no external DRAT/LRAT/FRAT proof claim.

## How to Reproduce

Run `python -m unittest discover -s tests -v` with `WITNORA_DRAT_TRIM` set to a real `drat-trim.exe`.

## Artifact and Source Archive Expectations

The generated package artifact is `witnora-core-v2.25-public-preprint-preparation.zip`. Source archive SHA values are recorded after freeze.

## SHA Placeholders

Before freeze, source archive SHA may be `PENDING_SOURCE_ARCHIVE_FREEZE`.

## Reviewer Instructions

Attack TC-063, G5 affine soundness, native certificate assumptions, claim boundaries, related-work positioning, and reproducibility.
