# First-UIP CDCL prototype — limited crossover, not a breakthrough

## Source and method

MiniSat's upstream `Solver::analyze` resolves an implication graph toward a
first unique implication point (first UIP). `search` adds the learned clause,
backjumps, and asserts its implied literal. Sources:

- https://github.com/niklasso/minisat/blob/master/minisat/core/Solver.cc
  (`analyze`, `propagate`, `search`, `cancelUntil`)
- https://github.com/niklasso/minisat/blob/master/minisat/core/Solver.h

`scripts/experiment_minisat_first_uip.py` independently implements the
standard algorithm in a small Python watched-literal engine with:

- A stable assignment trail and per-variable implication reason/level.
- Two-watched-literal propagation, dynamically attached learned clauses.
- First-UIP resolution, non-chronological backjumping, asserting literals.
- Same original occurrence-priority / positive-first branching baseline as
  `TrailDPLL`, **but branches diverge after learning**, as intended.

It intentionally **does not yet implement** VSIDS, restarts, phase saving,
clause minimization, or learned-clause database reduction; these are material
parts of MiniSat. No source code was copied; MiniSat is MIT licensed.

## Correctness evidence

- 125 fixed instances (12 seeds across 16/32-variable XOR controls, 3-SAT and
  mixed parity OOD, plus five pigeonhole UNSAT sizes): both experimental
  variants agree with independent native MiniSat22 SAT/UNSAT results.
- Another 250 randomized CNFs and ten adversarial/edge fixtures tested.
- **Every learned clause** in these additional tests was semantically audited
  using an independent MiniSat oracle: `original CNF AND NOT learned-clause`
  must be UNSAT. This is an external validation, **not a certificate**.
- After each backjump, all non-asserting learned literals are checked false
  before the asserting literal is enqueued.
- Three dedicated unittest methods passed.

## Timed ablation (9 repeats, median per formula)

| Metric | Watched DPLL | First-UIP CDCL | MiniSat22 |
|---|---:|---:|---:|
| Fixed instances | 125 | 125 | 125 |
| Sum of median milliseconds | 235.6304 | **189.9180** | **31.4733** |
| Cases faster than watched DPLL | — | 15/125 | Not reported |
| Learned clauses during one run per instance | — | 1,181 | Not instrumented |

The aggregate speed improvement is **dominated by a few planted hard
pigeonhole contradictions**. On the harder pigeonhole families:

| Pigeons / holes | Watched DPLL decisions | CDCL decisions | DPLL ms | CDCL ms |
|---|---:|---:|---:|---:|
| 7 / 6 | 719 | **218** | 23.20 | **21.14** |
| 8 / 7 | 5,039 | **796** | 198.40 | **153.12** |

On the smaller pigeonhole tests, CDCL is often slower; most OOD tests do not
benefit either. MiniSat remains decisively faster, even on hard cases.
These are tiny Python timing runs, not statistical proofs of general speed.
The DPLL/CDCL runtime environments match; native-vs-Python comparison is a
practical reference, not a language-controlled algorithm comparison.

Reproduce:

```
python -c 'from scripts.experiment_minisat_first_uip import benchmark; print(benchmark(seeds=12,repeats=9)["summary"])'
python -m unittest tests.test_minisat_first_uip -q
```

## Decision

**Retain as engineering progress in draft research only.** Learning/backjumping
can dominate at sufficient problem difficulty, but this is established CDCL
behavior, not novel Witnora mathematics. To integrate soundly, produce
independently checkable learned-clause resolution traces and a source-bound
UNSAT proof. Next performance gate should isolate a cheap activity heuristic
or restarts on native-scale realistic workloads without changing correctness
criteria. Do not market this as world-changing research yet.
