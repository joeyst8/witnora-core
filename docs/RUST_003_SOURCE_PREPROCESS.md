# Rust R-003: Exact source-preserving consensus and unit normalization

Status: **green native Rust/PyO3 integration**, **9 Rust unit tests**,
**4 new Python source-preprocessing tests**, **12/12 Ganak exact-count
matches**, and all three previously refusing W-CRC-019 redundant-unit
families now counted exactly when native preprocessing is enabled.

Verified dedicated Rust source-preprocessing workflow:
https://github.com/joeyst8/witnora-core/actions/runs/41736318985

## Why the change matters

W-CRC-019 established that adding mathematically redundant explicit
unit clauses to a dense 2-CNF forcing family made the original
Python source/CRC backend refuse n=16/32/64 under its **4,096
Fourier-mode budget**. Independent Ganak still counted 2 models,
and the raw forcing CNF had the same two solutions.

The fault was not an intrinsic hardness barrier. The source syntax
was obscuring elementary Boolean reductions. R-003 now executes
those reductions in **native Rust before the existing source
adapter's affine extraction and Fourier expansion**.

## What the Rust code does

`rust/witnora-ve/src/source_preprocess.rs` performs:

1. Validation, deterministic clause canonicalization, removal
   of tautologies and duplicate literals/clauses.
2. Exact unit propagation **while retaining unit clauses** so the
   set of complete satisfying assignments is unchanged.
3. Batch disjoint consensus replacements:
   `(A OR x) AND (A OR NOT x) <=> A`.
4. Repeats to a stable point under explicit pass/clause-visit caps,
   otherwise returns `INCOMPLETE` instead of an unjustified count.

These operations are **standard Boolean resolution and
simplification**, not a novel algebraic discovery. The input's
original variable universe is preserved (including unconstrained
variables), so the result is assignment-set equivalent rather
than merely equisatisfiable or equivalent after existentially
hiding helper variables.

Rust's `simplify_source_native` PyO3 interface is wrapped by
`witnora_core/crc_rust_preprocess.py`. The source-counting
adapter supports explicit opt-in
`source_preprocessor="rust_consensus"`, with the original
`"none"` default unchanged.

The preprocessing limit is independent of the downstream
Fourier/inclusion-exclusion/Shannon limits. Missing native
binaries and malformed input are explicit errors; ordinary
budget exhaustion returns `None`, never a guessed SAT/UNSAT
answer.

## Exact independent verification

- **280 deterministic random source CNFs** at n=2..8 were
  exhaustively compared at the Rust-library level for their
  **entire satisfying-assignment set**, including empty
  clauses, duplicate literals and tautologies.
- Another **200 seeded source CNFs** at n=3/4/5/6/8 were
  checked by Python against the same full assignment sets
  and an independent brute-force #SAT evaluator.
- Explicit contradictory-unit, out-of-range literal,
  tautological, unbounded-visit and insufficient-pass
  negative controls passed.
- The source-CRC integration counts both the original
  forcing and unchanged parity families exactly.
- The 12 benchmark instances all matched independent Ganak
  exact counts of **2 models**.

No Lean kernel proof of the native transformation has yet
been written. Finite exhaustive tests are evidence, not
a universal formal-equivalence theorem.

## Complete end-to-end source-to-count benchmark

All timings below include full source parsing, Rust PyO3
preprocessing when selected, the exact CRC source adapter
and coefficient counting. Two timed repetitions per
method on one hosted runner; Ganak independently checked
all 12 results.

| n=64 source family | Source clauses | Rust-simplified clauses | Untouched CRC | Rust preproc + CRC |
|---|---:|---:|---:|---:|
| pairwise forcing | 4,032 | 63 | 185.0303 ms exact | 3.3957 ms exact |
| forcing + implied units | 4,095 | 63 | INCOMPLETE_BUDGET | 1.5545 ms exact |
| complete pairwise parity | 4,032 | 4,032 | 18.3167 ms exact | 23.2748 ms exact |

The forcing baseline improved by **54.5x on this particular
controlled family**, with preprocessing **included**.
The three previous redundant-unit refusals at n=16/32/64
now returned exactly 2 models. This is a genuine
representation-sensitive prototype repair.

However, the full parity source did not admit any consensus
pair; scanning it for reductions added ~27% time at n=64.
A future source profiler/admissibility gate must avoid
invoking the simplifier on families unlikely to benefit.
Two repeats are not statistically sufficient to assert
a stable speed ratio under differing runner contention.

For completeness, forcing baseline n=8/16/32 raw vs native
were 0.6676/0.2934, 3.5583/0.2600, and 23.8279/0.7769 ms.
The implied-unit variant n=16/32 went from incomplete
to exact in 0.1862/0.4776 ms respectively.
All results are from one small family, not a general
SAT/#SAT performance victory.

## Migration and proof boundary

This is now the **second native Rust computational operation**
alongside indexed factor variable elimination:

- Rust: exact source-preserving preprocessing and indexed
  variable-elimination component kernel.
- Python: experiment harness, some source adapters, separators,
  alternative counters and regression reference.
- Lean: untouched TC-063 proof and certified checker modules.

The native Rust result is not automatically a verified
mathematical proof. A future Lean checker could independently
validate a transformation certificate containing individual
consensus pairs and unit-reduction steps. Until then, rely
on exact limited tests and comparisons, not an inflated
formal-refinement claim.

Next stages:
1. Establish a cheap, independently checked admission rule
   for source preprocessing to avoid parity-family overhead.
2. Port more source normalization/structural decomposition
   into Rust, with full model-count differentials and
   source-witness cost included where appropriate.
3. Preserve a source-level certificate format suitable for
   Lean verification; retain all current formal trust gates.
4. Increase held-out source-family coverage and measure peak
   memory, not just 2-run wall times.

Research branch: `research/w-crc-001-asymmetric-v1`,
draft PR #122, stacked on TC-063 #121. Nothing was
merged to main.
