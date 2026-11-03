# W-CRC-014: Width-bounded exact factor variable elimination

Status: **correctness and coverage expansion, but negative large-n timing
regression; 87 green tests**.
CI: https://github.com/joeyst8/witnora-core/actions/runs/41721388489

## Question

Can Witnora count large residual CNF components whose number of
variables exceeds its local brute-force cap, provided their
interaction width is low?

**Yes.** A bounded exact sum-product factor variable-elimination
backend admits long 2-CNF chains and rings. Unlike brute-force
component enumeration, its cost depends exponentially on the
*largest intermediate factor width*, not on the full number of
variables. It is standard bucket/variable elimination, closely
related to induced width/treewidth algorithms, not a new complexity
result. Reference: Larrosa and Dechter, *Boosting Search with Variable
Elimination* (UCI research archive):
https://ics.uci.edu/~dechter/publications/r89a.html

## Implementation and safety

- `witnora_core/crc_variable_elimination.py`
- The existing `count_source_by_separator` accepts an opt-in
  `component_backend="variable_elimination"`; its default remains
  `"enumeration"`.
- Each signed normalized clause is encoded as a table with entry 0
  on its sole violating assignment and 1 elsewhere. Factors touching
  a chosen variable are multiplied, that variable is summed out
  exactly, and a new smaller-scope integer table is produced.
- Each factor scope, intermediate union and total operation count
  obey strict user-specified hard limits. Unsupported cases return
  `None`. No approximate coefficient, SAT guess, or UNSAT inference.
- The current ordering heuristic recomputes affected factor scope
  costs from scratch across all remaining variables each step.
  This is correct but introduces substantial Python overhead.

## Tests

Six new Python tests exercise:
- 160 seeded signed random small-CNF differentials against a separate
  exhaustive full model counter;
- exact 8/16/32/64-variable positive chains and cycles against
  independent Fibonacci and Lucas integer formulas;
- explicit width, work and malformed-mask failures;
- cutset integration where previous enumeration returns
  incomplete and VE returns exact counts;
- additional seeded random source-to-cutset comparisons; and
- API invalid-backend and resource-bound rejection.

Full workflow: **87 Python tests passed**, all prior WCRC benchmarks
remained green.

## 13-case benchmark versus independent Ganak

For a path of n positive OR-2CNF clauses, the model count is
F(n+2), where F is Fibonacci. For a cycle, the count is
F(n-1)+F(n+1), a Lucas number. One full Glucose3 SAT witness search
is explicitly timed and added to the median of two source-to-count VE
invocations. The other method's previously measured in-process time
does **not** include this extra witness search.

| n | Source | Old enumeration | VE + SAT witness ms | Ganak engine ms | VE+SAT/Ganak |
|---:|---|---|---:|---:|---:|
| 16 | chain | incomplete | 1.2631 | 7.5649 | 0.167 |
| 16 | ring | incomplete | 2.2389 | 7.6749 | 0.292 |
| 32 | chain | incomplete | 3.8704 | 27.3457 | 0.142 |
| 32 | ring | incomplete | 6.7113 | 31.4758 | 0.213 |
| 64 | chain | incomplete | 15.2340 | 35.2448 | 0.432 |
| 64 | ring | incomplete | 28.8055 | 44.4013 | 0.649 |
| 128 | chain | incomplete | 79.9584 | 53.4397 | 1.496 |
| 128 | ring | incomplete | 154.1143 | 70.5597 | 2.184 |
| 256 | chain | incomplete | 539.7042 | 94.7031 | 5.699 |
| 256 | ring | incomplete | 1037.8882 | 130.2865 | 7.966 |

All 10 new counts matched the exact Fibonacci/Lucas formulas and
Ganak. The new method beat Ganak engine time on the six n<=64 cases
but lost on all four n>=128 cases. Thus the main advance is **new
admissions, not a broad speedup**.

Three planted random signed 3-CNFs (n=16/24/32, 48/72/96 clauses)
still had no admissible small primal separator under the chosen
endpoint groups, so both counters returned `INCOMPLETE_BUDGET`.
Independent Ganak counted all three.

**Summary:** 13/13 Ganak exact; 10/13 W-CRC-014 exact; 0/13
W-CRC-012 brute enumeration exact under the same 8-variable
component cap. Times are very small pilot samples from one hosted
runner, not a statistically controlled ranking.

## Successor W-CRC-015

Use an incremental factor-variable incidence index and a
versioned priority queue so unchanged elimination candidates are
not rescored after every step. This optimization should preserve
the exact factor arithmetic and strict budgets. Test the new
backend against the frozen W-CRC-014 implementation, independent
brute counts, Ganak and the same long-chain/cycle analytic controls.

Even a large implementation speedup would remain established
bounded-width exact inference, not P≠NP or a general SAT result.
