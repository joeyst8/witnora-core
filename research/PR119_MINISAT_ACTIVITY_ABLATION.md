# MiniSat-informed conflict-activity branching — negative gate

## Hypothesis and source

MiniSat's `Solver::analyze` bumps activities of variables involved in a
conflict, and `pickBranchLit` selects high-activity unassigned variables
through a heap. Its activity increment is increased each conflict, which
implements relative decay. Source inspected:

https://github.com/niklasso/minisat/blob/master/minisat/core/Solver.cc

We added three small, no-op extension hooks to the existing first-UIP Python
solver, then independently implemented an activity policy in
`scripts/experiment_minisat_vsids_ablation.py`. It bumps each newly seen
conflict variable, increases the bump increment by `1/0.95` after conflict,
rescales extreme activities, and chooses the maximum-activity unassigned
variable with deterministic static-priority ties.

Compare on one **identical** watched-literal, first-UIP, chronological
branch-polarity, learned-clause and backjump engine:

- `static`: existing occurrence-ranked variable choice.
- `activity`: dynamic conflict activity priority; no heap acceleration.

This is a partial MiniSat-inspired EVSIDS ablation, **not a reproduction of
MiniSat**. Neither variant implements phase saving, restarts, learned-clause
database reduction or minimization. Both use positive-first polarity.

## Bounded gate, not an unchecked timeout

An initial unrestricted run exhibited a severe hard-case slowdown and was
interrupted. We then added an explicit **2,000-conflict budget**. Reaching
the bound returns `UNKNOWN`, never `UNSAT`; completed answers must agree
with independent native MiniSat22. Timings charge all work, including
budget-exhausted cases, but such cases are **not counted as solved**.

137 cases: 16/32-variable cross-XOR controls (96), OOD 3-SAT (12), mixed
parity (12), additional near-threshold random 3-SAT (12), and pigeonhole
contradictions (5). Seven repeated timings, per-case medians.

| Metric | Static CDCL | Activity CDCL | Native MiniSat22 |
|---|---:|---:|---:|
| Completed cases | 137/137 | **136/137** | 137/137 |
| Time sum on shared 136 solved cases (ms) | **44.8954** | 174.7567 | 11.2784 |
| All-case time including budget exhaustion (ms) | **172.6278** | 609.3930 | 29.6088 |

Activity was faster on **19 of the 136 matched completed cases**, reduced
decisions in six, and increased them in thirteen. Its failure to complete
was the planted **8-pigeon/7-hole** contradiction, where it exhausted the
2,000-conflict budget; static CDCL solved that case with 796 decisions.

This is a **clear regression** for the tested implementation. It does not
demonstrate anything negative about modern MiniSat's full heuristic stack.
Many times are tiny Python microbenchmarks, and no SATLIB holdout or Lean
certificate is claimed.

## Independent checks

- Five dedicated tests: 180 randomized CNFs, 30 extra phase-transition
  random instances, malformed decay rejection, budget exhaustion semantics,
  and a benchmark smoke check.
- Every learned clause from the 180 random cases independently tested for
  logical entailment with a separate MiniSat22 solver under its negation.
- All fully decided answers agree with native MiniSat; budget exhaustion is
  explicitly `UNKNOWN`.

Reproduce:

```
python -c 'from scripts.experiment_minisat_vsids_ablation import benchmark; print(benchmark(seeds=12,repeats=7)["summary"])'
python -m unittest tests.test_minisat_vsids_ablation -q
```

## Decision

**Reject promotion of stand-alone dynamic activity.** This result supports
testing the *interaction* of polarity phase saving, efficient decision
selection and restarts on a stronger benchmark, with independent ablations
and an explicit work cap. Do not tune constants on the same 137 cases and
then claim a discovery. Preserve this negative benchmark as the control.
