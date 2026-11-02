# Source-verified symmetry units inside CDCL — no runtime win

## Question

The previous flip-orbit experiment reduced brute-force candidate enumeration.
Does that benefit transfer to actual clause-learning SAT search when we add
one representative-selection unit clause per verified symmetry pivot?

## Mathematically permitted transformation

For a CNF `F`, each accepted sign-flip generator `g` is audited against **all
original clauses**, satisfying `F(x) == F(x xor g)` for every assignment.
Generator span is a GF(2) subgroup. Its echelon basis defines a unique orbit
representative with every pivot bit equal to zero. Hence the transformed
formula

`F AND (AND_{pivot bit p} NOT x_p)`

is **equisatisfiable** with `F`. It is *not* pointwise logically equivalent:
it excludes satisfiable nonrepresentative assignments. A source-bound UNSAT
certificate for the original CNF would need to carry and verify this orbit
argument before accepting UNSAT from the strengthened formula.

To bound overhead we added a conservative gate to the candidate detector:
if **no exact source-bound XOR rows** are detected, it skips the expensive
flip-candidate sweep. This gate is incomplete for CNF symmetries unrelated
to XOR, but does not introduce false symmetries. The previous exploratory
orbit benchmark retains its original ungated behavior by default.

This operator is known SAT symmetry breaking, not a novelty claim.
Prior examples include Aloul et al., *Solving Difficult SAT Instances in
the Presence of Symmetry*:
https://web.eecs.umich.edu/~imarkov/pubs/conf/c023.pdf

## Experiment

`scripts/experiment_flip_orbit_cdcl_gate.py` compares plain and augmented
CNF on **both** native MiniSat22 and our watched-first-UIP Python CDCL.
The augmented timing includes exact XOR detection, generator construction,
verification against the full source CNF, representative units, solver
initialization and search. Each solver is freshly initialized per timing.

63 cases: 10/14/32-variable synthetic XOR SAT, contradictory XOR/unit,
partially symmetry-broken XOR, random 3-SAT controls (five seeds each),
plus three pigeonhole controls. Five repeats, per-instance median times.

| Metric | Plain CNF | Verified orbit units (incl. overhead) |
|---|---:|---:|
| MiniSat22 total time | **2.2412 ms** | 113.3427 ms |
| Python first-UIP total time | **14.2395 ms** | 123.5765 ms |
| Python cases with fewer decisions | — | 30/63 |
| MiniSat cases with lower time | — | **0/63** |
| Python cases with lower time | — | **0/63** |

45/63 cases had positive verified flip-group rank. All 63 augmented and
unaugmented results matched the independent MiniSat truth oracle. The
three pigeonhole cases have no detected XOR-derived sign flip symmetry;
the gating overhead there is still nonzero.

Extra correctness: 150 randomized mixed XOR/CNF examples were checked for
equisatisfiability with independent MiniSat, and any augmented SAT model was
verified directly against the original CNF and pivot units. Exhaustive
small-formula checks confirm that, when a model exists, at least one exists
with all pivot bits zero. Four dedicated tests passed.

## Decision

**Fail the performance gate; do not promote.** The shortcut is mathematically
sound and reduces some decision counts, but the preprocessing is much more
expensive than the actual MiniSat solves on these workloads. This is a
specific synthetic negative result, not a theorem that symmetry breaking
never helps. The method is established in prior research and produces no
world-changing or Lean-certified novelty. Preserve the audit as a control
for any future source-bound quotient claim.

Reproduce:

```
python -m scripts.experiment_flip_orbit_cdcl_gate
python -m unittest tests.test_flip_orbit_cdcl_gate -q
```
