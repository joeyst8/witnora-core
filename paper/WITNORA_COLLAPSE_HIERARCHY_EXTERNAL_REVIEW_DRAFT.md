# Witnora Collapse Hierarchy: External Review Draft

## Abstract

Witnora is a certified collapse-research framework for studying verifier-to-witness collapse through operator grammars, native certificates, obstruction fingerprints, planner-guided finite executions, and restricted theorem candidates. Witnora does not claim a proof of P vs NP.

## Introduction

The project studies how SAT verification structure can sometimes be turned into witnesses, certificates, or proof obligations. The current package is designed for external attack and review.

## Problem Framing

The central question is how collapse operators can be stated, checked, composed, planned, and theoremized without overstating their scope.

## Related-Work Positioning

Witnora touches SAT preprocessing, certified SAT solving, structural SAT, affine reasoning, symmetry, cardinality, proof compression, automated theorem search, and AI reasoning evaluation. The contribution is the certificate-backed collapse hierarchy and reviewable obligation structure, not novelty of every individual primitive.

## Collapse Grammar Hierarchy G0-G14

The hierarchy now spans base simplification, XOR, symmetry, cardinality, capacity, affine residue, proof motif compression, obstruction dual certificates, separator lift, composed orchestration, circuit projection, proof motif generalization, collapse planning, planner-guided execution, and the bounded separator-affine theorem layer.

## Obstruction-To-Operator Loop

v2.14 identifies obstruction fingerprints and promotes graph separator, circuit projection, proof motif generalization, and composed orchestration directions.

## Certified Operators and Native Certificates

Native certificates are checked by Witnora checkers. Native certificates are not DRAT/LRAT/FRAT unless explicitly exported and externally checked.

## Composed Operator Orchestration

G9 composes certified operator steps only when step certificates, formula hashes, handoffs, and witness/proof lifts verify.

## Circuit Projection Lift

G10 projects only exact definitional gate encodings and requires lifted SAT witnesses to satisfy the original CNF.

## Proof Motif Generalization

G11 treats near-motif similarity as diagnostic until every concrete or parametric instantiation verifies.

## Self-Expanding Collapse Planner

G12 produces plan-only certificates. Planner certificates are plan-only unless paired with separate verified execution certificates.

## Planner-Guided Execution Loop

G13 pairs a verified plan with a separate verified execution chain. Matching a plan on finite fixtures does not prove all plans succeed.

## Soundness Theoremization G9-G13

v2.21 records G9-G13 soundness as formal proof sketches and proof obligations, not as mechanized proven theorems.

## TC-063 Bounded Separator-Affine Family Theorem

TC-063 is a restricted theorem with proof obligations over SAF(c,r), not an all-SAT theorem. It depends on fixed separator bound c, supported affine extraction bound r, G5 affine checker soundness, complete separator assignment enumeration, original-CNF SAT witness verification, and complete UNSAT cover verification.

## Experiments / Finite Evidence

Finite evidence supports implementation behavior but does not substitute for a family proof.

## Reproducibility

The v2.24 package includes release manifests, SHA records, tests, and reproduction instructions for external review.

## Claim Boundaries

No P vs NP proof, P vs NP progress, polynomial-time SAT, all-SAT coverage, hierarchy completeness, fake DRAT claim, or unqualified theorem-proven claim is made.

## Limitations

Native checkers are not proof-assistant verified. TC-063 has proof obligations. Several claims are finite evidence or proof sketches. The current hierarchy may need a lattice formalization.

## Future Work

External formalization of TC-063, G5 checker soundness, DRAT/LRAT/FRAT bridges, broader benchmark pressure, and proof-assistant integration are natural next steps.

## Appendix Pointers

See `TC063_THEOREM_APPENDIX.md`, `G9_G13_SOUNDNESS_APPENDIX.md`, `CLAIM_BOUNDARY_TABLE.md`, and `REPRODUCIBILITY_GUIDE.md`.
