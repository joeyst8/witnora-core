# Collapse Theory Lab

## v2.15 Graph Separator Lift

v2.15 adds `G8_GRAPH_SEPARATOR_LIFT_PROTOTYPE`, promoted from v2.14's
`GRAPH_SEPARATOR_OBSTRUCTION` recommendation.

G8 uses a primal graph model. It removes a small separator, verifies the
resulting components, conditions components on separator assignments, and emits
native certificates for SAT witness lift or UNSAT separator cover. Invalid
cross-component clauses and incomplete UNSAT covers are rejected.

This is a prototype and not a theorem, not DRAT, not a complete separator
solver, and not P vs NP progress.

## v2.14 Obstruction Dual Layer

v2.14 adds a diagnostic G7 layer for rows where the current G0-G6 ladder does
not emit a certified collapse. Instead of stopping at no-collapse, Witnora
builds an obstruction-dual certificate: grammar attempt trace, feature
evidence, obstruction fingerprint, proof obligations, and a recommended missing
operator family.

The certificate is bounded research evidence. It is not a satisfiability or
unsatisfiability result, not a hardness claim, not a lower-bound proof, and not
P vs NP progress.

## v2.8 Hierarchy Theoremization

v2.8 formalizes the current G0-G6 ladder as a bounded theoremization program.
It adds no new operator. It defines `W_B(G)`, records empirical strictness
evidence, emits theorem candidates, and lists proof obligations needed before
any strictness statement can become a theorem.

The full chain is `G0_BASE -> G1_XOR -> G2_SYMMETRY_CERTIFIED ->
G3_SYMMETRY_CARDINALITY_CERTIFIED ->
G4_ORBIT_CAPACITY_COUNTING_PROTOTYPE ->
G5_HIGH_ARITY_AFFINE_RESIDUE_PROTOTYPE ->
G6_PROOF_MOTIF_COMPRESSION_PROTOTYPE`.

v2.8 does not prove P vs NP, hierarchy completeness, lower bounds, or proven
strictness. Native certificates remain native certificates, not DRAT, unless
explicitly exported and checked.

Witnora-Core v2.0 adds a research lab for comparing bounded collapse
grammars. It is not a product feature and it is not a new SAT-solver claim.

## Purpose

The lab studies this question:

Given a CNF verifier instance, when can a deterministic, replayable grammar
discover a collapse path to a witness or proof?

## Core Objects

- Collapse Grammar G: a finite set of deterministic transformations and
  terminal classes.
- Bound Profile B: explicit caps on width, XOR arity, runtime, proof size,
  search nodes, operator depth, and symmetry diagnostics.
- Bounded Collapse Class W_B(G): formulas that collapse under grammar G within
  bound profile B and emit a valid certificate/proof when required.
- Strictness Witness: bounded evidence that one grammar fails under the
  configured bound while an extended grammar succeeds with certificate-backed
  evidence.
- Operator Delta: the changed public outcomes between G and G plus an operator.
- Collapse Cost: recorded path length, operator counts, peak formula sizes,
  proof size, runtime, certificate size, and bound status.

## Current Profiles

- `G0_BASE`: UP, PLE, SUB, BCE, VE, components, 2SAT, bounded treewidth.
- `G1_XOR`: `G0_BASE` plus exact CNF XOR extraction and sparse/min-fill XOR
  elimination.
- `G2_SYMMETRY_CERTIFIED`: `G1_XOR` plus exact automorphism validation, native
  symmetry certificates, SBP preservation obligations, and SAT witness
  reconstruction for supported small formulas.
- `G2_HORN_PROTOTYPE`: honest stub.
- `G3_CARDINALITY_PROTOTYPE`: honest stub.
- `G3_CARDINALITY_PB_PROTOTYPE`: exact cardinality/PB structure diagnostics
  only; no PB solving claim.
- `G3_SYMMETRY_CARDINALITY_CERTIFIED`: `G2_SYMMETRY_CERTIFIED` plus exact
  assignment-grid cardinality/PB recognition and native pigeonhole counting
  certificates for standard `php_n_m` encodings.
- `G4_ORBIT_CAPACITY_COUNTING_PROTOTYPE`: exact local Hall/capacity-deficit
  certificates over generated assignment/resource CNFs. This is native
  counting evidence, not a complete matching/allocation solver.
- `G5_HIGH_ARITY_AFFINE_RESIDUE_PROTOTYPE`: exact high-arity GF(2) affine
  extraction from full forbidden-assignment CNF encodings plus native
  Gaussian-elimination certificates. This is not heuristic XOR mining,
  CryptoMiniSat-style extraction, broad modular arithmetic solving, or DRAT.
- `G6_PROOF_MOTIF_COMPRESSION_PROTOTYPE`: repeated native proof motif
  detection, template verification, reuse instantiation checking, and
  compressed macro-proof certificates. This is not DRAT and not a
  proof-compression completeness claim.
- `G4_BACKDOOR_DIAGNOSTIC`: honest stub.
- `G2_SYMMETRY_PROTOTYPE`: `G1_XOR` plus deterministic syntactic orbit
  diagnostics. This is not full automorphism detection and does not certify
  orbit quotient collapse.

## v2.1 Frontier Layer

v2.1 turns no-collapse rows into structured obstruction records. It asks:

- Which bound was exceeded or which operator was not applicable?
- Which structural signal appears in the failed row?
- Which next operator would make the obstruction certifiable if implemented?

Current obstruction records are bounded diagnostics, not lower-bound theorems.
Current non-collapse is bounded non-collapse under configured grammar/resource
bounds, not a proof that no method can solve the instance.

## v2.2 Certified Symmetry Layer

v2.2 adds `run-symmetry-lab` and `check-symmetry-cert`. The lab validates exact
automorphism generators, recomputes orbits, records SBP obligations, and checks
direct SAT witness reconstruction for supported toy and graph-coloring rows.

The critical soundness rule is that symmetry-breaking predicates are not
treated as clauses implied by the original formula. They are accepted only with
a preservation argument such as orbit-representative existence and with direct
witness verification for SAT rows. For UNSAT, `F and SBP` being UNSAT is not
enough to conclude `F` is UNSAT unless the preservation obligations are
present, and DRAT remains a separate original-CNF proof requirement.

## v2.3 Pigeonhole Native Counting

v2.3 recognizes standard pigeonhole CNFs using assignment variables
`x[pigeon,hole]`. It checks that each pigeon has an original-CNF ALO clause over
all holes and that each hole has all original-CNF pairwise AMO clauses over all
pigeon pairs. When `n > m`, the native certificate records the counting
contradiction: `n` pigeons require at least `n` occupied assignments while `m`
holes accept at most `m` pigeons.

This is native semantic certification. It is not DRAT, not PB solving, and not
a proof-complexity lower bound.

## v2.4 Operator Genesis

v2.4 adds an Operator Genesis Engine. Instead of naming the next operator by
hand, the lab now extracts obstruction fingerprints from selected failed or
non-collapsed rows and generates candidate operator schemas.

Generated candidates record trigger signatures, intended transformations,
certificate obligations, safety risks, promotion criteria, novelty scores,
evidence scores, and risk scores. They remain `GENERATED_CANDIDATE` records
unless a future release implements and verifies them.

This layer is a theorem-discovery and operator-planning tool. It is not a solver
extension and does not claim that generated operators are implemented,
certified, or theorem-proven.

## v2.5 Orbit Capacity Counting

v2.5 implements the first generated-operator prototype:
`G4_ORBIT_CAPACITY_COUNTING_PROTOTYPE`. It targets local Hall/capacity deficits
in exact assignment/resource CNFs. The native certificate records a demand
subset `S`, its allowed neighborhood `N(S)`, exact source clauses, resource
capacities, and the inequality `|S| > capacity(N(S))`.

Orbit summaries may compress the display, but the checker trusts the result
only after expanding the evidence back to concrete items, resources, and source
clauses. Complete matching rows that duplicate standard pigeonhole are recorded
as duplicate controls, not as novel G4 evidence.

## v2.6 High-Arity Affine Residue

v2.6 implements the second generated-operator prototype:
`G5_HIGH_ARITY_AFFINE_RESIDUE_PROTOTYPE`. It promotes the v2.4
`MODULAR_RESIDUE_COLLAPSE` candidate into a bounded native checker for exact
GF(2) affine equations whose arity exceeds the lower G1 extraction cap.

The extractor accepts only complete forbidden-assignment CNF encodings of
equations. It rejects incomplete, polluted, wrong-parity, and over-cap controls
or leaves them diagnostic-only. The certificate records deterministic GF(2)
Gaussian elimination using `SWAP_ROWS` and `ADD_ROW_XOR`; there is no
nontrivial row scaling over GF(2).

This is a native affine certificate, not a DRAT proof, not broad modular
arithmetic solving, and not a G5 strictness theorem.

## v2.7 Proof Motif Compression

v2.7 implements the third generated-operator prototype:
`G6_PROOF_MOTIF_COMPRESSION_PROTOTYPE`. It promotes the v2.4
`PROOF_MOTIF_COMPRESSION` candidate into a native macro-proof checker for
repeated local proof motifs.

The checker trusts a reuse only after verifying the template proof, the
substitution map, original source clause IDs, deterministic instantiated proof
hash, derived lemma, and final contradiction. Optional Tseitin rows are not
counted as G6 deltas if earlier XOR grammars can already collapse them.

This is native proof-structure evidence, not DRAT, not proof-compression
completeness, and not a G6 strictness theorem.

## Claim Boundary

Allowed claim:

Witnora v2.0 formalizes collapse grammar comparisons and demonstrates bounded
strictness examples where adding exact XOR reasoning changes selected formula
families from no-collapse to certified collapse.

Forbidden claims:

- no P vs NP progress claim
- no general SAT solving claim
- no broad XOR extraction claim
- no competitive SAT solver claim
- no lower bound against all algorithms
- no complete collapse grammar claim
- no certified symmetry-collapse claim for pigeonhole unless a future release
  implements and verifies such a transformation
