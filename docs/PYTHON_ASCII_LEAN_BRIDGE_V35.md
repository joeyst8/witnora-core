# Python-generated ASCII certificate bridge (v35)

Research PR #36 (draft), based on the kernel-reducible ASCII parser in PR #35.

## Verified result

The Python generator calls the existing DSATUR routines for four graph instances: triangle, four-vertex path, four-clique, and two disconnected triangles. It validates a proper coloring and matching-size clique, serializes the data as canonical ASCII `N|K|edges|colors|clique`, and emits the **actual byte values** as `List Nat` declarations in generated Lean source.

Lean parses those raw byte lists using the structurally recursive parser, verifies each certificate with the numeric checker, and derives exact chromatic optimality. A deliberate first-byte corruption of every generated certificate is also rejected. The CI workflow additionally tests deterministic Python output and malformed Python input, scans generated source for proof holes/native evaluation, and archives the generated Lean source.

The generated theorems `triangleAsciiOptimal`, `pathFourAsciiOptimal`, `cliqueFourAsciiOptimal`, and `twoTrianglesAsciiOptimal` each report only `[propext, Classical.choice, Quot.sound]`. None requires `Lean.ofReduceBool`. Dedicated CI passed: https://github.com/joeyst8/witnora-core/actions/runs/41237973312.

## Exact boundary

- This verifies the **literal bytes emitted into Lean source** for four instances, not a general theorem that all Python serialization runs are faithful.
- The input is generated Lean source, not a verified file-reading or arbitrary UTF-8-to-byte adapter.
- The clique lower bound must match the coloring upper bound; this does not solve general chromatic optimality for arbitrary graphs.
- The corruption check is one mutation per case, not exhaustive fuzzing.
- No TC-063, G5, or G14 theorem is established.

Next: independent randomized/adversarial batches, byte-for-byte cross-check against a separately implemented reference serializer, and a scalable kernel-checking workload. Then return to the core XOR-CNF/G5/G14 proof obligations.
