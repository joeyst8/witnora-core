# Adversarial ASCII certificate experiment (v36)

Draft PR #37 extends the Python-to-Lean byte verification research.

## CI results

GitHub Actions run: https://github.com/joeyst8/witnora-core/actions/runs/41238162695

- 200 deterministic seeded complete-multipartite graph cases passed independent field-by-field Python ASCII serialization comparison with the production emitter.
- Each randomized case generates seven distinct byte mutations; the Python test currently verifies that the mutations differ from the original, **not** that a parser rejects each one.
- Eight concrete certificates generated from actual Python DSATUR results were parsed and proved optimal in Lean: triangle, pathFour, cliqueFour, twoTriangles, starFive, threePartSix, bipartiteSix, cliqueAndIsolates.
- Lean also rejected one deliberately damaged byte stream per certificate (first digit replaced with non-digit ASCII `x`).
- Every generated optimality theorem's axiom audit: `[propext, Classical.choice, Quot.sound]`; no native evaluation / `Lean.ofReduceBool`.
- Timed Lean invocation: **2.55 seconds**, reported peak resident memory **982,568 KiB** on the GitHub runner. A single CI run on these small examples is not a scaling law or comparative benchmark.

## Interpretation

The second serialization implementation reduces the risk of a shared accidental formatting bug, but uses the same arithmetic conventions. The 200 Python cases do not establish a universal correctness theorem. The eight Lean proofs independently validate those precise emitted byte lists. There remains no universal formal theorem relating arbitrary Python file bytes to Lean input lists.

## Next

1. Independently parse and assert rejection of **all** mutation families, including semantic mutations, before claiming adversarial coverage.
2. Characterize verifier time and memory across multiple controlled input sizes and repetitions.
3. Return the parser/certificate machinery to the core Witnora XOR-CNF, indexed G5/G14, and TC-063 proof obligations rather than conflating graph-coloring examples with the original target.
