# MiniSat source-level reverse engineering: watch propagation gate

## Why MiniSat beats recent Witnora prototypes

Source studied: the upstream `niklasso/minisat` core, not a reverse-engineered
binary. Upstream code is MIT licensed; we **did not copy** solver implementation
code into Witnora. Our experimental implementation was written independently
from the published algorithmic design.

Primary source links:

- https://github.com/niklasso/minisat/blob/master/minisat/core/Solver.cc
- https://github.com/niklasso/minisat/blob/master/minisat/core/Solver.h
- https://github.com/niklasso/minisat/blob/master/LICENSE
- https://minisat.se/MiniSat.html
- Niklas Eén and Niklas Sörensson, *An Extensible SAT-solver*, SAT 2003:
  https://research.chalmers.se/en/publication/74325

## Mechanism map (source inspected)

| Feature | MiniSat implementation | Our current experimental prototypes | Implication |
|---|---|---|---|
| Clause propagation | `Solver::propagate` uses two watched literals and an assignment queue (`qhead`) | Previous masked DPLL rebuilds/simplifies clause tuples | Full-clause rescans are avoidable |
| Assignment state | Stable trail, reason clause, decision level; `uncheckedEnqueue` | Recursive reduced clause states and dictionaries | Persist assignment state and use reversible trail |
| Conflict learning | `Solver::analyze` learns a first-UIP clause | No learned clauses in the isolated DPLL | Avoid re-exploring related failures |
| Backjumping | `cancelUntil(backtrack_level)` | Chronological recursive backtracking | Jump past irrelevant decisions |
| Variable ordering | Activity bumping and heap in `pickBranchLit` | Occurrence-count branch scoring | Prioritize conflicts, not just density |
| Search management | Restarts, learned-clause reduction, phase saving | No CDCL restarts or learned database | Important separate gate after watched propagation |

### What watched literals actually change

During each new assignment, only clauses watching the **now-false** literal
need attention. A satisfied alternate watcher permits an immediate skip.
Otherwise the solver either moves the watch to a non-false literal, enqueues
the other watched literal if unit, or returns a conflict. The two watches
remain valid across undo/backtracking; their positions need not be restored.
This is a known modern SAT technique, **not new Witnora mathematics**.

## Controlled Witnora prototype

`scripts/experiment_minisat_watch_reverse_engineering.py` compares:

- `scan`: repeated full-clause scans after each wave of unit propagation.
- `watch`: a persistent two-watched-literal index and assignment queue.

The two variants share the same branch ordering, polarity, recursive DFS,
original CNF, trail, and result criteria. No clause learning in either.
Both are written in Python. Native MiniSat22 is an external reference.

For 12 fixed seeds, 16/32-variable crafted cases, plus 3-SAT and mixed-parity
out-of-distribution controls (120 formulas), 15 repeats per solver and
median-per-case aggregation:

| Metric | Full scan | Watched literals | Native MiniSat22 |
|---|---:|---:|---:|
| Cases correct (against MiniSat) | 120/120 | 120/120 | 120/120 |
| Decision counts exactly matched | Yes | Yes | N/A |
| Total clause examinations | 66,327 | **5,928** | Not instrumented |
| Total median runtimes (ms) | 47.8828 | **8.8695** | **3.2869** |
| Instances with lower total time than scan | — | **120/120** | N/A |

The watched-literal approach visits **about 11.2× fewer clauses** and runs
**about 5.4× faster** in this matched-core Python benchmark. It is still
about 2.7× slower than native MiniSat22 on the same instances. Exact ratios
vary by machine and Python environment. These tiny instances are primarily
an engineering diagnostic, not a solver-performance leaderboard.

Three additional test methods (including one containing 350 random
formulas) check empty clauses, contradictory units, watcher relocation,
backtracking, and agreement with independent MiniSat22. No independent
proof or Lean refinement theorem has been established for the new watcher.

Reproduce:

```
python -c 'from scripts.experiment_minisat_watch_reverse_engineering import benchmark; print(benchmark(seeds=12,repeats=15)["summary"])'
python -m unittest tests.test_minisat_watch_reverse_engineering -q
```

## Gate decision

**Promising engineering win; retain in draft only.** The minimal watched
DPLL is a research benchmark, not an integrated or formally verified
Witnora solver. Next compare an instrumented watched-DPLL with its own
conflict-learning version. Require a separately testable proof chain for
learned clauses, reversible trail, and UNSAT output before any claim of
verified correctness. The priority is to expose headroom for genuinely
novel reasoning after eliminating baseline implementation inefficiencies.
