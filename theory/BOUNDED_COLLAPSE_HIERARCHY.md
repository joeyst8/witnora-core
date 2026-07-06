# Bounded Collapse Hierarchy

## v2.9 Restricted Edge

v2.9 introduces a restricted theorem kernel for the edge
`G0_WIDTH_C -> G1_XOR_FOR_STRICTNESS`. This is not a full `G0_BASE` theorem.
It is a bounded statement about the width/treewidth subroute under cap `c` and
the exact XOR route that extends it.

The bounded hierarchy uses `W_B(G)` rather than an absolute `W(G)` claim.

`W_B(G)` is the set of formulas for which Witnora can produce, under bound
profile `B` and grammar `G`, one of the following checked outcomes:

- a SAT witness verified against the original CNF;
- an UNSAT proof verified by the appropriate external checker;
- an accepted native certificate whose independent checker succeeds.

The definition is operational. It depends on the configured bound profile,
including runtime, width, treewidth cap, XOR arity cap, affine arity cap,
certificate size, proof size, operator depth, search nodes, motif reuse sites,
and Hall subset size.

The hierarchy currently formalized is:

`G0_BASE -> G1_XOR -> G2_SYMMETRY_CERTIFIED -> G3_SYMMETRY_CARDINALITY_CERTIFIED -> G4_ORBIT_CAPACITY_COUNTING_PROTOTYPE -> G5_HIGH_ARITY_AFFINE_RESIDUE_PROTOTYPE -> G6_PROOF_MOTIF_COMPRESSION_PROTOTYPE`

Strictness along this chain is empirical evidence unless a formal proof is
supplied and checked. v2.8 supplies proof obligations, not final lower bounds.

v2.11 introduces a finite empirical edge-delta certificate for
`G1_XOR -> G2_SYMMETRY_CERTIFIED`. Its lower side is
`LOWER_REPLAY_NO_COLLAPSE`, not a lower-bound proof, so the evidence grade is
`FINITE_EMPIRICAL_EDGE_DELTA_CERTIFIED`. This is distinct from v2.10's
`FINITE_STRICTNESS_CERTIFIED`, which relies on certified width obstruction.

This work does not prove P vs NP.
