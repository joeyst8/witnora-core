# Phase-saving and restarts: controlled MiniSat-inspired interaction gate

## Research question

Could missing phase saving and restarts account for the severe regression of
our independently implemented conflict-activity heuristic?

Using one watched-literal, first-UIP CDCL engine, we compared five variants:

1. `static`: original occurrence-priority variable selection, positive-first.
2. `activity`: decayed conflict-activity priority, positive-first.
3. `phase`: activity priority plus phase saving at backjump.
4. `restart`: activity priority plus geometrically increasing restarts.
5. `combined`: activity priority plus both phase saving and restarts.

The restart schedule starts at 32 conflicts and grows by `ceil(1.5×)`. The
new solver preserves learned clauses during restarts and reprocesses root
assignments to account for newly attached clause watchers. We did not tune
these constants to win the current benchmark. Phase saving remembers the
sign of an assigned variable when it is undone, then reuses that sign on its
next decision. This remains a **simplified** interpretation of MiniSat's
feature interaction, not a reproduction of its complete implementation.

Upstream primary code consulted:
https://github.com/niklasso/minisat/blob/master/minisat/core/Solver.cc

## Truth and resource controls

All branches were capped at **2,000 conflicts**, with exhausted runs
returning `UNKNOWN` rather than a guessed SAT/UNSAT answer. Independent
MiniSat22 checked every completed result. Five modes rotated their order
between timing repeats. Median time per instance was summed across 137
fixed test cases: 16/32-variable XOR controls, OOD random 3-SAT, mixed
parity, 24-variable transition 3-SAT, and five pigeonhole contradictions.

Six new tests passed, including 120 additional randomized CNFs tested in all
five modes with independent entailment checks for learned clauses, forced
restarts, remembered negative polarity, budget-exhaustion semantics, and
bad-parameter rejection. No Lean proof or UNSAT certificate was produced.

## Result (five repeats, fixed 2,000-conflict budget)

| Variant | Completed / 137 | Time on 136 shared solved cases | Charged time on all 137 |
|---|---:|---:|---:|
| Static first-UIP | **137** | **44.1168 ms** | **171.4765 ms** |
| Activity only | 136 | 182.3723 ms | 625.1432 ms |
| Activity + phase | 136 | 155.7203 ms | 762.4352 ms |
| Activity + restarts | 136 | 182.4223 ms | 674.1874 ms |
| Activity + both | 136 | 316.0611 ms | 1282.1222 ms |
| Native MiniSat22 | **137** | 12.0028 ms | 31.2557 ms |

Every activity-based variant exhausted the budget on the planted 8-pigeon /
7-hole contradiction. Static CDCL solved this instance with 796 decisions;
the activity variants had accumulated at least 2,000 conflicts before
giving up. The combined variant was slower than activity alone on the common
solved subset. Phase saving did reduce its matched-case time relative to
activity alone, **but neither approach approached static CDCL**.

Charged totals **include incomplete computations** and therefore are not
comparisons of complete solver throughput. The 136-case matched totals are
more relevant for runtime comparisons; the 137th case measures coverage.
These are small Python microbenchmarks, not a SAT competition or proof of
general disadvantage for fully implemented MiniSat heuristics.

## Gate decision

**Reject this particular feature combination.** Watched propagation remains
our robust engineering speedup; first-UIP learning gives a real advantage
only on some hard cases, while activity+phase+restart does not generalize
here. Preserve these negative results in draft. Before further tuning,
prioritize source-bound proof traces and find a demanding, independently
reproducible workload with larger genuine (non-planted) search savings.

Reproduce from repo root with PySAT:

```
python -c 'from scripts.experiment_minisat_phase_restart import benchmark; print(benchmark(seeds=12,repeats=5,conflict_budget=2000)["summary"])'
python -m unittest tests.test_minisat_phase_restart -q
```
