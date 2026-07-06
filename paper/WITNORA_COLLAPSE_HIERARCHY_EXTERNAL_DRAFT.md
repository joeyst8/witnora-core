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

## Related Work

Witnora is positioned near several established lines of work: SAT preprocessing, certified SAT solving, DRAT/LRAT/FRAT-style proof logging, bounded-treewidth and structural SAT algorithms, XOR/affine reasoning, symmetry reasoning, cardinality and pseudo-Boolean reasoning, proof compression and macro-proof ideas, automated theorem/proof search, and AI reasoning evaluation.

The contribution is not that every individual operator is new. Many ingredients are known or related to known proof and solving techniques. Witnora's contribution is the certificate-backed collapse hierarchy, evidence grading, operator-genesis loop, native certificate taxonomy, and proof-obligation discipline for studying verifier-to-witness collapse.

## Contribution Table

| Contribution | What is claimed | Evidence type | What is not claimed |
| --- | --- | --- | --- |
| Bounded collapse hierarchy G0-G6 | Operational hierarchy of bounded collapse grammars | Research program / empirical evidence | Complete SAT algorithm or hierarchy completeness |
| Native certificate taxonomy | Distinct native certificate objects and checkers | Checker-backed artifacts | Native certificates as DRAT unless exported and checked |
| Operator Genesis Engine | Candidate operator schemas from obstruction fingerprints | Generated candidates / proof obligations | Autonomous theorem discovery or implemented success by default |
| Generated operators G4/G5/G6 | Three generated candidates promoted to prototypes | Empirical operator evidence | General matching, modular, or proof-compression completeness |
| Finite strictness certificate G0_WIDTH_C -> G1_XOR | Finite restricted strictness with lower obstruction evidence | FINITE_STRICTNESS_CERTIFIED | Full G0_BASE or scalable family theorem |
| Finite empirical edge-delta certificate G1_XOR -> G2_SYMMETRY_CERTIFIED | Finite replayed delta with upper witness verification | FINITE_EMPIRICAL_EDGE_DELTA_CERTIFIED | Lower-bound proof or strictness theorem |
| Proof-obligation matrix | Explicit obligations for theorem promotion | Formal proof obligations | Obligations discharged by naming them |
| Reproducibility package | External review packet and replay scripts | Package validation | Peer-review acceptance |
| Claim-boundary table | Allowed and forbidden wording with tests | Validation guards | Elimination of all future review risk |

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

## Reviewer Objection Table

| Objection | Response |
| --- | --- |
| This does not prove P vs NP. | Correct. P vs NP is only motivation. No P vs NP progress is claimed. |
| This is finite evidence, not a family theorem. | Correct. v2.10 is finite strictness certification; family theorem remains a proof obligation. |
| Empirical edge deltas are not lower bounds. | Correct. v2.11 explicitly labels them FINITE_EMPIRICAL_EDGE_DELTA_CERTIFIED. |
| Native certificates are not DRAT. | Correct. Native certificates are independently checked by Witnora checkers; DRAT is only claimed when exported and externally checked. |
| Some operators are known ideas. | Correct. Witnora's novelty is the certificate-backed hierarchy, operator-genesis loop, evidence grading, and proof-obligation structure. |
| The hierarchy may be a lattice, not a line. | Correct. The current line is an operational sequence; partial-order/lattice formalization is future work. |
| The system is synthetic/crafted. | Partly correct. Current families are controlled witnesses for operator behavior; broader benchmarks are a future gap. |
| Why no external peer review yet? | v2.13 prepares the artifact for external review; no peer-review acceptance is claimed. |

## Gap Analysis

Open gaps include random 3-SAT, general circuit-SAT, arbitrary PB encodings, non-exact affine patterns, realistic SAT competition instances, and formulas where no confident obstruction fingerprint is found.

## Relationship to P vs NP

P vs NP is the long-range motivation. Witnora studies certificate-backed collapse structure that may clarify verifier-to-witness routes, while explicitly avoiding progress claims.

## Why This Does Not Prove P vs NP

The current results are bounded, operational, and finite or empirical unless otherwise labeled. They do not establish general lower bounds, hierarchy completeness, or a polynomial-time algorithm for SAT.

## Reproducibility

The v2.12 package includes release SHA records, evidence summaries, claim-boundary tables, reproduction steps, validation scripts, and a package manifest. The expected full test command is `python -m unittest discover -s tests -v` with real drat-trim configured when available.

## Limitations

This work reports no P vs NP progress and no polynomial-time SAT algorithm.

It does not claim hierarchy completeness, and finite certificates do not imply family theorems. Empirical edge deltas are not strictness theorems. Native certificates are not DRAT unless exported and checked. The current hierarchy is operational and may later become a partial order or lattice rather than a line.

Many instances are controlled or synthetic witnesses for operator behavior. Broader external benchmarks remain future work. Native checkers are not formally verified proof-assistant artifacts.

## Claim-Boundary Appendix

| Claim | Allowed wording | Forbidden wording | Reason | Test/validation guard |
| --- | --- | --- | --- | --- |
| P vs NP | P vs NP is a long-range motivation. | Witnora proves P vs NP progress. | The package contains bounded artifacts, not a complexity-theory resolution. | NO_PNP_CLAIM_PASS |
| Polynomial-time SAT | This work does not claim a polynomial-time SAT algorithm. | Witnora is a polynomial-time SAT algorithm. | The hierarchy is a bounded research program. | NO_POLYTIME_SAT_CLAIM_PASS |
| Hierarchy completeness | The hierarchy is a research program. | The G0-G6 hierarchy is complete. | Gaps and proof obligations remain open. | NO_HIERARCHY_COMPLETENESS_CLAIM_PASS |
| Full hierarchy strictness | Edges have graded evidence. | All hierarchy edges are strict theorems. | Only v2.10 has finite strictness with lower obstruction. | EVIDENCE_SUMMARY_GRADES_PASS |
| Full G0_BASE strictness | v2.10 concerns restricted G0_WIDTH_C. | Full G0_BASE strictness is proven. | Full G0 contains routes not discharged by the finite width certificate. | FINITE_STRICTNESS_G0_G1_SUMMARY_PASS |
| Finite strictness certificate | FINITE_STRICTNESS_CERTIFIED is finite and restricted. | Finite certificates prove scalable family theorems. | The scope is finite and restricted. | NO_FALSE_FAMILY_THEOREM_CLAIM_PASS |
| Finite empirical edge delta | FINITE_EMPIRICAL_EDGE_DELTA_CERTIFIED records replayed finite delta evidence. | The empirical edge delta is a strictness theorem. | G1 lower replay is not obstruction proof. | FINITE_EDGE_DELTA_NOT_STRICTNESS_PASS |
| Native certificate vs DRAT | Native certificates are not DRAT proofs unless explicitly exported and checked. | Native certificates are DRAT proofs. | Native checkers and external proof formats have different trust semantics. | NATIVE_CERT_NOT_DRAT_PASS |
| Generated operator vs theorem | Generated operators are prototypes or candidates unless obligations are discharged. | Generated operators are theorems. | Implementation evidence and theorem evidence are separate. | NO_NEW_OPERATOR_PASS |
| Replayed no-collapse vs lower-bound proof | LOWER_REPLAY_NO_COLLAPSE is bounded replay evidence. | Replay no-collapse is a lower-bound proof. | A lower-bound proof requires an independently checked obstruction. | NO_FALSE_LOWER_BOUND_CLAIM_PASS |
| Empirical evidence vs family theorem | EMPIRICAL_EVIDENCE_NOT_THEOREM marks bounded evidence and proof obligations. | Empirical evidence is a family theorem. | Scaling and lower-bound obligations remain open. | NO_FALSE_FAMILY_THEOREM_CLAIM_PASS |

## Future Work

Next work should either submit the package for external review or add another finite edge certificate while preserving the evidence-grade distinction introduced in v2.10 and v2.11.
