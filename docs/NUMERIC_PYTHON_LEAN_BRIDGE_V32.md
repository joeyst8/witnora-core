# Numeric Python-to-Lean Bridge (v32)

Research status: draft PR #33; not merged.

## What was checked

The Python generator computes DSATUR colorings for four concrete graph cases (triangle, four-vertex path, four-clique, two disconnected triangles) and emits Lean source containing **raw natural-number** edge endpoints, color assignments, and clique vertices. Lean's `checkNumeric` verifies the inputs, and `checked_numeric_sound` derives the exact chromatic-optimum claims for these cases. GitHub Actions runs the Python unit tests, generates the Lean source, kernel-checks it, scans the new bridge for `sorry`/`axiom`/`unsafe`, and archives the generated source.

`NumericEdgeListBridge.lean` additionally proves `decodedEdges_preserve_list`: when every endpoint satisfies the range check, decoding the **whole ordered edge list** equals mapping each numeric edge to its bounded `Fin` representation. This includes duplicate edges, preserves order, and prevents a successful range check from silently filtering edges away. The theorem is conditional on `edgeBoundsValid = true`.

Workflow run: https://github.com/joeyst8/witnora-core/actions/runs/41236792668 (all job steps successful).

## What this does not establish

- No parser or proof yet connects arbitrary externally supplied text/bytes to these Lean values.
- No universal theorem proves the Python implementation correct for all inputs; each emitted concrete case is checked independently by Lean.
- The optimality certificates use a proper coloring and a matching-size clique, so they only cover graphs for which such a certificate is provided.
- This is not a proof of the original TC-063, G5, or G14 targets.
- The branch remains experimental and is not a released or merged result.

## Next falsifiable milestone

Define a canonical numeric serialization format, parse it inside Lean, prove parser/decoder correspondence, and test both valid cases and adversarial malformed cases. Then broaden independently checked graph instances beyond the four fixtures.
