# Collapse Grammar Program

## v2.8 Hierarchy Theoremization

v2.8 formalizes the complete G0-G6 hierarchy as a bounded research program:

`G0_BASE -> G1_XOR -> G2_SYMMETRY_CERTIFIED -> G3_SYMMETRY_CARDINALITY_CERTIFIED -> G4_ORBIT_CAPACITY_COUNTING_PROTOTYPE -> G5_HIGH_ARITY_AFFINE_RESIDUE_PROTOTYPE -> G6_PROOF_MOTIF_COMPRESSION_PROTOTYPE`.

The output is a theoremization bundle: definitions, empirical strictness
evidence, theorem candidates, proof obligations, gap analysis, and a draft
paper. It does not add an operator and does not prove strictness,
completeness, lower bounds, or P vs NP progress.

## Verifier-to-Witness Motivation

Witnora studies whether structured verifier instances can be transformed by
deterministic, replayable routes into witnesses or externally checked proofs.

## Collapse Grammars

A collapse grammar is a finite set of deterministic transformations and
terminal tractable classes. A run either finds a replayable path or records that
no path was found under the configured resource bounds.

## Bounded Collapse Classes W_B(G)

For a grammar `G` and bound profile `B`, `W_B(G)` is the observed set of
formulas that collapse under `G` within `B` and emit a valid certificate/proof
when required. The bound profile includes caps such as width, XOR arity,
runtime, proof size, search nodes, operator depth, and symmetry diagnostic
limits.

The unbounded notation `W(G)` is aspirational/theoretical in the Witnora
program. Current releases report `W_B(G)` evidence only.

## Strictness Witnesses

A strictness witness records a family, a base grammar, an extended grammar, an
added operator, and certificate-backed evidence that the observed public
category changed.

## Operator Hierarchy

The v2.0 hierarchy starts with `G0_BASE`, adds exact affine reasoning in
`G1_XOR`, and keeps Horn, cardinality, and backdoor routes as honest stubs for
future work.

v2.1 adds a diagnostic `G2_SYMMETRY_PROTOTYPE` layer. It records syntactic
candidate orbits over variables, literals, and clauses. This is not full graph
automorphism detection and does not by itself define a satisfiability-preserving
quotient.

v2.2 adds `G2_SYMMETRY_CERTIFIED` for small formulas with exact automorphism
evidence. A native symmetry certificate can validate generators, recompute
orbits, record symmetry-breaking predicates, and verify reconstructed SAT
witnesses against the original CNF. It is not an external UNSAT proof unless a
DRAT proof against the original CNF is checked.

v2.3 adds `G3_SYMMETRY_CARDINALITY_CERTIFIED`, which recognizes standard
pigeonhole assignment variables `x[pigeon,hole]`, checks ALO/AMO clauses
against the original CNF, and emits a native counting certificate for `n > m`.
This is native certification, not DRAT and not a complete PB solver.

v2.4 adds an Operator Genesis layer. It extracts obstruction fingerprints and
generates candidate operator schemas with trigger signatures, preservation
obligations, certificate sketches, promotion criteria, and theorem-candidate
queue entries. Generated schemas are not implemented operators.

v2.5 adds `G4_ORBIT_CAPACITY_COUNTING_PROTOTYPE`, the first implemented
prototype promoted from a generated operator candidate. It checks local
Hall/capacity deficits over exact assignment/resource CNFs and emits native
certificates when the provided subset and capacity evidence verify against the
original formula. This is not a complete matching or allocation solver, and
complete matching rows that duplicate G3 pigeonhole are not counted as novel G4
deltas.

v2.6 adds `G5_HIGH_ARITY_AFFINE_RESIDUE_PROTOTYPE`, the second implemented
prototype promoted from a generated operator candidate. It checks exact full
forbidden-assignment CNF encodings of high-arity GF(2) affine equations and
emits native Gaussian-elimination certificates. This extends the bounded arity
frontier beyond G1's lower exact-XOR cap, but it is not heuristic XOR mining,
not CryptoMiniSat-style extraction, not broad modular arithmetic solving, and
not DRAT.

v2.7 adds `G6_PROOF_MOTIF_COMPRESSION_PROTOTYPE`, the third implemented
prototype promoted from a generated operator candidate. It checks repeated
native proof motifs by verifying one template proof and every reuse
instantiation, then emits a compressed macro-proof certificate. This is not
DRAT, not proof-compression completeness, and not a novel Tseitin claim when
prior XOR grammars already apply.

v2.14 adds `G7_OBSTRUCTION_DUAL_CERTIFICATE_PROTOTYPE`, which records bounded
G0-G6 non-certification traces, obstruction fingerprints, proof obligations,
and missing-operator recommendations. G7 does not solve the row and does not
turn replay failure into a lower-bound proof.

v2.15 adds `G8_GRAPH_SEPARATOR_LIFT_PROTOTYPE`, promoted from G7's
`GRAPH_SEPARATOR_OBSTRUCTION` recommendation. G8 uses exact primal separators,
component conditioning under separator assignments, SAT witness lift, and UNSAT
separator cover. Its native certificate is not DRAT and not a separator
completeness theorem.

v2.16 adds `G9_COMPOSED_OPERATOR_ORCHESTRATION_PROTOTYPE`, promoted from G7's
`COMPOSED_OBSTRUCTION` recommendation. G9 is a certificate-chain layer: every
operator step must verify its input formula hash, output formula hash, native
step certificate, preservation type, and lift rule, and every handoff between
steps must match. SAT composition verifies the final lifted witness against the
original CNF. UNSAT composition requires preservation through every step. This
is not arbitrary transformation chaining, not DRAT, and not a composition
completeness theorem.

v2.17 adds `G10_CIRCUIT_PROJECTION_LIFT_PROTOTYPE`, promoted from G7's
`CIRCUIT_PROJECTION_SIGNAL` recommendation. G10 detects exact definitional
gate encodings, projects only verified auxiliary variables, recomputes the core
formula hash, and lifts SAT witnesses by evaluating the gate definitions. UNSAT
projection is accepted only when the projection chain is
equisatisfiability-preserving for the supported exact definitional family. This
is not arbitrary auxiliary projection, not DRAT, and not a complete circuit-SAT
method.

v2.18 adds `G11_PROOF_MOTIF_GENERALIZATION_CHECKER_PROTOTYPE`, promoted from
G7's `PROOF_MOTIF_NEAR_MISS` recommendation. G11 turns near-repetition into a
certificate only when the generalized template and every concrete reuse
instantiation verify over the original CNF. Loose similarity is
diagnostic-only. Exact G6 motif duplicates are not counted as novel G11
deltas. This is not arbitrary proof-pattern learning, not DRAT, and not a
proof-motif completeness theorem.

v2.19 adds `G12_SELF_EXPANDING_COLLAPSE_PLANNER_PROTOTYPE`, a planning layer
over G0-G11. G12 verifies plan structure, operator compatibility, handoff
requirements, missing-operator hypotheses, and claim boundaries. It does not
execute the plan and does not certify SAT, UNSAT, DRAT, a theorem, or hierarchy
completeness. Its evidence grade is `FINITE_PLANNER_CERTIFICATE_VERIFIED`.

## Theorem Candidates

Theorem candidates are tracked with explicit statuses: conjecture, empirical
evidence, proof sketch, refuted, or open. A candidate is not a theorem until its
proof obligations are discharged. The initial registry includes bounded XOR
strictness, formal XOR strictness on Tseitin, a symmetry collapse conjecture,
and a collapse obstruction conjecture.

## Collapse Obstructions

Obstruction records explain bounded non-collapse under a configured grammar and
profile. They can cite treewidth over cap, XOR arity over cap, absent exact XOR
patterns, symmetry signals without a certified quotient, unsupported
cardinality/Horn structure, proof export blowup, or search caps. These records
guide operator discovery; they are not lower-bound claims.

## Relationship to P vs NP

Witnora does not claim progress on P vs NP. It provides a certificate-backed
experimental framework for studying when verifier instances admit deterministic
collapse paths to witnesses or proofs.

## Why This Does Not Prove P vs NP

The lab reports bounded, configured experiments. A no-collapse result is not a
lower bound against all algorithms, and a collapse result for a family slice is
not a general SAT-solving result.

## Research Agenda

1. Expand exact operators only when their evidence can be replayed.
2. Separate native traces from external proof certification.
3. Preserve no-collapse rows honestly.
4. Use frontier diagnostics to prioritize operators.
5. Freeze claims only after tests, artifacts, and red-team review.
6. Turn obstruction records into certified operators only when witness
   reconstruction or proof preservation is explicit.
7. Treat symmetry-breaking predicates as preservation obligations, not as
   clauses implied by the original formula unless an external proof checker
   accepts them.
8. For cardinality/counting operators, verify the exact original-CNF structure
   before emitting native semantic certificates.
9. Treat generated operator schemas as research objects until implemented,
   independently checked, tested, red-teamed, and frozen.
10. For generated operator prototypes, distinguish duplicate controls from true
    operator deltas and keep native certificates separate from DRAT claims.
11. For high-arity affine operators, require exact full-CNF evidence,
    deterministic GF(2) row operations, and explicit rejection of incomplete,
    wrong-parity, or over-cap encodings.
12. For proof-motif operators, trust reuse only after expanding and checking
    every instantiation against original source clauses.
13. For composed orchestration, trust a chain only when all formula handoffs,
    step certificates, preservation declarations, and witness/proof lifts
    verify end to end.
14. For circuit projection, eliminate only exact definitional auxiliary
    variables and require SAT or UNSAT lift evidence against the original CNF.
