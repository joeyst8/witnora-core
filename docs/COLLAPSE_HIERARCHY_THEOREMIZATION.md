# Collapse Hierarchy Theoremization

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
