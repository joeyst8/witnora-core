# Draft gate: source-bound cross-support parity consequences

## Hypothesis

Exact source-CNF XOR encodings permit safe cross-equation deductions.
For example, `(x1 xor x2 xor x3 = 0)` and
`(x1 xor x2 xor x4 = 0)` imply `(x3 xor x4 = 0)` by GF(2) cancellation.
Propagating this new, shorter row might reduce DPLL search more than its
extraction and checking costs. This is standard XOR elimination, **not a
claim of mathematical novelty**.

## Implementation and soundness boundary

`scripts/experiment_cross_support_propagation.py` only uses rows recovered
by `detect_cnf_xor_patterns` from exact complete original CNF encodings;
it XORs overlapping rows and retains 1/2-variable results. The DPLL engine
propagates row-implied unit assignments, while **retaining all original CNF
clauses**. Thus every derived row is an implied consequence of source CNF.
This prototype is not a DRAT or Lean-certified solver.

Independent MiniSat22 oracle tests: 64 fixed 16/32-variable instances
(eight seeds, four families) plus 100 mixed random small instances. Three
regression tests passed.

## Result

| Metric | Result |
|---|---:|
| Fixed generated cases | 64 |
| Cross-support implied literals | 16 |
| Affine contradictions detected | 16 |
| Fewer search nodes than masked baseline | 16/64 |
| Faster end-to-end than masked baseline | **0/64** |
| Masked solver sum of per-instance median times | 4.3720 ms |
| New solver including extraction/elimination | 10.9621 ms |

These are tiny Python synthetic microbenchmarks, not stable speed ratios or
SATLIB results. Baseline masked DPLL uses a different branching heuristic
and component splitting, so node-count comparisons are not controlled for
identical search order. New solver timing includes extraction. MiniSat was
used as an independent correctness oracle, not yet a timed performance gate
for this exact experiment. The method has no demonstrated performance edge.

## Decision

**Keep the negative result in the draft; do not promote the operator.**
The sound cross-equation deduction is real, but also mathematically familiar.
Next gate: compare a *shared solver core* with and without derived rows to
isolate causal decision/conflict savings, then test large non-synthetic
instances and native MiniSat. Require source-bound certificates before
claiming verified UNSAT.

Reproduce:

```
python -m scripts.experiment_cross_support_propagation
python -m unittest tests.test_cross_support_propagation -q
```
