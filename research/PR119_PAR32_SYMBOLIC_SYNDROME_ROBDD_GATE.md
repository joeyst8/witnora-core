# PR #119: Exact symbolic syndrome compilation — first narrow strong-baseline win

**Draft research gate, not a novel theorem or general SAT claim.** The
development-source experiment now shows a repeatable, end-to-end improvement
over unmodified CryptoMiniSat on **one historical PARITY instance**. The
winning composition is established width-bounded factor dynamic programming,
reduced ordered binary decision diagrams (ROBDDs), backward automaton pruning,
and a sparse syndrome join. These are not new mathematical primitives. A
genuinely new theorem, broadly useful speedup, and formal refinement proof
are still *unestablished*.

## Fixed scientific contract

- Source: official original SATLIB `par32-1-c.cnf.Z`, decompressed SHA-256
  `5e3253738e729c3fda8cde22e67b6d8bae0df6d53e9afabb6bd74d5ceb700312`;
  1,315 variables and **5,254 raw source CNF clauses**.
- The same exact source XOR detector yields 1,158 source equations and 622
  residual nonlinear clauses. Projecting 940 XOR-only variables exposes
  375 residual variables, 186 local width-3 XORs, and 32 global XOR rows.
- The same source-derived separator `{184, 186, 188}` partitions 186 interior
  variables on each side, with natural-order frontier width at most five.
  Exact eight-way bucket-elimination model counts sum to **704,494,193**.
- Boundary mask `1` has **4,992 left** and **40,920 right** local models.
  The full global parity target includes the fixed boundary contribution.
- `par32-2-c` remains a **sealed holdout**. The gate rejects it before any
  network access. No planted model, manual XOR RHS, or secret benchmark
  answer enters the algorithm.
- The 30-second isolated worker charges **every step from source analysis
  through complete original-clause verification**. All methods exclude
  network download. Resource caps are fail-closed `UNKNOWN`, never UNSAT.

## Mathematical representation and source verification

Let `S_R` and `S_L` be the exact sets of 32-bit XOR contributions from
valid right and left interior models, respectively, with the three
separator bits fixed. A global solution exists for that boundary condition
if and only if there are `l in S_L`, `r in S_R` with

```text
                       l XOR r = target XOR boundary_syndrome.
```

The **right-hand ROBDD** is produced by sweeping the 186 interior variables
and checking each original residual-clause/local-XOR factor when its last
variable is assigned. At every step the state retains only the assignment
to variables still present in future factors (maximum frontier five).
Each state's value is a canonical ROBDD denoting the set of *all* accumulated
32-bit signatures. Choosing a true variable XOR-translates that set by the
source-derived 32-bit column. Reconvergent states combine sets by exact
ROBDD union. This is symbolic union, not approximate sampling.

The right side has **40,920 source-valid models and exactly 40,920 distinct
32-bit syndromes**, proven by the independent exact local model count and
the ROBDD's exact satisfying-assignment cardinality. The completed ROBDD has
**18,169 reachable nodes** (148,824 total nodes were allocated during
construction, including temporary canonical nodes). It compiles in about
**0.30–0.39 seconds** in the measured runs.

For the smaller left side, first construct its width-five **Boolean
frontier transition automaton**. Mark a state viable only if a backward
traversal proves it has a complete accepting continuation. Then perform an
exact forward transfer of sparse syndrome→witness maps *only on viable
transitions*. This yields **4,992 distinct syndromes**, equal to the exact
left model count, with at most 4,992 syndrome entries at any step. A
right-ROBDD membership check finds a complementary pair without enumerating
SAT models or building a second expensive ROBDD.

One right-side native-XOR assumption query reconstructs the chosen right
interior model. Both interiors and the boundary then determine the 375
residual assignments. The previously extracted **exact source XOR equations**
reconstruct the 940 remaining variables; the experiment independently
evaluates **all 5,254 original raw clauses**. A source violation fails the
worker, not merely a score or digest comparison. Every successful result
recovered the archived original Boolean-vector SHA-256:

`515c7dabc059ff203d550e1f37b2b249dd556b4746b690cdfd56589015095bbf`.

## Measured ablations: keep the failures

| Source-bound variant | Charged worker time / result | Mechanistic finding |
|---|---|---|
| Prior indexed incremental assumption oracle | 4.16–5.06 s, SAT verified | 2,017 right-side oracle queries, 2,055 exact conflict-cache skips |
| Right-side ROBDD + enumerated left SAT models | **4.80385 s, SAT verified** | Right set built in 322.86 ms; only one right query, but 4,072 left SAT models before the first match |
| Two full side ROBDDs with direct diagram intersection | **UNKNOWN**, 500,000-node resource cap at 5.39716 s | Intermediate BDD node growth prevented a completed join; **no UNSAT inference** |
| Right ROBDD compiled into a left solver's acceptance CNF | **5.36172 s, SAT verified** | 18,169 gate variables / 36,337 CNF clauses; SAT compilation/search erased the query saving |
| Sparse left frontier transfer **without** backward viability | **UNKNOWN**, 250,000-entry cap at 4.57812 s | Many locally valid prefixes cannot complete; source constraints prune late |
| **Right ROBDD + backward-pruned sparse left**, first run | **3.15523 s, SAT verified** | 4,992 unique left signatures; 51.2 ms sparse join/reconstruction; one right oracle query |

Two-sided BDD and non-pruned sparse attempts are legitimate resource-limit
failures, **not** negative satisfiability certificates. The source is known
SAT. The winning method is not a disguised faster SAT solver: the right
support is compiled symbolically and the left support is derived by bounded
width factor automaton rather than a solver-model enumeration loop.

## Interleaved matched source runs — plain original-CNF control

Both methods were run sequentially from the same pre-fetched, SHA-checked
source object in the same environment; single thread; CryptoMiniSat 5.17.0;
no tuning or network time in either worker. Source preparation and final
source model checks are charged to Witnora. Plain solver `wall_ms` includes
its verification (its `total_worker_ms` counter is slightly earlier).

| Pair | Witnora exact hybrid worker | Raw-CNF CryptoMiniSat worker | Witnora wall | CryptoMiniSat wall |
|---|---:|---:|---:|---:|
| 1 | **3,123.00 ms** | 4,239.17 ms | 3,152.08 ms | 4,247.76 ms |
| 2 | **3,629.65 ms** | 4,329.17 ms | 3,659.19 ms | 4,336.94 ms |
| 3 | **3,567.21 ms** | 4,183.09 ms | 3,595.58 ms | 4,190.53 ms |
| Mean | **3,439.95 ms** | 4,250.48 ms | **3,468.95 ms** | 4,258.41 ms |

The observed worker-time reduction is **19.1%**; including process overhead
and full-model checking, wall-time reduction is approximately **18.5%**.
This is a narrow repeatable advantage on this one instance, **not** a
population-level statistical claim across SAT problems or machines.

## Matched transformed strong-baseline check

The earlier affine-quotient implementation reduces source equations and
feeds the projected CNF to the same CryptoMiniSat engine. Two additional
interleaved pairs yielded:

| Pair | Witnora exact hybrid worker | Affine quotient + CryptoMiniSat worker |
|---|---:|---:|
| 1 | **3,330.80 ms** | 4,190.94 ms |
| 2 | **3,447.00 ms** | 4,045.90 ms |

The hybrid also won both transformed-baseline comparisons. Historical raw
CryptoMiniSat controls from the preceding research gate were
**3,778.14/4,045.28 ms** and affine controls **4,017.65/3,916.35 ms**:
the present result is directionally consistent, though not a large dataset.
After adding exact ROBDD cardinality diagnostics, a further independent
verified hybrid run took **3,664.35 ms** (full worker).

## Verification and reproduction

Offline exhaustive tests compare ROBDD OR, XOR-coordinate translation,
intersection, membership, exact cardinality, chosen witnesses, and the
BDD-to-CNF gate against every pattern of toy syndromes. Factor DP is checked
against independent brute-force clauses and local XORs, with and without
boundary conditioning. A separate regression reconstructs sparse witnesses
and counts; a negative test checks the holdout is rejected before fetch.

All **47 relevant regression tests pass** (39 pre-existing and 8 new).

```sh
python -m unittest \
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

# Winning source-checked hybrid (30 s all-in worker cap):
python scripts/experiment_satlib_symbolic_syndrome_bdd.py --budget 30

# Honest ablations, including resource-cap UNKNOWN outcomes:
python scripts/experiment_satlib_symbolic_syndrome_bdd.py --one-sided --budget 30
python scripts/experiment_satlib_symbolic_syndrome_bdd.py --two-sided --budget 30
python scripts/experiment_satlib_symbolic_syndrome_bdd.py --bdd-gated --budget 30

# Competing source-exact CryptoMiniSat arms:
python scripts/experiment_satlib_cryptominisat_gate.py \
  --modes raw_cnf affine_quotient --timeout 12 --repeats 2
```

The source command requires the pinned `pycryptosat==5.17.0` environment and
the project's existing SATLIB source downloader. Deterministic output
includes the immutable SHA, source model digest, and all charged phase times.

## Scientific decision and next gate

**Retain this as a promising single-instance algorithmic lead in draft
PR #119; do not publish a breakthrough claim or open the sealed holdout.**

1. Freeze the operator and its source-independent logic before cross-family
   validation. Test on multiple official source families and independently
   generated/adversarial formulas, checking complete original models, widths,
   memory caps, and unsolved `UNKNOWN` cases without cherry-picking.
2. Compare against additional current CDCL/XOR-aware solvers in reproducible
   environments, with all transformation and verification time included.
3. Look for a *new*, provable compression invariant or scaling theorem and
   discharge Lean/Python refinement obligations before making a mathematical
   novelty claim. This experiment alone does not establish one.

Relevant prior art makes the originality boundary clear: decision diagrams
and semiring-valued dynamic programming are established, including
[decision diagrams for semiring valuations](https://research.ucc.ie/en/publications/decision-diagrams-for-the-computation-of-semiring-valuations/)
and [ADDMC algebraic decision-diagram model counting](https://arxiv.org/abs/1907.05000).
The single-thread solver baseline is [CryptoMiniSat](https://github.com/msoos/cryptominisat).
