# Collapse Hierarchy Theoremization

## v2.13 Reviewer-Defense Layer

v2.13 does not add a new operator or promote any hierarchy edge. It hardens the
external paper with related work, contribution and objection tables,
limitations, a claim-boundary appendix, and reviewer inspection guidance.

Evidence grades remain unchanged: v2.10 is the finite restricted strictness
certificate, v2.11 is the finite empirical edge-delta certificate, and the
remaining hierarchy edges stay empirical or proof-obligation scoped unless a
separate certificate discharges stronger obligations.

## v2.12 External Reproducibility Package

v2.12 packages the hierarchy work for external review. It adds a polished
external paper draft, reproducibility manifest, release SHA manifest, evidence
summary, claim-boundary table, reproduction steps, validation script, and
review packet.

v2.12 does not add a new operator. It does not prove P vs NP, does not claim a
polynomial-time SAT algorithm, does not claim hierarchy completeness, and does
not convert empirical edge deltas into strictness theorems.

## v2.9 Restricted Proof Kernel

v2.9 starts the first formal strictness proof attempt. It targets only
`G0_WIDTH_C` against `G1_XOR_FOR_STRICTNESS`: the bounded-width/treewidth route
is rejected by exact finite width obstruction, while the G1 XOR route is
accepted by checked native GF(2) evidence.

The theorem is restricted to the width/treewidth subroute. Full `G0_BASE`
strictness is not claimed. Scalable expander/Tseitin strictness remains a proof
obligation unless a real graph-theoretic proof is supplied.

## v2.10 Finite Strictness Certificate

v2.10 turns the restricted proof kernel into a reusable finite certificate
format. `FINITE_STRICTNESS_CERTIFIED` means the checked finite instances replay
successfully under `G0_WIDTH_C` width obstruction and `G1_XOR_FOR_STRICTNESS`
XOR acceptance.

It is not a scalable family theorem, not full `G0_BASE` strictness, not a
hierarchy strictness theorem, and not P vs NP progress.

## v2.11 Finite Empirical Edge Delta Certificate

v2.11 extends the finite-certificate framework to `G1_XOR ->
G2_SYMMETRY_CERTIFIED` without calling replay-only evidence strictness.

The lower side is bounded replay evidence:
`LOWER_REPLAY_NO_COLLAPSE`. It is not a lower-bound proof. The upper side is a
checked G2 symmetry SAT witness reconstruction. The evidence grade is
`FINITE_EMPIRICAL_EDGE_DELTA_CERTIFIED`, not `FINITE_STRICTNESS_CERTIFIED`.

This does not prove a G1-vs-G2 family theorem, hierarchy completeness, or P vs
NP progress.

v2.8 formalizes the current Witnora hierarchy without adding a new operator.
It turns the G0-G6 ladder into a theoremization artifact: bounded definitions,
empirical strictness evidence, theorem candidates, proof obligations, evidence
bundles, and gap analysis.

## Full Hierarchy

- `G0_BASE`: UP, PLE, SUB, BCE, VE, component decomposition, 2SAT, bounded treewidth.
- `G1_XOR`: G0 plus exact XOR extraction and sparse/min-fill XOR elimination.
- `G2_SYMMETRY_CERTIFIED`: G1 plus exact automorphism validation, orbit certificates, and SAT witness reconstruction.
- `G3_SYMMETRY_CARDINALITY_CERTIFIED`: G2 plus exact AMO/ALO detection and native standard pigeonhole certificates.
- `G4_ORBIT_CAPACITY_COUNTING_PROTOTYPE`: G3 plus local Hall/capacity-deficit native certificates.
- `G5_HIGH_ARITY_AFFINE_RESIDUE_PROTOTYPE`: G4 plus exact high-arity GF(2) full-CNF extraction and native elimination certificates.
- `G6_PROOF_MOTIF_COMPRESSION_PROTOTYPE`: G5 plus verified native macro-proof motif certificates.

## Bounded Collapse Class

`W_B(G)` is operational and bounded. A formula is in `W_B(G)` when Witnora,
under bound profile `B` and grammar `G`, emits a SAT witness verified against
the original CNF, an externally checked UNSAT proof, or an accepted native
certificate whose checker succeeds within the configured resource bounds.

Current non-collapse is bounded non-collapse under configured grammar/resource
bounds. It is not a proof of hardness or a lower bound against all algorithms.

## Theoremization Boundary

v2.8 does not prove strictness. It records empirical strictness evidence and the
proof obligations required to promote a candidate into a theorem.

Required proof obligations include prior-grammar non-collapse, new-grammar
certification, checker soundness, bound-profile well-definedness, cost-model
completeness, witness-family scaling, and lower-bound work where applicable.

## Non-Claims

v2.8 does not prove P vs NP.
v2.8 does not add a new operator.
v2.8 does not prove hierarchy completeness.
v2.8 does not prove strictness for any edge.
Native certificates are not DRAT unless explicitly exported and checked.
