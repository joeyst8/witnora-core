# Reviewer Guide

## What to read first

Read the external paper draft, then the contribution table, evidence summary, claim-boundary appendix, and reviewer objection table.

## What to reproduce first

Run the full unit suite, validate the v2.12 package, then validate the v2.13 hardening package.

## How to run validation

`python scripts/validate_v2_13_paper_package.py --package-root outputs/v2.13-paper-hardening-reviewer-defense`

## How to inspect v2.10 finite strictness certificate

Inspect the G0_WIDTH_C -> G1_XOR evidence row. Confirm `FINITE_STRICTNESS_CERTIFIED` appears only where certified lower obstruction evidence exists.

## How to inspect v2.11 finite empirical edge delta

Inspect the G1_XOR -> G2_SYMMETRY_CERTIFIED row. Confirm lower replay is bounded non-acceptance, not a lower-bound proof.

## How to inspect evidence grades

Check `EVIDENCE_SUMMARY.md` and verify v2.10 remains `FINITE_STRICTNESS_CERTIFIED` while v2.11 remains `FINITE_EMPIRICAL_EDGE_DELTA_CERTIFIED`.

## How to inspect claim boundaries

Read `CLAIM_BOUNDARY_APPENDIX.md` and compare allowed wording, forbidden wording, reason, and validation guard.

## What Witnora claims

Witnora claims a certificate-backed collapse hierarchy and operator-discovery program with finite certificates, empirical edge deltas, native certificates, and explicit proof obligations.

## What Witnora does not claim

It does not claim P vs NP progress, polynomial-time SAT, hierarchy completeness, peer-review acceptance, or family theorems from finite certificates.

## Known weaknesses

Current witnesses are often controlled. Native checkers are not proof-assistant verified. Several hierarchy edges remain empirical rather than theorem-proven. The current chain may later need a lattice formalization.

## Suggested reviewer questions

- Are W_B(G) definitions useful?
- Is finite strictness certification meaningful?
- Is the empirical edge-delta label honest?
- Are native certificates adequate for this research program?
- Which proof obligation should be attacked next?
- Which operator is most novel?
- Should the hierarchy be a lattice instead of a chain?
- Is the paper framing acceptable as a workshop/system/research-program paper?
