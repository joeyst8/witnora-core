# v29 executable finite-edge-list graph coloring certificate

**Status:** Lean 4.19.0 kernel-checked, executable finite Boolean checks, soundness proved without `sorry`. Not yet a parser or Python-to-Lean refinement.

## What changed relative to v28

v28 proved that matching **abstract** proper-coloring and clique witnesses establish exact chromatic optimality. v29 introduces a **computable Boolean checker** on concrete finite graph data:

- `edges : List (Fin N × Fin N)` — a finite list of undirected edges; adjacency is the disjunction of forward/reversed pair membership.
- `paint : Fin N → Fin (k+1)` — explicit proposed palette assignment.
- `vertices : Option (Fin k) → Fin N` — explicit proposed enumeration of k+1 clique vertices.

The checker recursively evaluates all elements of `Fin N` and `Option (Fin k)`. It validates:

1. No self-loops in the concrete graph.
2. Different colors on every edge.
3. Clique enumeration injectivity.
4. Pairwise adjacency of all distinct clique vertices.

Lean proves:
```
checkCertificate edges paint vertices = true
  -> exists hNoLoops,
       chromaticNumber (edgeAdj edges) hNoLoops = k + 1
```

The Boolean verifier's quantifier loops are **structurally recursive**. The soundness proof translates each successful finite check into the abstract witness conditions, then applies the v28 optimality theorem.

## Executable test instances

- A concrete three-vertex triangle, edges `(0,1), (0,2), (1,2)`, distinct colors `0,1,2` and all three vertices as a clique: the checker reduces to `true` using `by decide`, and Lean derives exact chromatic number 3.
- Additional explicit negative cases verify rejection of: all vertices painted the same color; a clique enumeration with repeated vertices; and a self-loop in the edge list.

## Verification and axiom audit

Dedicated workflow `.github/workflows/concrete-color-certificate.yml` performs `lake build Witnora.ConcreteColorCertificate` and rejects explicit `sorry`, `axiom`, or `unsafe` declarations. It passed on the soundness theorem and triangle certificate; the new negative tests are included in the same gate.

`#print axioms` showed:

- `checked_certificate_sound`: `[propext, Classical.choice, Quot.sound]`.
- `triangle_certificate_passes`: `[propext]`.
- `triangle_chromatic_exact`: `[propext, Classical.choice, Quot.sound]`.

These are Lean's foundational axioms, not extra graph-specific assumptions.

## Boundaries

The edge list and maps are **concrete Lean data**, but there is **not yet** a byte-level text format, a verified parser, or a proof that Python's emitted numeric arrays correspond to the `Fin` values and adjacency relation. In particular, a successful checker on hand-authored Lean data is not by itself a verified Python pipeline.

The next milestone is deterministic signed/natural integer serialization into Lean expressions plus a checked parser or certified value adapter. Integration with the original TC-063 XOR-CNF/G5/G14 work remains separate and incomplete.

## Reproduce

`cd formal`

`lake build Witnora.ConcreteColorCertificate`
