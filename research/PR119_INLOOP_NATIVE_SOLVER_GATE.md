# PR #119: In-loop masked decomposition versus native MiniSat

Status: **negative competitive-runtime result**, retained for research
decision-making. No claim of solver advantage or novel algorithm.

## Method

Run `scripts/benchmark_inloop_vs_minisat.py` with `python-sat` installed.
The benchmark uses five existing families (hidden, random 3-SAT,
disconnected 3-SAT, mixed parity, bridged parity), eight seeds per family,
five alternated repetitions per formula, and checks Witnora's SAT/UNSAT
answer against MiniSat22 on every repetition.

Both measurements include the respective solver's construction/initialization
work; the Python prototype and native compiled MiniSat are **not**
implementation-equivalent. Per-formula timing medians are summed to compare
total work on this fixed study, not to predict asymptotic scaling.

| Metric | Masked Python DPLL | MiniSat22 |
| --- | ---: | ---: |
| Formulas | 40 | 40 |
| Repetitions | 5 | 5 |
| SAT/UNSAT disagreements | 0 | 0 |
| Sum of per-formula median times | 37.02085 ms | 4.55585 ms |
| Per-formula timing wins | 0 | 40 |

**Result:** masked Python DPLL took **8.126×** the cumulative time.
This does not establish a speed advantage over native SAT solvers; it is
evidence against promoting the current Python prototype on performance.

For context, the pre-existing within-Python benchmark on the same five
families found 26/40 masked wins against frequency-DPLL and a summed
median-time reduction (62.6564 ms to 35.9205 ms). That comparison is
useful for isolating implementation effects but **is not** a MiniSat win.

## Next falsification gate

Determine whether structural decomposition can yield a decision or node
advantage that survives controlling for Python overhead, on new held-out
families and harder instances. If not, retain it as a negative prototype
and redirect effort to more selective structural operators. Benchmarking
with one machine and tiny runtimes is preliminary; broader solver and
resource comparisons remain unperformed.
