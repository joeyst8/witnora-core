# W-CRC-002: dense and mixed nonlinear falsification pilot

Status: experimental, stacked on draft PR #122 (`research/w-crc-001-asymmetric-v1`). This experiment tests the *limitations* of W-CRC-001 rather than claiming a new operator.

## Exact question

Does Witnora's exact asymmetric affine/Walsh boundary contraction improve
*total* computation over its existing source-to-ANF counter once nonlinear
constraints overlap strongly on a large boundary?

Pure XOR success and disjoint-OR speedups are already explained by known
algebraic/decomposition structure. Neither is evidence of a breakthrough.

## Reproducible benchmark

Run `python -m pip install python-sat` followed by
`python -m scripts.benchmark_crc_scaling`.

- Two families: `dense_random_3cnf` (no forced affine structure) and
  `mixed_xor_dense_3cnf` (a complete canonical XOR-CNF chain encoding
  one global even-parity constraint, coupled to ~4.2k random nonlinear
  3-clauses on its k shared boundary variables).
- Boundary sizes 16, 20, 24; three deterministic seeds per size and family:
  18 instances. Source-variable counts in the mixed family: 30, 38, 46.
- Three internal exact variants: original bounded inclusion-exclusion
  CRC, opt-in bounded Shannon CRC, and original structured ANF.
- External PySAT Glucose3: separate SAT decision and **all-model
  enumeration** when <=1000 models. Model enumeration is an independent
  small-case count cross-check, **not** a state-of-the-art dedicated
  #SAT solver comparison.
- Default cap 3000 memo states for both recursive internal methods,
  1024 inclusion-exclusion subsets, 2.5s per attempt, two repeat timing
  samples per internal method, and a 1000-model cap on enumeration.
- Wall-clock medians include source recognition/ANF encoding, not merely
  the final algebraic query. All exact model counts must agree; any
  external SAT decision must agree with any completed count's zero/nonzero
  verdict.
- Emit one JSON object per instance with family, seed, interaction density,
  statuses, model counts, states, backend, measured times, and a summary.
  Incomplete budgets, timeouts, and uncompleted model enumeration remain
  visible and never become an UNSAT claim.

## Interpretation and decision gate

We are looking for consistent improvements on mixed *nonlinear* cases
with shared interactions, not just on intentionally factorable data.
If CRC fails most instances under equal state/time budgets or wins only
on XOR constructions already easy for dedicated parity reasoning, retain
the method as a narrow exact option; do not claim an algorithmic advance.

These random small instances are an initial development gate. A
meaningful performance claim requires larger multi-seed datasets,
confidence intervals, reproducible machine configurations, independent
state-of-the-art SAT solvers for decision, and specialized *exact #SAT*
solvers (e.g. dedicated counters, not repeated SAT enumeration) for
counting. In addition, use planted satisfiable/unsatisfiable and
Tseitin-style adversarial controls. The Shannon coefficient oracle is
ordinary weighted model counting with worst-case exponential growth.

Lean formal verification remains a separate obligation: source CNF
semantics, exact small-XOR extraction, projection, requested Walsh
coefficient query, contraction, budgets, and the correspondence from
the Python-produced results to checker-approved evidence. No universal
complexity-theory theorem is implied by W-CRC-002.
