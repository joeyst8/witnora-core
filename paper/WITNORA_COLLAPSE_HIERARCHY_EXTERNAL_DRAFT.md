# Witnora Collapse Hierarchy: Certificate-Backed Operator Discovery for Verifier-to-Witness Collapse

## Abstract

Witnora is a certificate-backed collapse hierarchy and operator-discovery program for studying verifier-to-witness collapse. It compares bounded grammars, emits native certificates where implemented, and records proof obligations where evidence remains empirical.

## Introduction

The project studies when structured CNF verifier instances admit deterministic, replayable collapse paths to witnesses or proof certificates. The current artifact packages the G0-G6 hierarchy, finite certificates, empirical edge evidence, and reviewer-facing reproduction steps.

## Motivation: Verifier-to-Witness Collapse

The long-range motivation is to understand routes from efficiently checkable verifier instances to efficiently discoverable witnesses or certificates. Witnora treats this as an experimental theorem-building program, not as a solved complexity question.

## Non-Claims

This work does not prove P vs NP.
This work does not claim a polynomial-time SAT algorithm.
Strictness is only claimed where a finite strictness certificate with lower obstruction evidence is verified.
FINITE_EMPIRICAL_EDGE_DELTA_CERTIFIED is not a lower-bound proof.
Native certificates are not DRAT proofs unless explicitly exported and checked.
The hierarchy is a research program, not a complete SAT algorithm.

## Bounded Collapse Classes W_B(G)

For a bound profile B and grammar G, W_B(G) is the operational set of formulas for which Witnora emits a SAT witness verified against the original CNF, an externally checked proof, or an accepted native certificate whose checker succeeds within configured bounds.

## Grammar Hierarchy G0-G6

- G0_BASE: UP, PLE, SUB, BCE, VE, components, 2SAT, bounded treewidth.
- G1_XOR: G0 plus exact bounded XOR extraction and affine elimination.
- G2_SYMMETRY_CERTIFIED: exact automorphism validation and SAT witness reconstruction.
- G3_SYMMETRY_CARDINALITY_CERTIFIED: exact AMO/ALO and pigeonhole counting certificates.
- G4_ORBIT_CAPACITY_COUNTING_PROTOTYPE: local Hall/capacity-deficit native certificates.
- G5_HIGH_ARITY_AFFINE_RESIDUE_PROTOTYPE: exact high-arity GF(2) native certificates.
- G6_PROOF_MOTIF_COMPRESSION_PROTOTYPE: native macro-proof motif certificates.

## Native Certificate Types

Native certificates include width obstruction records, XOR/GF(2) certificates, symmetry witness reconstruction, pigeonhole counting, orbit-capacity deficits, affine residue traces, and proof-motif macro certificates. Native certificates are checked by Witnora-native checkers and are not DRAT proofs unless explicitly exported and checked.

## Operator Genesis

Operator genesis extracts obstruction fingerprints and proposes operator schemas. Generated candidates are not trusted until implemented, checked, tested, red-teamed, and frozen.

## Finite Strictness Certificate: G0_WIDTH_C -> G1_XOR

v2.10 records `FINITE_STRICTNESS_CERTIFIED` for finite restricted witnesses: `tseitin_10`, `xor_chain_unsat_n5`, `tseitin_12`, `xor_chain_unsat_n7`, `tseitin_14`, and `xor_chain_unsat_n9`. The lower side has certified width obstruction; the upper side has verified G1 XOR evidence. This is finite and restricted, not a scalable family theorem.

## Finite Empirical Edge Delta: G1_XOR -> G2_SYMMETRY_CERTIFIED

v2.11 records `FINITE_EMPIRICAL_EDGE_DELTA_CERTIFIED` for `cycle_4_3color`, `cycle_6_3color`, `cycle_8_3color`, and `cycle_10_3color`. The lower side is bounded replay no-collapse under G1_XOR, not a lower-bound proof. The upper side verifies G2 symmetry SAT witness reconstruction.

## Empirical Evidence for G2-G6

G2-G6 evidence includes pigeonhole/cardinality certificates, local Hall/capacity-deficit certificates, high-arity affine residue certificates, and proof motif macro-certificates. These are empirical operator-delta records unless a stricter proof object is explicitly supplied.

## Proof Obligations

Open obligations include full G0_BASE non-collapse, scalable family lower bounds, checker soundness writeups, cost-model completeness, and external proof bridges where sound.

## Gap Analysis

Open gaps include random 3-SAT, general circuit-SAT, arbitrary PB encodings, non-exact affine patterns, realistic SAT competition instances, and formulas where no confident obstruction fingerprint is found.

## Relationship to P vs NP

P vs NP is the long-range motivation. Witnora studies certificate-backed collapse structure that may clarify verifier-to-witness routes, while explicitly avoiding progress claims.

## Why This Does Not Prove P vs NP

The current results are bounded, operational, and finite or empirical unless otherwise labeled. They do not establish general lower bounds, hierarchy completeness, or a polynomial-time algorithm for SAT.

## Reproducibility

The v2.12 package includes release SHA records, evidence summaries, claim-boundary tables, reproduction steps, validation scripts, and a package manifest. The expected full test command is `python -m unittest discover -s tests -v` with real drat-trim configured when available.

## Limitations

Finite certificates do not imply family theorems. Empirical edge deltas do not imply lower bounds. Native certificates do not replace external proof formats unless a bridge is checked against the original CNF.

## Future Work

Next work should either submit the package for external review or add another finite edge certificate while preserving the evidence-grade distinction introduced in v2.10 and v2.11.
