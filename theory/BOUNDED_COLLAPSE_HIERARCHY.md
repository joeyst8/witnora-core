# Bounded Collapse Hierarchy

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

This work does not prove P vs NP.

