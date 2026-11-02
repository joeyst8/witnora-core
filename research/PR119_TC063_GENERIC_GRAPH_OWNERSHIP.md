# PR #119: generic TC-063 G14 graph-to-residual ownership

Status: `LEAN_KERNEL_CHECKED_CONDITIONAL_GENERIC_GRAPH_OWNERSHIP`.

Verified with pinned Lean 4.35.0 at
[GitHub Actions run #41493331576](https://github.com/joeyst8/witnora-core/actions/runs/41493331576),
commit `7d2d639edfe96e517d1a4c8469ae961c6a449cb4`.
All three Dubois20 Lean proofs and their nine fixture tests passed again; the
imported generic `SeparatorAgreement` foundation and the new generic graph
ownership theorem compiled successfully. Lean reports the final graph-ownership
theorem uses only standard axioms `[propext, Quot.sound]`, with **no `sorryAx`**.

The preceding verified Dubois20 two-component result had a remaining trust
gap: Python checked the graph separator and component ownership, whereas Lean
checked concrete clause partition, per-component G5 consequences and UNSAT
cover. This experiment targets the **general graph-to-clause localization
implication** and reuses the previously proved executable reducer.

`theory/TC063PrimalGraphOwnership.lean` imports
`theory/SeparatorAgreement.lean` and defines:

- `CoOccurs`: exact primal-graph adjacency when two variables appear in a
  common original source clause.
- `NoCrossEdges`: a graph cut invariant forbidding an edge between variables
  labeled as different components.
- `AllUnassignedOwned`: every variable not fixed by the separator assignment
  is classified into a component.
- `ResidualOwner`: deterministic owner of a nonempty clause based on its
  first surviving literal.

Theorems prove for **any** variable type, original list CNF, partial
assignment and two-way ownership satisfying those explicit premises:

1. Every reduced literal comes from the original clause and is unassigned.
2. No two reduced-clause literals can belong to different components.
3. Every nonempty reduced clause has a unique owner consistent with **all**
   of its literals.
4. Every reduced clause is either an **empty** contradiction clause or
   classified into a component. Empty contradictions are not discarded.
5. An empty reduced clause implies residual CNF UNSAT for all models.
6. If no empty residual clause exists, all residual clauses are covered by
   the two component partitions already used by the G14 SAT-lifting theorem.

## Explicit remaining obligations

- `NoCrossEdges` is a **premise**, not independently derived from the actual
  Python primal-graph builder or a verified connected-component computation.
- `AllUnassignedOwned` is a **premise**, not yet proved of the Python
  separator/component labeling pipeline.
- The existing verified `ReduceCNF` semantics are reused, but actual Python
  implementation refinement and source DIMACS parsing remain unproved.
- The theorem provides a general **soundness bridge**, not universal
  recognition completeness, affine extraction, G5 certificate validation,
  arbitrary component-count composition, or the full TC-063 complexity bound.

Next objective: kernel-check the concrete Dubois20 source-clause graph and
29/29 labeling against these general premises, then formalize the recognizer
and Python-to-Lean refinement boundary. Keep the production theorem's status
restricted until all pieces are connected.
