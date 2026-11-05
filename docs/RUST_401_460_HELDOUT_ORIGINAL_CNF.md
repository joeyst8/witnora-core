# R-401–R-460: heldout nonlinear CNF, components and independent rank

The bounded Python research prototype extends mixed-arity XOR experiments with
**13 planted non-XOR CNF clauses** (some sharing XOR variables; others including
fresh variables) and with one to three disconnected parity components. SAT
controls retain an independently enumerated satisfying assignment. UNSAT cases
require both an odd GF(2) source-row dependency and an independently checked
DRAT proof over the **unchanged full original CNF** (background clauses included).

The independent bit-matrix Gaussian elimination reference computes coefficient
rank and augmented rank from source equations, without calling the syndrome DP.
Its augmented rank predicts the exact number of reachable syndrome states,
`2 ** augmented_rank`. Both algorithms must agree on consistency, but this
identity does not imply that a large-state DP search is efficient.

R-401–R-420: SAT and UNSAT nonlinear background, original-source integrity,
fresh/overlapping clauses and seeded replay.

R-421–R-440: SAT/UNSAT disjoint components, location of the first odd dependency,
three-component caps, source disjointness and seeded replay.

R-441–R-460: independent Gaussian coefficient/augmented rank, contradictory
zero rows, duplicate/opposing rows, signed triangles, permutations, seed replay,
variable caps and reachable-state cross-checks.

Reproduce locally:

```sh
WITNORA_DRAT_TRIM=/path/to/pinned/drat-trim python -m unittest tests.test_xor_heldout_401_460 -v
python -m scripts.benchmark_xor_heldout_401_460 --samples 16 --drat-trim /path/to/pinned/drat-trim
```

GitHub CI additionally runs the exact same families through native Rust
candidate generation and compares proof, error and statistics exactly.
Results are finite diagnostics, **not** P-vs-NP or general SAT results.
