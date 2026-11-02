# PR #119: CryptoMiniSat strong-baseline and originality gate

**Decision: no breakthrough claim; no public release.** This record exists to
prevent the earlier weak-baseline comparison from being presented as proof of
a new mathematical operator. Affine elimination and parity-aware SAT solving
are well-established techniques.

## Purpose and locked source

Previous source-exact results showed that the affine quotient finds verified
SAT witnesses where MiniSat22 and CaDiCaL195 time out within seven seconds.
This is a legitimate local comparison but an inadequate state-of-the-art gate:
those solvers do not specialize in XOR constraints. This experiment adds the
XOR-aware CryptoMiniSat solver as a stronger control.

- Locked, historical DIMACS source: `par32-1-c.cnf.Z` at the [Rutgers archive](https://archive.dimacs.rutgers.edu/pub/challenge/satisfiability/benchmarks/cnf/).
- Original decompressed SHA-256:
  `5e3253738e729c3fda8cde22e67b6d8bae0df6d53e9afabb6bd74d5ceb700312`.
- Source input: 1,315 variables and **5,254 raw original clauses**.
- Every SAT result is independently decoded and checked against **all 5,254
  source clauses**. Failed checks raise an error, never count as SAT.
- Only this development file is accepted; **`par32-2-c` holdout is not run**.
- Solver: official `pycryptosat==5.17.0` binary wheel, single thread,
  no configuration tuning. See upstream [CryptoMiniSat](https://github.com/msoos/cryptominisat)
  and [Python XOR API](https://github.com/msoos/cryptominisat/blob/master/python/README.md).
- Each condition has **two sequential runs**, a **7-second** isolated worker
  wall cap, and charged construction + solver initialization + solving + model
  checking. Original download is outside all measured caps. Timeouts are
  `UNKNOWN_TIMEOUT`, not UNSAT.

## Three matched conditions

1. **Raw original CNF:** pass all original clauses to CryptoMiniSat. It may
   recover parity structure using its own preprocessing.
2. **Source-exact native XOR:** use the existing safe and complete detector,
   replace 4,632 proven XOR encoding clauses with 1,158 native equations,
   and keep all 622 residual clauses. Charge detection and construction time.
3. **Affine quotient:** eliminate the same 1,158 equations, keep the 157
   independent coordinates, encode 1,010 shared XOR gates plus the residual
   clauses as a 1,167-variable, 4,662-clause CNF, feed that to the **same**
   CryptoMiniSat, and charge the transformation in full.

This compares *representations on one backend*, avoiding a misleading
"different algorithms and different backends" claim.

## Results: original-source models all verified

| Method | Status, both runs | Total worker, ms (runs 1 / 2) | Preparation, ms (runs 1 / 2) | Search + solve overhead, approx. ms (runs 1 / 2) |
|---|---|---:|---:|---:|
| **Raw original CNF** | SAT / SAT | **3,778.14 / 4,045.28** | 2.03 / 4.55 | 3,776.11 / 4,040.73 |
| Source-exact native XOR | SAT / SAT | 5,039.54 / 5,455.85 | 2,520.57 / 2,655.94 | 2,518.97 / 2,799.91 |
| **Affine quotient** | SAT / SAT | **4,017.65 / 3,916.35** | 2,720.14 / 2,675.67 | 1,297.51 / 1,240.68 |

Wall time (including child creation) follows the same pattern: raw
3,785.87 / 4,053.33 ms; native XOR 5,046.82 / 5,464.08 ms; quotient
4,025.94 / 3,925.47 ms. Neither quotient nor native-XOR extraction
delivered a convincing **end-to-end** advantage over the unmodified source.
The quotient's approximate mean worker time is 3.97 s, versus 3.91 s for
raw CryptoMiniSat. Two runs cannot establish a statistically significant
small difference either way.

**Interesting lead, not a discovery:** after Python preprocessing, the
quotient required about 1.24–1.30 s to solve versus 3.78–4.04 s for raw
CryptoMiniSat. But the approximately 2.7 s preprocessing cost **must not be
discarded**. A substantially faster detector would make this established
method's performance more competitive; this is an engineering hypothesis to
test, not evidence of new mathematics.

Supplying 1,158 equations as native XOR helped CryptoMiniSat's post-setup
search compared with its original-CNF run, but detection overhead made it
slower end-to-end. This is a warning against cherry-picked solver-only times.

## Implementation and verification

Sources:

- `scripts/experiment_satlib_cryptominisat_gate.py` — source digest gate,
  exactly three representations, subprocess time cap, source-model audit,
  reproducible mode and repeat CLI.
- `tests/test_satlib_cryptominisat_gate.py` — original-model SAT checks for
  every mode on a synthetic source, exhaustive 2^4 truth-table equivalence
  of source-exact XOR partition, and holdout-lock regression.

```shell
PYTHONPATH=/tmp/witnora_cms_deps:/tmp/witnora_bench_deps:. \
  python -m unittest tests.test_satlib_cryptominisat_gate \
  tests.test_satlib_affine_quotient tests.test_real_satlib_parity_gate \
  tests.test_verified_flip_orbits -v

PYTHONPATH=/tmp/witnora_cms_deps:/tmp/witnora_bench_deps:. \
  python scripts/experiment_satlib_cryptominisat_gate.py \
  --timeout 7 --repeats 2
```

`pycryptosat==5.17.0` should be installed in an isolated environment as
documented by upstream. The `/tmp/witnora_cms_deps` path is just this run's
temporary dependency location, not a committed package or reproducibility
requirement.

## Scientific decision and next gate

- **Reject** "new SAT mathematics" and "beats the best solvers" claims.
- **Keep** the reproducible matched comparison in the research-only draft.
- **Do not open** the `par32-2-c` holdout yet. Freeze a novel nonlinear
  residual-coupling hypothesis and controls *before* first operator run on
  that source.
- Require multiple independent problem families and meaningful wins over
  CryptoMiniSat (and other strong modern baselines), using all-in timing and
  verified models. A one-instance win is insufficient.
- Continue Lean soundness work separately; a faster solver and a formal
  correctness theorem are different achievements.

Relevant prior research: [Preprocessing in SAT Solving](https://cca.informatik.uni-freiburg.de/papers/BiereJarvisaloKiesl-SAT-Handbook-2021-Preprocessing-Chapter-Manuscript.pdf)
and [Extending Clause Learning SAT Solvers with Complete Parity Reasoning](https://arxiv.org/abs/1207.0988).
