# R-001/R-002: Native Rust indexed exact-counting migration

Status: **green Rust build, Rust native tests, Python differential
integration, independent Ganak benchmark, and full pre-existing
W-CRC regression CI**. This is the first working native Rust
**component** replacement, not a complete rewrite of Witnora
and not a new complexity theorem.

Verified dedicated Rust/PyO3 workflow:
https://github.com/joeyst8/witnora-core/actions/runs/41730735431

Independent legacy W-CRC 105-test gate:
https://github.com/joeyst8/witnora-core/actions/runs/41730735450

## Exact implementation boundary

- `rust/witnora-ve/src/lib.rs` implements ordinary exact
  sum-product indexed variable elimination over signed source
  clauses. Factor incidence and versioned min-scope heap are
  deterministic. Arbitrary-size `BigUint` counts preserve
  n=256 Fibonacci/Lucas outputs exactly.
- `rust/witnora-ve/src/main.rs` accepts a strict explicit-variable
  text protocol, outputs `EXACT` plus count/operations/width
  or `INCOMPLETE`; malformed input is rejected.
- An optional PyO3 extension exposes `count_component_native`
  **in-process**, returning the exact integer as decimal text
  to avoid truncated 64-bit FFI values.
- `witnora_core/crc_rust_bridge.py` converts source-checked
  normalized Python clause-violation masks to Rust signed CNF.
  It prefers the in-process native extension when installed,
  otherwise a configured CLI binary. Missing binaries cause
  explicit configuration errors, not hidden Python fallback.
- `witnora_core/crc_cutset_count.py` now admits the opt-in
  `component_backend="variable_elimination_rust"`, while the
  legacy default `enumeration` stays unchanged.

This is a **new untrusted native execution path**. It does not
prove its own count or replace Lean TC-063 kernel certificates.
The exact count has been independently tested on bounded controls.

## Verification and adversarial checks

- Five compiled Rust tests passed, including 240 deterministic
  signed random small CNF differential cases versus exhaustive
  reference, noncontiguous variable IDs, tautologies, UNSAT,
  malformed inputs, factor-width and operation-budget refusal,
  and an n=256 big-integer Fibonacci count.
- Five Python/Rust integration tests passed, including
  **150 more seeded signed random** exact differential cases
  checking both the count and the **same factor-operation work**
  against the frozen W-CRC-015 indexed reference.
- Direct Rust-in-process versus Rust-CLI equivalence checks,
  plus exact cutset-source integration on signed chains/rings,
  passed.
- Eight larger n=16/64/128/256 chain/ring cases matched
  **analytic Fibonacci/Lucas counts** and an independently
  executed Ganak 2.8.0 counter. Source and factor-operation
  accounting agree with the Python reference on every case.
- The existing broader **105-test** Python W-CRC gate remains
  green. Source defaults, Lean modules, TC-063 #121, and
  production trust gates were not altered.

No general arbitrary SAT/#SAT superiority or soundness theorem
is inferred from finitely many matching test results.

## Complete end-to-end component pilot (R-002)

Times in milliseconds, medians of three complete calls on one
GitHub Actions runner. `Rust binding` includes the in-process
Python-to-Rust conversion and call. `Rust CLI` also includes
creating a fresh child process. No external SAT-witness step
or full cutset discovery is included.

| Family | n | Python indexed VE | Rust in-process binding | Rust fresh subprocess |
|---|---:|---:|---:|---:|
| chain | 16 | 0.2509 | 0.0931 | 1.0387 |
| ring | 16 | 0.3855 | 0.0856 | 1.0696 |
| chain | 64 | 1.1494 | 0.6533 | 1.5259 |
| ring | 64 | 1.6532 | 0.6661 | 1.5864 |
| chain | 128 | 3.0358 | 2.1763 | 3.1620 |
| ring | 128 | 3.9401 | 2.2864 | 3.2420 |
| chain | 256 | 8.7981 | 7.8111 | 9.1697 |
| ring | 256 | 10.5852 | 8.1516 | 9.1637 |

In-process Rust was **about 1.1–4.5x faster** than the
Python reference on these eight cases, but its advantage
decreased as n grew. A fresh Rust subprocess was often
slower, especially at n=16. This motivated and validated
the native binding, not a broad Rust superiority claim.
Three repetitions, a shared runner and limited families
do not support robust statistics.

All eight Ganak trials produced the matching exact integer.
Ganak's reported engine-only times on n=256 were ~93.3ms
for chain and ~137.0ms for ring, but these are not matched
whole-pipeline timings and its default cache has a small
probabilistic collision qualification.

## What was NOT migrated

- Most Python feature engineering, source parsing, witness
  acquisition, cut discovery, experiment scripts and SAT/#SAT
  prototype algorithms remain Python.
- The Lean source-bound G14/G5/TC-063 proofs and kernel checker
  remain **Lean**, intentionally.
- The R-002 Python extension is only a native implementation
  of the existing conventional VE algorithm.
- There is no proof-producing count certificate format yet
  for **arbitrary** Rust model-count results.
- We have not compared peak memory or broad external industrial
  benchmark suites.

## Next engineering checkpoints

1. Make the native Rust backend the actively evaluated reference
   for accepted cutset components on a larger held-out suite,
   while retaining the frozen Python fallback for differential
   checks and never silently substituting it on Rust errors.
2. Port source-level consensus/unit normalization and count
   its **complete preprocessing time**, keeping source
   equivalence checks and fail-closed behavior.
3. Optimize avoidable allocations/BigUint operations in Rust,
   then repeat statistically controlled timing and memory tests.
4. Build a signed-source certificate format independently
   checkable in Lean. Generated native results are not trusted
   merely because Rust is memory safe.
5. Only after parity, robustness and proof-gate requirements
   should further Python modules be retired or defaults changed.

Research branch `research/w-crc-001-asymmetric-v1`,
draft PR #122; formal TC-063 draft #121 untouched.
