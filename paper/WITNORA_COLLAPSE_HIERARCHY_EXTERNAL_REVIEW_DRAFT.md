# Witnora: A Certified Collapse Hierarchy for Verifier-to-Witness SAT Reasoning

## Abstract

Witnora is a certified collapse-path framework for CNF SAT reasoning. It defines a hierarchy of operators G0-G14 whose outputs are mediated by native certificates and checkers. The framework includes obstruction-dual records, graph separator lift, composed orchestration, circuit projection, proof motif generalization, a self-expanding planner, and planner-guided execution. TC-063 is a restricted theorem with proof obligations over SAF(c,r). TC-063 is not an all-SAT theorem. Witnora does not claim a proof of P vs NP or a polynomial-time algorithm for SAT. TC-063 is stated as a restricted theorem with proof obligations over SAF(c,r), not as an all-SAT or hierarchy-completeness result. Native Witnora certificates are not DRAT/LRAT/FRAT proofs unless explicitly exported and externally checked. The package includes reproducibility artifacts, evidence manifests, and claim-boundary audits.

## Introduction

This preprint studies verifier-to-witness SAT reasoning as a certificate-backed collapse program. Witnora asks when a CNF instance can be transformed, decomposed, certified, planned, or checked through a bounded operator grammar without losing the connection to the original formula.

## Problem Framing

The project does not attempt to replace SAT solvers. It instead organizes collapse paths, obstruction fingerprints, native certificates, and proof obligations so that each finite result can be independently audited.

## Contributions

| contribution | claim | boundary |
| --- | --- | --- |
| Collapse hierarchy G0-G14 | A structured sequence of collapse grammars and theorem layers for SAT reasoning research. | Not all-SAT coverage and not hierarchy completeness. |
| Native certificate framework | Operators emit native certificates checked by Witnora checkers. | Native certificates are not DRAT/LRAT/FRAT unless exported and externally checked. |
| Obstruction-to-operator loop | Failure can produce obstruction fingerprints, operator recommendations, and certified promoted operators. | An obstruction fingerprint is not a SAT/UNSAT proof. |
| Certified composition and planner-guided execution | Finite plans can be paired with separate checked execution chains. | A plan alone is not execution and a matching execution is not a completeness theorem. |
| G9-G13 soundness backbone | Soundness is stated as proof sketches and proof obligations. | No unqualified theorem-proven status. |
| TC-063 restricted theorem with proof obligations | TC-063 is scoped to SAF(c,r), fixed c, supported r, and G5 affine residual checking. | Not an all-SAT theorem and not P-vs-NP progress. |
| Reproducible release/evidence manifests | The package records release evidence, claim boundaries, reviewer guides, and reproducibility steps. | Finite evidence supports implementation behavior but does not substitute for proof. |

## Related Work

### SAT Preprocessing and Inprocessing

SAT solvers use simplification, variable elimination, blocked clause elimination, and bounded structural reductions. Witnora overlaps with these ideas but frames them as a native certificate-centered collapse hierarchy with obstruction-to-operator feedback. TODO citation: classic SAT preprocessing and inprocessing surveys.

### Proof Logging and Certified SAT Solving

DRAT, LRAT, and FRAT style proof logging support externally checked SAT solving workflows. Witnora differs by using native operator certificates; external proof bridge not yet claimed unless a proof is exported and externally checked. TODO citation: DRAT/LRAT/FRAT proof logging references.

### XOR / Affine Reasoning

Gaussian elimination over GF(2), XOR extraction, and affine SAT tractability are standard tools for parity structure. Witnora uses this as G5 high-arity affine residue reasoning and as a dependency for TC-063 residual components. TODO citation: XOR reasoning in SAT and Gaussian-elimination-based SAT integration.

### Graph Separators and Bounded-Width Reasoning

Separator decomposition, bounded treewidth style reasoning, and component decomposition are established structural SAT approaches. TC-063 uses a fixed-size separator together with affine residual components; polynomiality is only for fixed separator bound c and supported affine extraction r. TODO citation: structural SAT and bounded treewidth references.

### Circuit CNF and Definitional Encodings

Tseitin-style auxiliary variables and exact definitional gates are common in circuit CNF encodings. G10 handles exact definitions only, rejects unsafe auxiliary projection, and trusts SAT lift only after checking the lifted assignment against the original CNF. TODO citation: Tseitin encodings and circuit-to-CNF references.

### SAT Portfolios / Algorithm Selection

Portfolio and algorithm-selection systems choose among solvers or tactics. G12 differs by producing a plan-only certificate with an explicit execution-required boundary; the plan does not certify SAT, UNSAT, or proof success. TODO citation: SAT portfolio and algorithm selection references.

### Proof Compression and Proof Motifs

Repeated proof patterns and macro-proof ideas motivate proof compression. G6 and G11 use checked motif certificates; near similarity is not treated as proof unless every reuse instantiation verifies. TODO citation: proof compression and macro-proof references.

## Collapse Grammar Hierarchy G0-G14

The hierarchy includes base simplification, XOR, symmetry, cardinality, capacity, affine residue, proof motif compression, obstruction dual certificates, separator lift, composed orchestration, circuit projection, proof motif generalization, collapse planning, planner-guided execution, and the bounded separator-affine theorem layer.

## Obstruction-to-Operator Loop

The v2.14-v2.18 line demonstrates failure fingerprinting, operator recommendation, and promotion into certified prototype operators. The loop is evidence of a research workflow, not a completeness theorem.

## Certified Operator Composition and Planner-Guided Execution

G9 requires checked step certificates, formula handoffs, and witness/proof lifts. G12 produces plan-only certificates. G13 pairs plans with separate execution certificates; execution results are trusted only if actual operator certificates and original-CNF obligations verify.

## G9-G13 Soundness Backbone

The G9-G13 backbone is expressed as proof sketches and proof obligations. It is not marked as unqualified theorem-proven.

## TC-063 Bounded Separator-Affine Collapse Theorem

TC-063 status: RESTRICTED_THEOREM_WITH_PROOF_OBLIGATIONS. Scope: SAF(c,r). TC-063 applies to fixed separator bound c, supported affine extraction bound r, exact G5 affine residual components, and native certificates only. G5 affine soundness is a dependency. There is no all-SAT claim, no P-vs-NP claim, and finite scaling is implementation support only. TC-063 is not theorem-proven-unqualified.

### How to Attack TC-063

Reviewers should attack the separator decomposition lemma, assignment exhaustiveness, G5 affine soundness dependency, SAT lifting, UNSAT cover, polynomial bound, native certificate boundary, and restricted scope.

## Reproducibility

The release includes package manifests, source/artifact SHA records where available, tests, reproduction instructions, claim-boundary audits, and reviewer-facing checklists.

## Limitations

- No P-vs-NP proof.
- No polynomial-time SAT algorithm.
- No all-SAT or hierarchy-completeness claim.
- TC-063 is restricted to SAF(c,r).
- TC-063 remains RESTRICTED_THEOREM_WITH_PROOF_OBLIGATIONS.
- G5 affine soundness is a dependency.
- Native certificates are not DRAT/LRAT/FRAT.
- Finite tests and scaling runs support implementation, not proof.
- External proof bridge is absent.
- Planner certificates are plan-only unless paired with verified execution certificates.
- Polynomiality for TC-063 is only for fixed separator bound c and supported affine extraction r.
- Exponential dependence on c is explicit.

## Claim Boundaries

This preprint does not claim P-vs-NP progress, polynomial-time SAT, all-SAT coverage, hierarchy completeness, unqualified theorem-proven status, or external DRAT/LRAT/FRAT proof status.

## Future Work

Future work includes external formalization of TC-063, proof-assistant checking of native checkers, external proof bridges, broader benchmarks, and choosing an appropriate preprint or workshop target.
