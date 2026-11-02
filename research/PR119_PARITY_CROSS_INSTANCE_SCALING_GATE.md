# PR #119: Frozen symbolic-parity transfer — correctness generalizes, speed does not uniformly generalize

**Research draft; no novel theorem or world-changing performance claim.**
The source-exact right-ROBDD / backward-pruned sparse-left operator that beat
CryptoMiniSat on `par32-1-c` was applied with unchanged symbolic primitives
and resource caps to three additional authentic SATLIB PARITY sources. It
found and checked complete original models in every run. It lost to
CryptoMiniSat on both `par16` sources and gained a smaller, noisy advantage
on another independent `par32` source. The distinct-size evidence reveals a
practical performance crossover, **not** algorithmic superiority in general.

## Source and holdout integrity

The original benchmark files are from the
[Rutgers DIMACS CNF archive](https://archive.dimacs.rutgers.edu/pub/challenge/satisfiability/benchmarks/cnf/).
SATLIB describes these as satisfiable parity-learning instances, with five
instances at each of sizes 8, 16 and 32; the `-c` files are pre-simplified
variants of the same family.

| Approved validation source | Original variables | Raw clauses | Decompressed SHA-256 |
|---|---:|---:|---|
| `par16-1-c.cnf.Z` | 317 | 1,264 | `33691e8d6a59db323b77240ae6319353f3adc0738c36e7a3e1e9f3efaa182d8a` |
| `par16-2-c.cnf.Z` | 349 | 1,392 | `d85df8f9275977bbeb1e50fb2a3b8bce59fb6e0158dbde0b0ec33fb8faa30560` |
| `par32-3-c.cnf.Z` | 1,325 | 5,294 | `fe096410a048413b6279239143bab90bb5fb54037f7ac38d431cf81e892c12b6` |

The SHA is checked before any solver worker starts. The second 32-bit source,
**`par32-2-c`, remains sealed** and is explicitly rejected before any
network call. No unapproved files, hidden witness assignments or hand-tuned
global parity right-hand sides are accepted by this validation driver.

**Selection timeline and caveat:** The two public 16-bit sources were chosen
before their runtime measurements. After observing that the smaller sources
lost, the independent full-size `par32-3-c` was selected from the published
archive to check the suspected size crossover. The algorithm and caps were
kept fixed. This **adaptive choice means the third case is exploratory**;
it is not a pristine preregistered held-out test of a universal speedup.

## Frozen mechanism and applicability

- Extract only XOR equations proven by complete original-CNF encodings.
  Project exact equations over residual variables by GF(2) elimination.
- Separate source-derived width-3 local XORs from larger global parity rows;
  refuse unsupported source structures. The original `par32-1-c` produced
  186 local and 32 global rows; `par16` produces 61 local and 16 global
  rows. The new full-size instance also produces 186 local and 32 global.
- Select the smallest source-primal separator among natural-order cuts,
  with at least `max(8, floor(residual_vars / 4))` interior variables on
  either side. This rule generalizes the original quarter-size eligibility
  condition, not a choice fitted to runtime results.
- Exact bucket elimination counts all boundary-conditioned local models.
  Sweep the larger side by a canonical syndrome ROBDD; sweep the smaller
  side by forward signature transfer restricted to exact backward-viable
  frontier transitions. Join a pair by 16- or 32-bit XOR signature equality.
- Use **one** native-XOR SAT assumption query for the matched larger-side
  model, reconstruct the auxiliary XOR-only source variables from the
  already-extracted equations, and verify **every original raw clause**.
- Keep the original strict caps: 30-second isolated source-to-verification
  worker, 500,000 BDD nodes, 250,000 sparse entries and 100,000 frontier
  states. Incomplete work returns `UNKNOWN`, never UNSAT.

The core symbolic BDD operations, sparse transfer semantics and original
instance implementation were **not modified** to optimize these new cases.
The new driver adapts only source-derived dimensions. These sources are all
from the *same parity-learning family*, not evidence on arbitrary SAT,
industrial planning, cryptographic verification or unrelated applications.

## Matched CryptoMiniSat control: all original witnesses verified

Two trials per source, sequential symbolic then plain CryptoMiniSat 5.17.0,
single thread, from the same already-fetched SHA-checked source in each case.
Source download excluded in both methods; initialization, source analysis,
exact counts, compilation, search and final raw-source audit included in
the symbolic worker. `CryptoMiniSat` worker counts are taken immediately
before final verification; process wall times include its verification.

| Source / pair | Witnora worker | Raw CryptoMiniSat worker | Witnora wall | CryptoMiniSat wall |
|---|---:|---:|---:|---:|
| `par16-1-c`, 1 | 233.59 ms | **109.91 ms** | 238.20 ms | **114.84 ms** |
| `par16-1-c`, 2 | 220.11 ms | **99.51 ms** | 224.56 ms | **105.10 ms** |
| `par16-2-c`, 1 | 216.67 ms | **113.59 ms** | 220.63 ms | **119.19 ms** |
| `par16-2-c`, 2 | 265.69 ms | **139.39 ms** | 269.44 ms | **144.99 ms** |
| `par32-3-c`, 1 | **3,642.38 ms** | 4,607.88 ms | **3,682.22 ms** | 4,615.27 ms |
| `par32-3-c`, 2 | **4,158.10 ms** | 4,201.73 ms | 4,209.19 ms | **4,208.61 ms** |

For `par16-1-c` the symbolic method is about **2.2× slower** by worker
time; for `par16-2-c` it is about **1.9× slower**. On the independent
32-bit instance the worker mean was **3.900 s versus 4.405 s** (~11.5%
lower), but one of the two trials is effectively a tie in process wall
time. Therefore **no statistically sound general-speed claim follows**.
The previous locked `par32-1-c` source gate reported three interleaved
symbolic runs averaging 3.440 s versus raw CryptoMiniSat 4.250 s (~19.1%
lower); this is encouraging size-32 replication, not cross-family proof.

The initial exploratory `par32-3-c` probe also returned source-verified SAT
in both trials. One recorded paired trial was **3,865.36 ms** symbolic
versus **4,585.27 ms** CryptoMiniSat. Its first trial's complete metric
record was truncated during tool output, so it is *not* included in the
quantitative paired table. The subsequent compact two-run replication above
was retained in full instead of choosing a best run.

## Why the outcome changes with size

The local nonlinear constraints and exact widths are highly similar across
the members of this family:

| Structural measure | `par16` sources | `par32` sources |
|---|---:|---:|
| Residual variables | 124 | 375 |
| Local width-3 XORs | 61 | 186 |
| Wide global syndrome XORs | 16 | 32 |
| Example natural separator boundary | `{59,61}` | `{184,186,188}` |
| Local models, exact join | 5,489 | 704,494,193 |
| Side-factor counting width | 3 | 5 |

The 16-bit source analysis costs roughly **0.18–0.23 s**, while unmodified
CryptoMiniSat can solve and verify the entire original source in roughly
**0.10–0.14 s**. Even excellent symbolic joins cannot pay back that
preparation overhead on such small cases. At 32 bits, direct original-CNF
solver work grows while the width-bounded symbolic join stays comparatively
cheap enough to compete.

For `par32-3-c`, the larger side has 40,920 models with **40,920 distinct
32-bit syndrome words**. Its final ROBDD has **37,655 reachable nodes**
from 243,805 allocated temporary/canonical nodes; the smaller side has
4,992 distinct syndromes. All original 5,294 clauses were checked true
for the final source assignment. Its Boolean vector digest is:

`161871dfa2815c542f1dead1fe3521b2801df6b9688b7f25e2497689707955df`.

Both 16-bit sources likewise returned complete original-CNF models:

- `par16-1-c`: `87b9d8c87f34ce4e93c1f551840576338178cbd55ce8c8265a62f780ac09eee9`
- `par16-2-c`: `240f4685693de40bd7aa85d45ed7e079feebe7c5f1c2693dd08831761851fb56`

## Independent solver and regression control

On `par32-3-c`, the already-configured independent **CaDiCaL 1.95**
original-CNF solver timed out twice with a 12-second isolated cap:
`UNKNOWN_TIMEOUT` at **12,015.53 / 12,013.95 ms**. These are *unknown*
outcomes, **not UNSAT certificates**, and do not establish that no other
modern solver can beat Witnora. Plain CryptoMiniSat remains the completed
strong comparator.

The combined **53 relevant offline regressions passed** (47 previous and
six new cross-instance/holdout/digest/cap/reporting checks). Small-formula exactness
of BDD operations and sparse witness mapping has additional exhaustive
truth-table tests in the prior gate. The cross-instance code introduces
no additional theorem or Lean proof of Python refinement.

## Reproduction

With the existing pinned Python dependencies installed:

```sh
# All fixed public cross-instance validation sources, two paired trials each:
python scripts/experiment_satlib_symbolic_cross_instance_gate.py \
  --repeats 2 --budget 30 --compact

# One full-size public source, with the complete structural/source record:
python scripts/experiment_satlib_symbolic_cross_instance_gate.py \
  --names par32-3-c.cnf.Z --repeats 2 --budget 30

python -m unittest \
  tests.test_satlib_symbolic_cross_instance_gate \
  tests.test_satlib_symbolic_syndrome_bdd \
  tests.test_satlib_incremental_syndrome_oracle \
  tests.test_satlib_syndrome_mitm \
  tests.test_satlib_residual_geometry \
  tests.test_satlib_residual_fourier \
  tests.test_satlib_local_nonlinear_bridge \
  tests.test_satlib_cryptominisat_gate \
  tests.test_satlib_affine_quotient \
  tests.test_real_satlib_parity_gate \
  tests.test_verified_flip_orbits -v
```

An additional independent check uses
`scripts.benchmark_real_satlib_parity_gate.bounded_solve` with `Cadical195`
and 12 seconds on the SHA-pinned `par32-3-c` original raw clauses.

## Scientific decision

**Keep and develop the specialized operator, but do not release a novelty
claim.** We have exact source-verified solutions on four independent
historical parity instances across two sizes, performance wins on two
full-size source cases, and equally real negative small-case evidence.
The speed effect is plausibly a structural/size crossover, not an
unprecedented theorem or a general breakthrough.

Before publishing a significant claim, freeze the *entire* remaining
evaluation suite ahead of measurement, test additional unseen full-size
parity instances and genuinely unrelated SAT families, compare current
strong solvers with all charged preprocessing/verification, and investigate
whether a new provable syndrome-compression invariant exists. Continue
Track A's outstanding Lean normalization, extraction and Python-to-Lean
refinement obligations independently of performance. Keep `par32-2-c`
sealed until an explicit preregistered evaluation decision.
