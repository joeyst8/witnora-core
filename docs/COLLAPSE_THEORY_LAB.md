# Collapse Theory Lab

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
