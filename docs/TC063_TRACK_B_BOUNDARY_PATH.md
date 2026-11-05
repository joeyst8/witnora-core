# TC-063 Track B: G5 provenance-boundary path discovery

Audit date: 2026-11-03 UTC. Draft PR #121, branch `formal/g14-python-seen-enqueue-v121`.

## Structural hypothesis and mechanism

For a binary affine equation `x_u ⊕ x_v = b`, view its two-variable support as the mod-2 vertex boundary of an undirected source edge `(u,v)`. If a derived G5 row is an XOR of original edge rows indexed by a provenance set `P`, its support equals the set of vertices incident to an **odd** number of selected edges:

`support(XOR_{e in P} row(e)) = ∂P`.

G5 indexed `ADD_ROW_XOR` updates both sides by symmetric difference. The new experimental `g5_boundary_path_signal.py` independently replays every operation, validates the reported before/source/after support, and tracks which original edge IDs contributed to every live row.

When the selected provenance edges form a simple path, their odd-degree boundary is *exactly the pair of path endpoints*. We rank those endpoint pairs by the smaller of the path interior size and the number of remaining vertices outside that path. This is only a **balance proxy** on a general graph. A path can exist inside a wheel or dense graph without its endpoints separating the source graph.

### A precise cycle-family consequence

If the original graph is a simple `n`-cycle, a provenance path with `k` internal vertices and at least one vertex on the complementary path gives a genuine two-vertex separator. Removing its endpoints leaves exactly two connected components of sizes `k` and `n−2−k`. Consequently, a generated path with `k` nearest `(n−2)/2` has optimal balance among all two-vertex deletions. This conditional graph-theoretic reasoning is distinct from a Lean proof that every Gaussian run will discover a balanced path.

## Empirical randomized study (CI verified)

`tests/test_g5_boundary_path_signal.py`: 48 deterministic, independently relabeled and equation-order randomized trials for each **unchorded** cycle size, with exact source-graph deletion components as oracle. Every proposed cycle path was independently checked to be an actual two-cut.

| Cycle vertices | Trials | Path hint finds cut | Path mean largest component | Single G5 activity | Pairwise cross-merge | Numeric baseline |
|---:|---:|---:|---:|---:|---:|---:|
| 8 | 48 | 48 | **3.000** | 4.438 | 4.479 | 4.708 |
| 16 | 48 | 48 | **7.000** | 10.104 | 11.812 | 10.875 |
| 32 | 48 | 48 | **15.000** | 22.250 | 27.750 | 21.458 |

The path-selected separator had better largest-component balance than the single-variable G5 activity top pair on respectively **41**, **45**, and **45** trials, was worse on **zero**, and tied on the remainder. In every trial it achieved the optimal possible largest-component size `(n−2)/2` for these even-length cycles. This is evidence for a strong **special-family** signal, not a random-graph generalization or a new complexity theorem.

### Adversarial no-cut controls

On 32 shuffled-label/equation-order trials each, the path detector proposed:

- Wheel8 graph: **402** provenance-path candidates; **0** actual two-vertex cuts.
- Cube8 graph: **385** provenance-path candidates; **0** actual two-vertex cuts.

These are intentional false positives and substantiate the fail-closed design: **path evidence alone never certifies a separator**. Every candidate must pass an independently verified source-graph / G14 cut check before use. The prototype reports `DIAGNOSTIC_ONLY`, and no solving status is promoted.

The new module validates G5 operation snapshots and rejects forged after-row supports; it does not prove full CPython refinement or universally certify a trace's provenance mathematically.

## Lean source-bound check (CI verified)

`scripts/generate_python_g5_path_two_cut_lean.py` generates signed XOR-CNF sources of sizes **8, 12 and 16** with deterministic mixed/large variable IDs. It runs the actual Python Gaussian eliminator and provenance-path heuristic, selects the top balanced candidate, and emits concrete Lean examples.

Lean independently:

1. decodes the signed source CNF and reconstructs its primal vertices and neighbors;
2. checks `TC063VertexCouplingFiniteOracle.twoCutFlag` for each G5-derived pair;
3. checks each cut yields exactly **two** residual components using verified G14 finite DFS;
4. checks the entire exact set of cuts for the 8-variable source using `checkSignedTwoCuts`.

All generated checks passed in the `G14 Python seen-at-enqueue refinement` workflow, job https://github.com/joeyst8/witnora-core/actions/runs/41595709377 (targeted G5-derived cut step; CI also ran a second PR attempt). These checks bind the candidates to **signed CNF source clauses**, not to original ASCII DIMACS document bytes, and test finitely many instances.

## Explicit trust boundary and next obligations

- The mod-2 boundary identity is a mathematical invariant and a **Lean theorem candidate**. It has not yet been universally formalized as a provenance-to-support theorem.
- The experiment achieves optimal balance on unchorded cycles but **does not generalize without a graph condition**. Wheel/cube controls are concrete counterexamples to unconditional path ⇒ cut.
- The heuristic is a ranking/scheduling idea, not a replacement for G14 exact graph checking or the TC-063 restricted-family soundness theorem.
- We have not demonstrated end-to-end solver speedups on held-out real SAT instances or shown robust optimality on chorded/dense graphs.

### Next Track B proof/experiment

1. In Lean, formalize `boundary(P △ Q) = boundary(P) △ boundary(Q)` for finite source-edge multisets and connect it to G5 indexed XOR operations.
2. Formalize a graph-level *certified path-boundary separator* with explicit absence-of-cross-edges / independently checked G14 residual conditions.
3. Stress on held-out chorded cycles, dense regular hidden bridges, and random regular graphs; compare G14 call counts and total wall time (including candidate generation and verification) to exact baseline search.
4. Promote to production ranking **only after** measurable held-out benefit and the existing exact G14 fallbacks remain intact.

This is experimental structural research. It is not a P-vs-NP breakthrough or a general polynomial-time SAT claim.
