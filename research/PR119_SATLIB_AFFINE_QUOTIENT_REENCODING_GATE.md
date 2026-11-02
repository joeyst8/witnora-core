# PR #119: Original SATLIB PARITY affine-quotient re-encoding gate

**Status: research draft, not a discovery or publication claim.** The
underlying transformation is standard GF(2) elimination and XOR re-encoding.
It is being tested as a concrete, falsifiable SAT acceleration hypothesis.

**Later strong-baseline update:** `PR119_CRYPTOMINISAT_STRONG_BASELINE_GATE.md`
shows that CryptoMiniSat 5.17.0 also solves the unmodified original CNF in
3.78–4.05 seconds; our quotient with the *same* backend takes 3.92–4.02
seconds including preprocessing. The favorable MiniSat/CaDiCaL comparison
below is **not a competitive breakthrough**. Preserve this earlier note for
chronology, not as an independent speedup claim.

## Locked source and evaluation boundary

- Development problem: historical `par32-1-c.cnf.Z` from the original Rutgers
  DIMACS archive, not a generated imitation.
- Official decompressed DIMACS SHA-256:
  `5e3253738e729c3fda8cde22e67b6d8bae0df6d53e9afabb6bd74d5ceb700312`.
- 1,315 variables, 5,254 original raw clauses, previously authenticated in
  `PR119_OFFICIAL_SATLIB_PARITY_HARDNESS_GATE.md`.
- **Holdout** `par32-2-c.cnf.Z` is deliberately not run by this prototype.
  The script rejects that name. Its earlier baseline and structural metadata
  remain visible, but do not tune on its solve results.
- A cap includes CNF normalization, parity detection, Gaussian elimination,
  quotient construction, solver initialization, solving, model decoding, and
  raw-source witness validation. File download is not charged to either arm.
  The original-CNF arm only needs native solver initialization and solving:
  this is a *conservative* disadvantage to the quotient.

## Equisatisfiable, model-checked transform

1. Recognize only **complete, source-bound** XOR CNF encodings. The 1,158
   recognized equations have independent rank 1,158, leaving affine dimension
   157. Remove exactly their 4,632 verified encoding clauses.
2. Solve the equations symbolically in GF(2), retaining the nonzero RHS, to
   express every original variable as the XOR of independent coordinates and
   a constant. Inconsistent XOR equations fail closed.
3. Substitute those expressions into the 622 residual clauses (372 binary,
   250 ternary), sharing intermediate pairwise XOR gates. Every introduced
   gate is constrained by its complete four-clause truth-table encoding.
4. Ask a *stock* PySAT native CDCL solver to solve the transformed clauses.
   Reconstruct a complete original assignment from the independent coordinate
   values. For every SAT response, require all **5,254 original raw clauses**
   to evaluate true. UNSAT remains a solver claim, not a constructed witness.

For the natural pivot order, the quotient has **157 free coordinates**,
**1,010 cached XOR gates**, **1,167 total variables**, and **4,662 clauses**;
every clause has width 2 or 3 (372 two-literal, 4,290 three-literal).
The 1,010 gates introduce 4,040 clauses; the original residual contributes
622. The largest residual clause touches 31 independent coordinates after
substitution; mean support is 7.135.

The `residual_first` order is **identical** structurally in this source
because its 375 residual variables already occur first in the natural
ordering. The `reverse` pivot order balloons to 5,410 new XOR gates,
5,567 variables, 22,262 clauses, maximum support 64, and mean support 24.495.
This is a real coordinate-selection sensitivity, not proof of novelty.

## Experimental observations

First strict **3-second all-in gate**: all of natural and `residual_first`
timed out for MiniSat22, Glucose3 and CaDiCaL195. The initial profile revealed
**2.2–2.9 seconds** spent in Python source detection/transformation. The
3-second result therefore measures preprocessing cost as much as solve power.

First **7-second matched cap** on this single development instance:

| Method | Solver | Status | Worker total, including transform | Transform | Source witness |
|---|---|---|---:|---:|---|
| Original unchanged CNF | MiniSat22 | `UNKNOWN_TIMEOUT` | over 7 s | 0 | — |
| Original unchanged CNF | Glucose3 | `UNKNOWN_TIMEOUT` | over 7 s | 0 | — |
| Original unchanged CNF | CaDiCaL195 | `UNKNOWN_TIMEOUT` | over 7 s | 0 | — |
| Affine quotient, natural | MiniSat22 | `SAT` | **3,571.93 ms** | 2,239.59 ms | all raw clauses verified |
| Affine quotient, natural | Glucose3 | `UNKNOWN_TIMEOUT` | over 7 s | — | — |
| Affine quotient, natural | CaDiCaL195 | `SAT` | **5,605.54 ms** | 2,784.81 ms | all raw clauses verified |

The native unmodified source baselines are valid `UNKNOWN` timeouts; they are
**not** UNSAT proofs. Glucose has only one 7-second trial here, and its
failure should not be generalized.

### Sequential repeatability check (7 seconds per trial)

We subsequently ran two more sequential, independently timed trials for each
pair. Each quotient run redoes full Python source detection, row reduction,
compilation, native solving, and original-witness verification. They are not
cached-preprocessing timings.

| Solver | Raw original CNF, trials 1–2 | Quotient, total worker ms trials 1–2 | Quotient transform ms trials 1–2 |
|---|---|---|---|
| MiniSat22 | timeout, timeout | **4,670.50; 4,601.75** (`SAT`, `SAT`) | 3,140.78; 2,885.11 |
| CaDiCaL195 | timeout, timeout | **5,195.38; 4,797.95** (`SAT`, `SAT`) | 2,798.43; 2,604.11 |

Both independent solver runs followed exactly the same deterministic search
behavior on the transformed source: MiniSat reported 65,021 conflicts and
CaDiCaL 69,785 conflicts each time. Each returned source model passed the
entire raw CNF audit. These trials support a narrow, **local encoding
advantage** over the tested pure-CNF solvers at this cap, not a general
speedup or evidence of a genuinely new algorithm.

### Explanation control: change variable numbers only

For the **same original clauses**, change each variable ID by a fixed
bijection; do not remove clauses or conduct parity elimination. Decode any
SAT model back to the original variables and verify against the raw CNF.

| Numbering-only control | Solver | 7-second status |
|---|---|---|
| Reverse `v → n+1−v` | MiniSat22 | `UNKNOWN_TIMEOUT` |
| Random permutation, seed 1729 | MiniSat22 | `UNKNOWN_TIMEOUT` |

These controls reject *two* trivial permutation explanations, not all solver
heuristic effects. XOR re-encoding can also change branching heuristics,
literal activity, propagation, and clause order. We do not attribute an
observed win uniquely to mathematical elimination.

## Reproduction and tests

```shell
PYTHONPATH=/tmp/witnora_bench_deps:. python -m unittest \
  tests.test_satlib_affine_quotient tests.test_real_satlib_parity_gate \
  tests.test_verified_flip_orbits -v

PYTHONPATH=/tmp/witnora_bench_deps:. python \
  scripts/experiment_satlib_affine_quotient.py --timeout 7 \
  --orders natural --controls original reverse random_1729 \
  --solvers Minisat22 Glucose3 Cadical195
```

There are 12 passing offline tests in the listed scope: exact small-domain
SAT-model bijection for three pivot orders, no-XOR case, strict numbering
control bijections, invalid-order rejection, and existing source/audit tests.

## Literature, limitations, and next decision

Source provenance: [original DIMACS archive](https://archive.dimacs.rutgers.edu/pub/challenge/satisfiability/benchmarks/cnf/)
and [SATLIB PARITY background](https://www.cs.ubc.ca/~hoos/SATLIB/Benchmarks/SAT/DIMACS/PARITY/descr.html).
Parity-aware SAT preprocessing by Gaussian elimination is already established;
see Biere, Järvisalo and Kiesl's [SAT preprocessing handbook chapter](https://cca.informatik.uni-freiburg.de/papers/BiereJarvisaloKiesl-SAT-Handbook-2021-Preprocessing-Chapter-Manuscript.pdf)
and [complete parity reasoning in DPLL(XOR)](https://arxiv.org/abs/1207.0988).

Before any performance or originality claim: replicate timeouts and SAT wins,
include a modern native **XOR-aware** solver such as CryptoMiniSat, test
renaming/re-encoding controls and independent benchmark families, and freeze
all selection choices **before** opening the `par32-2-c` holdout. This draft
is a correctness-checked local observation only, not a world-changing result.
