# PR #119: Indexed incremental parity-syndrome oracle — exact but no established speedup

**Status: research draft; publication/novelty gate remains closed.** This
follow-up to the source-bound separator/MITM study replaces enumeration of
the larger side with an incremental native-XOR SAT oracle. It constructs and
checks a full witness of the historical original SATLIB instance, but the
matched strong-baseline timings do not show a reliable advantage. Incremental
assumption solving, failed-assumption clauses, XOR SAT, and syndrome matching
are established techniques, not a newly discovered mathematical foundation.

## Source lock and mathematical contract

- Official original `par32-1-c.cnf.Z` DIMACS SHA-256:
  `5e3253738e729c3fda8cde22e67b6d8bae0df6d53e9afabb6bd74d5ceb700312`.
- **1,315 source variables and 5,254 source clauses.** Extraction from exact
  complete source CNF encodings yields 1,158 XOR equations. Elimination of
  XOR-only variables leaves 375 residual variables, 622 ordinary clauses,
  186 local width-3 XORs, and 32 global syndrome equations.
- A verified three-variable separator `{184, 186, 188}` splits local factors
  into two 186-interior-variable sides. All eight boundary-conditioned
  counts are independently computed by exact integer bucket elimination;
  their join count is **704,494,193**. The experiment selects boundary mask
  `1`, where the left side has 4,992 local models and the right 40,920.
- Source-faithful global equations have the form
  `XOR(left_i) XOR XOR(boundary_i) XOR XOR(right_i) = rhs_i`.
  Each of the 32 equations is exact over GF(2); no manually supplied
  syndrome RHS, oracle witness, or hidden source solution is used.
- **Sealed holdout:** `par32-2-c` is never fetched, examined or tuned here;
  the command rejects that source before any network call.

## Experiment: a 32-bit assumption oracle with forbidden-cube memoization

1. Enumerate valid assignments to the smaller side with a single incremental
   solver and blocking clauses, preserving the three boundary bits.
2. Construct a *single* CryptoMiniSat solver for the larger side. For each
   global parity row introduce an indicator variable `y_i` and a native XOR
   constraint `y_i XOR XOR(right-interior variables in row i) = 0`.
   Assumptions on the 32 indicator literals query a required syndrome without
   recreating or re-solving a freshly encoded right-hand formula.
3. For every left assignment compute the complementary 32-bit syndrome.
   If the right oracle answers SAT, combine the sides and reconstruct all
   auxiliary source variables by GF(2) elimination. **Verify the complete
   1,315-variable model on every one of the 5,254 original raw clauses**.
4. If the oracle answers UNSAT, inspect its falsified-assumption conflict
   clause. Translate its *negated assumption* literals into a forbidden
   syndrome cube `(mask, value)`; reject unexpected literals/signs rather
   than risk unsound cache inference. A cube excludes all signatures `s`
   with `(s & mask) == value`. This is a sound generalized no-good, not a
   proof of UNSAT for the entire original instance.
5. Compare no cache, a linear list of subsumption-pruned cubes, and a
   dictionary indexed by exact cube masks. The indexed version performs
   one constant-time membership check per distinct mask, with no weakened
   mathematical condition. Preserve every negative result and timeout.

**Important performance repair:** The first prototype detected the 1,158
source XOR equations again when reconstructing the winning auxiliary model.
The final version explicitly reuses those already-extracted *exact source*
equations. This removes duplicated source work without changing the oracle,
model, or source verification. An offline regression checks fresh and reused
equation reconstruction agree.

## Real-source results

All source preparation, exact conditional counts, solver setup, enumeration,
32-bit queries, model reconstruction and full source verification are charged
to the solver worker. Network download is excluded equally for each arm.
Single-thread `pycryptosat==5.17.0`; all experiments use the identical
original source and have a 30-second isolated oracle-worker cap. Times can
vary with machine load; these are not statistically established speedups.

| Method / run | Charged worker time | Right-side queries | Sound cache skips | Final result |
|---|---:|---:|---:|---|
| Oracle, no core cache, before equation-reuse repair | 8,664 ms | 4,072 | 0 | SAT, verified |
| Oracle, linear core cache, before repair | 8,704 ms | 2,017 | 2,055 | SAT, verified |
| Oracle, mask-indexed core cache, before repair | 7,672.51 ms | 2,017 | 2,055 | SAT, verified |
| **Mask-indexed + equation reuse**, run 1 | **4,156.17 ms** | 2,017 | 2,055 | SAT, verified |
| **Mask-indexed + equation reuse**, run 2 | **4,901.60 ms** | 2,017 | 2,055 | SAT, verified |
| **Mask-indexed + equation reuse**, run 3 | **5,057.86 ms** | 2,017 | 2,055 | SAT, verified |
| Plain original-CNF CryptoMiniSat (recent matched run 1) | 4,671.80 ms | n/a | n/a | SAT, verified |
| Plain original-CNF CryptoMiniSat (recent matched run 2) | 4,280.09 ms | n/a | n/a | SAT, verified |

Earlier source-gated CryptoMiniSat control runs were about **3.78–4.05 s**.
The latest two controls were 4.28–4.67 s. Against all these runs the
experimental oracle is **not reliably faster**. Source preparation alone
consumed about 2.59–3.11 s in the three final oracle runs, whereas original
CNF CryptoMiniSat setup requires only a few milliseconds. An isolated 4.16 s
result is **not** evidence of a strong-baseline win.

Every successful oracle run examined exactly **4,072 small-side local models**,
queried exactly **2,017 complementary right syndromes**, and skipped another
**2,055** on sound conflict-cube implications. The indexed representation
stored **2,016 unique forbidden cubes under only 16 distinct bitmasks**;
1,808 conflict explanations specified 31 of the 32 syndrome bits. The
represented infeasible set is exact *as learned*: it is a sound, incomplete
collection of no-goods, not a compressed closed-form characterization of
all 2^32 possible right syndromes.

All completed oracle runs recovered the **same fully verified original model**,
Boolean-vector SHA-256:

`515c7dabc059ff203d550e1f37b2b249dd556b4746b690cdfd56589015095bbf`

The sorted true-variable IDs are preserved in the previously reviewed
`research/PR119_PAR32_1_MITM_VERIFIED_WITNESS.json` (603 positive variables).
No extra witness from a planted construction has been introduced.

## Repeatable tests and commands

After installing the pinned dependencies into a suitable Python environment:

```sh
python -m unittest \
  tests.test_satlib_incremental_syndrome_oracle \
  tests.test_satlib_syndrome_mitm \
  tests.test_satlib_residual_geometry \
  tests.test_satlib_residual_fourier \
  tests.test_satlib_local_nonlinear_bridge \
  tests.test_satlib_cryptominisat_gate \
  tests.test_satlib_affine_quotient \
  tests.test_real_satlib_parity_gate \
  tests.test_verified_flip_orbits -v

python scripts/experiment_satlib_incremental_syndrome_oracle.py \
  --indexed-cache --budget 30
python scripts/experiment_satlib_incremental_syndrome_oracle.py \
  --budget 30
python scripts/experiment_satlib_incremental_syndrome_oracle.py \
  --without-core-cache --budget 30
python scripts/experiment_satlib_cryptominisat_gate.py \
  --modes raw_cnf --timeout 12 --repeats 2
```

The benchmark checks the official decompressed source digest, has no route
to the sealed holdout, and reports only `SAT_VERIFIED_ORIGINAL` after the
raw clause audit. Worker timeouts and incomplete batch processing report
`UNKNOWN` and cannot be repackaged as UNSAT.

## Scientific decision

**Keep as a reproducible negative/engineering gate inside draft PR #119;
do not present or publish as new mathematics or a world-changing speedup.**
This is a compact incremental query interface for the 32-bit global
constraints, but still performs thousands of oracle calls; the compact
mask-index does not encode all feasible syndromes. More interesting future
work would be a verifiably exact *symbolic feasible-syndrome set* (e.g. a
validated decision diagram or tensor representation) with measured
build-and-query cost and cross-instance generalization. Any positive claim
must then beat unmodified strong solvers, include source preparation and
verification, survive a frozen holdout protocol, and clear a literature
novelty check. Exactness and speed are distinct questions.

Historical parity SAT solvers already used structural/two-phase reasoning:
see [AAAI 2000 equivalency reasoning](https://cdn.aaai.org/AAAI/2000/AAAI00-045.pdf)
and [CryptoMiniSat's native XOR/incremental API](https://github.com/msoos/cryptominisat).
