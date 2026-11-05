# Witnora: A Certified Collapse Hierarchy for Verifier-to-Witness SAT Reasoning

## Abstract

Witnora is a certified collapse-path framework for CNF SAT reasoning. It defines a hierarchy of operators G0-G14 whose outputs are mediated by native certificates and checkers. The framework includes obstruction-dual records, graph separator lift, composed orchestration, circuit projection, proof motif generalization, a self-expanding planner, and planner-guided execution. TC-063 is a restricted theorem with proof obligations over SAF(c,r). TC-063 is not an all-SAT theorem. Witnora does not claim a proof of P vs NP or a polynomial-time algorithm for SAT. TC-063 is stated as a restricted theorem with proof obligations over SAF(c,r), not as an all-SAT or hierarchy-completeness result. Native Witnora certificates are not DRAT/LRAT/FRAT proofs unless explicitly exported and externally checked. The package includes reproducibility artifacts, evidence manifests, claim-boundary audits, and a completed bibliography.

## Introduction

Witnora studies verifier-to-witness SAT reasoning as a certificate-backed collapse program. The project asks when a CNF instance can be transformed, decomposed, certified, planned, or checked through a bounded operator grammar while retaining an explicit connection to the original formula.

## Problem Framing

The framework does not attempt to replace SAT solvers or assert a universal collapse path. It organizes collapse operators, obstruction fingerprints, native certificates, theorem candidates, proof obligations, and finite execution evidence so that each claim can be audited separately.

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

SAT preprocessing and inprocessing remove or simplify structure through techniques such as variable elimination, blocked clause elimination, covered clause elimination, and other bounded reductions [een-biere-2005-effective-preprocessing; biere-jarvisalo-kiesl-2021-preprocessing; heule-jarvisalo-biere-2011-covered-clause]. Witnora uses preprocessing-like ideas as collapse operators, but the unit of evidence is a native certificate and a checker obligation. Witnora does not claim novelty for variable elimination, blocked clauses, or simplification themselves; the claim is the certificate-centered collapse hierarchy and obstruction-to-operator loop.

### Proof Logging and Certified SAT Solving

DRAT-trim, DRAT, LRAT, and FRAT provide proof logging and checking pathways for SAT solvers [wetzler-heule-hunt-2014-drat-trim; heule-2016-drat-format; cruz-filipe-heule-hunt-kaufmann-schneiderkamp-2016-lrat; baek-carneiro-heule-2021-frat]. Witnora relates to this line because it also treats checking as central. Witnora differs by using native operator certificates for collapse-specific evidence. Native Witnora certificates are not DRAT/LRAT/FRAT proofs unless explicitly exported and externally checked.

### XOR / Affine Reasoning

Gaussian elimination over GF(2), XOR extraction, and affine SAT reasoning are established polynomial-time tools for parity structure, including XOR-aware solvers such as CryptoMiniSat [soos-nohl-castelluccia-2009-cryptominisat]. Witnora uses affine reasoning as G5 and as a dependency inside TC-063. Witnora does not claim to discover Gaussian elimination; its contribution is the integration of exact affine residual certificates into the collapse hierarchy and the SAF(c,r) theorem boundary.

### Graph Separators and Bounded-Width Reasoning

Tree decompositions, treewidth algorithms, and separator-style decompositions are classical routes to structural tractability [robertson-seymour-1986-treewidth; bodlaender-1996-treewidth]. TC-063 uses a narrower construction: a fixed-size separator plus exact affine residual components. The polynomial bound is only for fixed separator bound c and supported affine extraction r, and TC-063 does not claim bounded-width completeness or coverage of arbitrary separator formulas.

### Circuit CNF and Definitional Encodings

Tseitin-style transformations and definitional CNF encodings introduce auxiliary variables to represent circuits equisatisfiably [tseitin-1968-propositional-calculus]. G10 is related to this work because it projects only exact definitional gates. It differs by requiring checker-verifiable definitions, direct original-CNF SAT witness validation, and equisatisfiability obligations for UNSAT preservation. It does not project arbitrary auxiliaries.

### SAT Portfolios / Algorithm Selection

SAT portfolio systems such as SATzilla select among solvers using per-instance features and empirical models [xu-hutter-hoos-leytonbrown-2011-satzilla]. G12 is related at the level of strategy selection, but it emits a plan-only certificate rather than choosing a solver result. The plan explicitly requires later certified execution; it does not certify SAT, UNSAT, DRAT, or theorem success.

### Proof Compression and Proof Motifs

Proof complexity and proof-system work studies proof representations, proof lengths, and proof checking [cook-reckhow-1979-proof-systems]. Witnora's G6 and G11 are related to proof compression and repeated proof motifs, but similarity is never treated as proof. Generalized motif reuse is trusted only when every concrete instantiation or verified parametric instantiation checks.


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

Future work includes external formalization of TC-063, proof-assistant checking of native checkers, external proof bridges, broader benchmarks, and venue-specific formatting after the user chooses a target.

## References

See `paper/references.bib` for structured bibliography entries.
