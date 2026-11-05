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


## Initial GitHub Actions results — 2026-11-03

Green run: https://github.com/joeyst8/witnora-core/actions/runs/41697640978
(27 Python unittest methods passed; 18 scaling instances completed).

All 18 original inclusion-exclusion CRC attempts returned
INCOMPLETE_BUDGET. Opt-in exact Shannon CRC, existing ANF, and the
external Glucose3 *all-model enumeration* each completed all 18;
**every exact model count agreed**. PySAT decision agreed with each
zero/nonzero classification.

| Family (9 cases each) | Median Shannon CRC | Median ANF | Median PySAT model enumeration | CRC faster than ANF |
| --- | ---: | ---: | ---: | ---: |
| Dense random 3-CNF | 4.8181 ms | 6.1803 ms | 0.1326 ms | 8 / 9 |
| Mixed XOR + overlapping nonlinear 3-CNF | 5.1942 ms | 16.2233 ms | 0.1494 ms | 9 / 9 |

Median of **per-instance** ANF/CRC speed ratios:
1.204x dense-only; 3.123x mixed. These are not the ratios of the
median runtimes in the table. Individual medians are two repeated
internal runs and one external model-enumeration run, on one CI machine.
For the mixed family at the k=24 boundary setting, the source has
46 variables and 191 clauses; the right nonlinear portion comprises
101 clauses. Boundary interaction edge density in the tested cases
ranges from roughly 0.67 to 0.82.

**Important negative result:** the standalone external PySAT model
enumerator is already about 34-37x faster than W-CRC-002 on these
low-model-count controls by the median per-instance ratio. These
instances are *easy for model enumeration*, so this comparison is
not a specialized #SAT solver benchmark, but it decisively rules out
claiming an external performance breakthrough on this pilot.
The speedups over ANF can arise from source representation overhead
and the tractable restricted affine-left structure, not an
unanticipated collapse in general computational complexity.

**Next gate:** select instances where naive model enumeration is
uncompetitive (many solutions) and include a **dedicated exact #SAT**
solver, plus larger random/structured controls with several repetitions.
Measure preprocessing, memory and extrapolated scaling independently.
We should also compare against native XOR-aware SAT methods. Run each
method under fair constraints and record budget exhaustion and timeouts
without dropping any failures. Do not infer novelty or a Lean proof
from the green Python tests.
