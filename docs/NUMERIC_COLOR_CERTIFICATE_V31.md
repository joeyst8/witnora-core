# v31 numeric graph-coloring certificate adapter in Lean

**Status:** Lean 4.19.0 kernel-checked and `sorry`-free, with executable accept/reject cases and proved in-range value preservation. This is an **in-memory Nat-array adapter**, not a verified external text parser or a universal Python refinement theorem.

## Input and checks

The module `formal/Witnora/NumericColorCertificate.lean` accepts ordinary numbers:

- `edges : List (Nat × Nat)` — endpoints as natural numbers;
- `colors : List Nat` — palette labels;
- `clique : List Nat` — claimed clique vertex IDs;
- a positive vertex count `N+1` and positive palette size `K+1`.

The executable `numericRangesValid` check rejects:

1. Wrong color list length.
2. Wrong clique list length.
3. Any color ID outside `0..K`.
4. Any vertex ID outside `0..N`, including both edge endpoints and clique entries.

Values are decoded into finite indexed witnesses and sent to the v29 concrete checker, which independently rejects self-loops, improper colorings, repeated clique vertices and missing clique edges. The decode functions use total modulo representations internally but **cannot accept out-of-range input** because the raw range validation must pass first.

## Kernel results

- `checked_numeric_sound`: if the concrete numeric checker returns true, then the decoded finite graph's chromatic number equals `K+1`.
- `decodeEdge_preserves`: valid endpoint pairs decode with exactly the original values.
- `decodedPaint_preserves`: an in-range color array value is unchanged in the finite palette.
- `decodedClique_preserves`: an in-range clique array value is unchanged in the finite graph.
- `numeric_triangle_passes` and `numeric_triangle_optimal`: the numeric triangle is accepted and its chromatic number 3 is proved.
- Rejecting test theorems for an out-of-range edge endpoint, an out-of-range color, a missing clique item, and repeated clique vertices.

The dedicated GitHub CI workflow `.github/workflows/numeric-color-certificate.yml` builds the module and rejects explicit `sorry`, `axiom`, and `unsafe` declarations. The checker and value-preservation lemmas passed this gate.

## Trust boundaries

The soundness theorem currently states exact optimality for `decodedEdges N edges`. We have proved local in-range decode preservation but have **not yet** proved a universal list-level correspondence between arbitrary accepted raw edges and their decoded graph. The next task is to close this correspondence and make the accepted numeric format the target of the Python exporter.

No byte/string parser, signed-integer serializer, general Python-to-Lean correctness proof, or TC-063 XOR-CNF/G5/G14 bridge is claimed here.

## Reproduce

`cd formal`

`lake build Witnora.NumericColorCertificate`
