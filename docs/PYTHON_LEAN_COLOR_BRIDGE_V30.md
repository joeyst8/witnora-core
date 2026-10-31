# v30 Python-generated Lean graph-coloring certificates

**Status:** end-to-end sample integration **kernel-checked**. Python exporter is not itself formally refined into Lean; this is not a proof for arbitrary Python executions or the original TC-063 SAT pipeline.

## Verified data path

The v29 theorem accepted concrete `Fin`-indexed Lean data. This branch introduces a deterministic Python exporter and a CI job that actually runs it:

1. Python's existing deterministic `_dsatur_greedy_coloring` computes a proper coloring for each fixed graph.
2. Python independently finds the lexicographically first clique matching the number of used colors.
3. The exporter checks normalized edge order, vertex ranges, contiguous color IDs, proper coloring, unique clique vertices and pairwise clique edges.
4. The exporter emits a complete Lean source module with concrete edge list, coloring function, clique function, a `by decide` success theorem, and a soundness theorem application yielding exact chromatic number.
5. GitHub CI compiles the trusted `ConcreteColorCertificate` checker and then executes `lake env lean` on the **generated** file. The Lean kernel validates the complete proof, rather than merely accepting the Python preflight.
6. The exact generated source is uploaded as a workflow artifact for human audit.

## Successful concrete instances

| Python graph | Chromatic number proved by Lean | Matching clique |
| --- | ---: | ---: |
| Triangle (3 vertices) | 3 | 3 |
| Path on 4 vertices | 2 | 2 |
| Complete graph on 4 vertices | 4 | 4 |
| Two disconnected triangles (6 vertices) | 3 | 3 |

The first CI run built the trusted checker and successfully checked all four generated proofs; `#print axioms` on each reported only `[propext, Classical.choice, Quot.sound]`. No `sorry` was introduced.

The Python emitter is deterministic and guarded by unit tests that reject malformed normalized edges, improper colorings, invalid clique choices, and invalid Lean identifiers.

## Precisely what is and is not trusted

- **Lean checks the actual generated certificate data.** The exporter cannot make an invalid coloring/clique optimal by merely declaring it: the finite Boolean checker must reduce to true and its soundness proof is kernel-checked.
- **Only certifiable cases are supported.** A graph can be optimally colored without containing a clique of equal size (for example a 5-cycle with chi 3 and omega 2). Such a case currently needs a different lower-bound certificate.
- **No fully verified serialization/parser theorem yet.** The Python script emits Lean text, and the Lean compiler parses it; the correspondence between all possible Python internal data and emitted Lean syntax is tested, not universally proved.
- **No production release trust claim.** This research branch is separate from the original TC-063 XOR-CNF/G5/G14 UNSAT obligations.

## Reproduce

`PYTHONPATH=. python -m unittest tests.test_lean_color_certificate_export -v`

`PYTHONPATH=. python scripts/generate_lean_color_certificates.py`

`cd formal`

`lake build Witnora.ConcreteColorCertificate`

`lake env lean Witnora/GeneratedColorCertificates.lean`

The CI workflow `.github/workflows/python-lean-color-bridge.yml` uploads `GeneratedColorCertificates.lean`.

## Next gate

Make the certificate format more directly data-oriented: normalize integer arrays with a checked decoder into `Fin N`, reject out-of-range entries inside Lean, and prove decoding correctness. Then enlarge the randomly generated certificate sample without relying on Python to preselect only trusted values. For non-clique-tight graphs, design a separate lower-bound witness (e.g. exhaustive small-instance non-k-colorability proof) rather than stretching the clique certificate beyond its mathematical scope.
