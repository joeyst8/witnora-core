# PR #119: Selective affine/CNF pair-conflict screen

Status: **experimental, bounded, sound-only UNSAT screen; not promoted**.

## Operator

Given an affine GF(2) row system and remaining CNF clauses, a pair of clauses
is UNSAT relative to the row system if *every* disjoint satisfying branch
for their conjunction makes the affine equations inconsistent. This is a
valid sufficient UNSAT check, not a complete SAT solver.

The unfiltered screen checks up to 120 pairs; the selective version only
checks pairs whose variables match the support of a recorded 2- or
3-variable affine row. This filter is intentionally incomplete: it may miss
UNSAT, but it cannot create a false UNSAT claim. It is not a novel
mathematical inference rule.

## Fixed synthetic study (not SATLIB)

Sixteen controlled contradictory-pair cases (eight seeds each at 16 and
32 variables), sixteen satisfiable controls, and sixteen independently
planted OOD SAT cases:

| Metric | Unfiltered | Selective |
| --- | ---: | ---: |
| Total cases | 48 | 48 |
| Target contradictions found | 16/16 | 16/16 |
| False UNSAT on SAT controls | 0 | 0 |
| Average inconclusive-check time | ~4.58 ms | ~0.051 ms |

`tests/test_affine_pair_conflict.py` checks 220 small random systems against
exhaustive enumeration; all reported UNSAT conclusions must be truly UNSAT.
An additional independent MiniSat22 check on the 48 generated cases found
16 true UNSAT cases and no false-positive UNSAT reports.

In a nine-repeat alternating-order timing comparison, the selective screen
took 1.380 ms (sum of 48 per-case median times), while MiniSat took 1.344 ms
to **fully solve** all 48 formulas. The screen solved only 16 and returned
`UNKNOWN` on 32; therefore this is **not** a speed advantage over MiniSat.
The sub-millisecond timings are preliminary, single-host measurements.

## Trust and novelty boundaries

Input affine rows are supplied directly. This experiment does **not** prove
their exact extraction from arbitrary original CNF, nor produce an accepted
Lean/DRAT UNSAT certificate. The existing Witnora G5 extraction and
certificate gates would be required before a source-bound promotion.

Next evaluation: freeze the trigger and run it as a selective, optional
operator inside actual search on independent unsolved benchmark instances.
Charge its discovery cost, compare search nodes and end-to-end wall time,
and retain `UNKNOWN` unless the contradiction is source-bound and verified.
