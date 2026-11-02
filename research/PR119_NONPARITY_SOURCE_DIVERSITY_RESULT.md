# PR #119: Preregistered non-parity gate — 0/4 symbolic coverage, independent XOR refutation lead

**Honest negative scientific gate.** Before seeing the four sources or their
solver timings, the exact names, truth expectations, no-tuning rule and
evaluation contract were saved to draft PR #119 in
`PR119_NONPARITY_PRECOMMITTED_PROTOCOL.md`, commit
`e31d2036d338218094a48702b8a9c48031ba8bcc`. The locked source-diversity
suite exposed a real limitation: **the successful 16/32-bit PARITY syndrome
ROBDD/sparse operator is applicable to 0/4 unrelated DIMACS sources**.
All four sources were solved by an ordinary SAT backend after the failed
structural gate. There is no general-purpose algorithmic speedup evidence.

An unexpected exact-source XOR contradiction in the unsatisfiable Dubois20
benchmark was independently validated and preserved as a **separate,
checkable candidate for the Lean formal-certification track**. Its algebra is
standard, and it is **not yet Lean kernel-checked**.

## Frozen sources and correctness boundary

Official source URLs are `https://archive.dimacs.rutgers.edu/pub/challenge/satisfiability/benchmarks/cnf/<name>`.
The sources are unmodified historical DIMACS compressed archives. Each was
downloaded, decompressed using `uncompress -c`, parsed with the original
strict DIMACS reader, and hash-checked *before* solver workers executed.

| Family | Precommitted source | Original vars / clauses | Known result | Decompressed SHA-256 |
|---|---|---:|---|---|
| Pigeonhole | `hole8.cnf.Z` | 72 / 297 | UNSAT | `e63ad9adca73c42dab2f89a3cec77dbf7800d595f72ce740b32004431e1bfd84` |
| Dubois | `dubois20.cnf.Z` | 60 / 160 | UNSAT | `82059aba0e5773644b386eb6bcbe53680655390cb041873a3cb3e93f7bd896a7` |
| AIM | `aim-50-1_6-yes1-1.cnf.Z` | 50 / 80 | SAT | `d96f1edb1db3d0e55a3ff0f7707517e41a79374acbb857df051e5441ab27657d` |
| AIM | `aim-50-1_6-no-1.cnf.Z` | 50 / 80 | UNSAT | `c0441193ae63b66e71461248e82273805f7194123263314ae73f318cdfa78b9d` |

The parity holdout **`par32-2-c` was never opened** and is forbidden by the
new input allowlist. The four independent cases include SAT and UNSAT
answers; UNSAT from the fallback is credited only to the completed
CryptoMiniSat backend, not to the unsupported symbolic operator.

## All completed paired trials (post infrastructure repair)

Two sequential trials per source, one thread, `pycryptosat==5.17.0`;
source download and original DIMACS parsing excluded from both worker arms.
Witnora portfolio time includes source-exact XOR detection, structural
eligibility analysis, original-CNF backend setup, solving and source-model
verification when SAT. The same raw clauses go directly to the unmodified
CryptoMiniSat baseline. Timed worker and process-wall records are retained;
no timeouts or bad source models occurred in the repaired suite.

| Case / trial | Frozen structural finding | Witnora portfolio worker | Plain CryptoMiniSat worker | Outcome |
|---|---|---:|---:|---|
| Pigeonhole 1 | Unsupported (2.20 ms) | **398.76 ms** | 464.35 ms | Backend UNSAT |
| Pigeonhole 2 | Unsupported (2.89 ms) | 481.92 ms | **425.02 ms** | Backend UNSAT |
| Dubois 1 | Potential XOR contradiction (5.17 ms) | 25.77 ms | **24.19 ms** | Backend UNSAT |
| Dubois 2 | Potential XOR contradiction (4.39 ms) | 22.93 ms | **20.44 ms** | Backend UNSAT |
| AIM SAT 1 | Unsupported (1.13 ms) | 28.01 ms | **21.86 ms** | Original SAT witness verified |
| AIM SAT 2 | Unsupported (1.02 ms) | 25.60 ms | **25.39 ms** | Original SAT witness verified |
| AIM UNSAT 1 | Unsupported (1.90 ms) | 32.97 ms | **26.14 ms** | Backend UNSAT |
| AIM UNSAT 2 | Unsupported (1.12 ms) | 30.14 ms | **27.54 ms** | Backend UNSAT |

The pigeonhole pair reverses the timing order between repetitions, showing
ordinary noise. The other families show either nearly tied or moderately
worse fallback times; no case exercises the symbolic syndrome operator.
**Applicability score = 0/4.** No source-level factoring scheme was
post-hoc modified to make the operator fit these formulas. This falsifies
the hope that the existing special-purpose right-ROBDD/left-sparse solver
already behaves as a broadly applicable SAT accelerator.

### Corrected benchmark infrastructure, recorded explicitly

The **initial** four-case timing attempt used an older CryptoMiniSat wrapper
written specifically for the known-SAT historical PARITY source. It threw
`AssertionError('UNSAT contradicts official SAT source')` on correct UNSAT
answers, making the original UNSAT timing records unusable as baseline
comparisons. In that same initial run, the Dubois XOR extractor stopped at
a source contradiction and the portfolio returned `ERROR`. These are
**harness errors/diagnostics, not solver failures and not data to hide**.

The **repair** did not change the frozen symbolic operator or evaluation
sources: a new raw-CNF baseline wrapper accepts and reports both SAT and
UNSAT; the portfolio reports the discovered Dubois structural contradiction
as `POTENTIAL_UNAUDITED_XOR_CONTRADICTION` and still calls the complete
backend before claiming UNSAT. The corrected suite was rerun end-to-end,
and its complete results appear above. No advantage is claimed from the
infrastructure correction.

## Separately verified Dubois20 XOR contradiction

This is a proof-certificate **lead** for Track A, not a new operator win in
the preregistered benchmark. The original `dubois20` has 60 variables and
160 clauses. Independent source inspection found **40 exact three-variable
XOR equations**, each encoded by four original source clauses; their
complete source-clause union contains all **160** original clauses.

The extractor's equation proposals are treated as untrusted. A separate
checker, `scripts/audit_satlib_dubois_xor_contradiction.py`, receives an
explicit equation/associated-clause list. It independently:

1. Checks every proposed source clause belongs to the original normalized
   CNF and uses only its stated row variables.
2. Enumerates every truth assignment to those three variables and proves
   the conjunction of the four source clauses is true **if and only if**
   the stated XOR equation holds. This source equivalence is checked for
   every row; no detector correctness claim is accepted blindly.
3. XORs the selected equations directly and confirms their entire variable
   coefficient vector is zero while the combined right-hand side is one:

   `0 XOR 0 XOR ... XOR 0 = 1` over GF(2), i.e. **`0 = 1`**.

All **40 equations** participate in the certificate. Its full source-bound
row list and signed clause subsets are archived in
`research/PR119_DUBOIS20_SOURCE_XOR_CERTIFICATE.json`, with original SHA.
An offline regression can load that JSON, recheck the row truth tables and
the final contradiction, and reject corrupted clauses or right-hand sides.
The script can also re-download the pinned official original source and
check the certificate against it.

**Proof status:** exact finite source-level algebraic verification in
Python; **NOT** a Lean 4 kernel-checked theorem, universal extractor proof,
or complete TC-063 UNSAT theorem. Dubois20 is an old benchmark based on
XOR-like constraints; finding parity inconsistency here is **not novel**.
Nevertheless, the portable original-clause proof is a concrete candidate
to run through the future shared-row indexed Lean checker.

## Reproduce and regression

```sh
# The exact fixed non-PARITY suite, including both SAT/UNSAT cases:
python scripts/experiment_satlib_nonparity_diversity_gate.py \
  --repeats 2 --budget 12 --compact

# Independent, source-pinned full Dubois contradiction audit:
python scripts/audit_satlib_dubois_xor_contradiction.py
python scripts/audit_satlib_dubois_xor_contradiction.py --full-certificate

python -m unittest \
  tests.test_satlib_nonparity_diversity_gate \
  tests.test_satlib_dubois_xor_contradiction \
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

**65 relevant offline regression tests pass**, including the newly
archived real-source XOR certificate audit. The original operator and its
successful parity source were not modified during this validation.

## Gate decision and next research action

**Reject the general-purpose speed/coverage claim** for this operator:
we have exact wins on a narrow old parity-learning family, but 0/4
coverage on an independently precommitted diversity suite. The fallback
portfolio has no repeatable new value beyond the established solver.

**Retain the Dubois certificate as an independently checkable algebraic
artifact.** The highest-value next milestone is to translate its small
source-exact XOR-CNF equivalence and GF(2) contradiction into Lean 4 and
kernel-check it from the actual parsed source and indexed proof rows.
That would be a measurable contribution to mathematical trust, even if it
does not improve SAT speed. Continue to seek genuinely distinct and novel
operators separately; do not claim world-changing research before those
math and generalization gates clear.
