# v28 Lean optimal-coloring certificates

**Status:** Lean 4.19.0 kernel-checked and sorry-free for generic finite simple graphs; **not** a verified Python-to-Lean bridge, a DSATUR correctness theorem, or a novel graph-theoretic result.

## Main result

The new module `formal/Witnora/ColoringOptimalityCertificate.lean` packages existing finite-graph mathematics into explicit, reusable witness theorems.

Given a finite loopless adjacency relation `Adj : Fin N → Fin N → Prop`:

1. A concrete function `paint : Fin N → Fin k` satisfying the proper-coloring condition on every edge certifies **chi(G) <= k**.
2. A concrete injective map `vertices : Option (Fin k) → Fin N` of `k+1` pairwise adjacent vertices certifies **k+1 <= chi(G)**.
3. A proper `(k+1)`-coloring and an explicit clique of matching size together prove **chi(G) = k+1**.
4. An explicit zero-palette coloring certifies **chi(G) = 0**, handling the empty graph separately.

There is no need to assume the numerical clique number, chromatic number, or extremal inequality as a hypothesis: existing `ChromaticMinimum`, `CliqueMaximum`, and `GraphMaxEquality` definitions discharge those obligations.

The theorem accepts the *mathematical properties* of the supplied witness maps as proofs. It does not itself parse external graphs or algorithm output; verifying the witnesses from actual text/array data is a separate engineering and formal-refinement task.

## Kernel and axiom audit

Dedicated GitHub Actions workflow `.github/workflows/color-optimality-lean.yml` passed:

- `lake build Witnora.ColoringOptimalityCertificate`: all 19 dependent modules built successfully.
- No explicit `sorry`, `axiom`, or `unsafe` declarations in the new file.
- `#print axioms` for all four results reported only `[propext, Classical.choice, Quot.sound]`.

These are standard Lean foundational axioms, not hidden graph-theorem assumptions. Existing imported modules produced a couple of harmless unused-variable warnings, unrelated to proof correctness.

## How this changes Witnora

The exploratory Python graph-coloring pipeline can now aim at a specific certificate format: graph adjacency, an explicit proper k-coloring, and a matching-size clique. Lean proves mathematically that **if those concrete maps are validated against the same graph**, no smaller coloring exists.

This is a graph-coloring trust milestone. It does **not** close the original TC-063 XOR-CNF extraction, shared-row indexed UNSAT certificate, G5/G14 bridges, or Python refinement obligations.

## Next formal work

1. Introduce a deterministic finite graph/witness input representation and check the maps/adjacency claims computationally.
2. Prove the parser/serialization representation agrees with the abstract `Fin N` adjacency relation.
3. Generate certificates for actual Python outputs and run them through the Lean checker.
4. Then consider a Lean DSATUR bipartite-optimality invariant, which is independent of the matching-coloring certificate itself.

## Reproduce

`cd formal`

`lake build Witnora.ColoringOptimalityCertificate`

The module prints its axiom dependencies at build time.
