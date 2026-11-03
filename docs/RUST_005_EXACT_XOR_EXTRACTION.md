# R-005: Exact source XOR recognition ported from Python to Rust

Status: **verified opt-in migration**, on research branch
`research/w-crc-001-asymmetric-v1` and draft PR #122.
The Lean TC-063 draft PR #121 is unchanged; no merge to main.

[Verified independent Rust/PyO3 GitHub Actions run #41738553647](https://github.com/joeyst8/witnora-core/actions/runs/41738553647)

## Why this port is mathematically sensitive

The legacy `witnora_core/crc_source.py` source adapter recognizes
complete canonical k-variable XOR clause encodings only when
**every clause banning the incorrect parity assignment is present**.
An incomplete collection must remain a literal CNF. Inventing
even one missing parity equation changes the satisfying assignments
and can silently produce a wrong #SAT result.

The Rust port implements the same criterion for k=1,2,3:

- Canonicalize signed clauses while dropping tautologies and exact
  duplicates; preserve explicit n-variable source universe.
- Build deterministic supports (variable sets) for source clauses
  of width 1..3.
- For each support and each RHS parity 0/1, construct the **complete**
  forbidden-assignment clause set. Extract the parity row only if
  the entire exact set is present in the remaining source.
- Remove exactly those extracted clauses. Retain all other clauses,
  including partial XOR groups and empty contradiction clauses.
- Encode row supports in arbitrary-precision Rust `BigUint` bit
  masks, sent through the PyO3 boundary as decimal strings so
  variables through ID 256 remain lossless.

The native `rust/witnora-ve/src/source_xor.rs` is exposed as
`extract_small_xors_native`. A strict Python adapter
`witnora_core/crc_rust_xor.py` returns the **same tuple of rows and
residual clauses** as `extract_exact_small_xors`.

The new option on `count_signed_cnf_crc` is
`source_extractor="rust"`; the default remains `"python"`.
The extractor is compatible with both `rust_consensus` and
`rust_adaptive` preprocessing modes and with the original
unpreprocessed path. Missing native binaries fail explicitly; there
is no silent fallback. Rust is not being treated as a Lean proof.

## Three independent correctness boundaries

The dedicated CI run confirmed:

1. **13 Rust tests passed**, including 245 small seeded randomized CNF
   **full satisfying-assignment-set** comparisons of extracted Rust
   XOR rows plus residual clauses to the original CNF.
2. **4 new Python integration tests passed**, including **280** seeded
   random CNFs (n=2..8) where Rust and Python extraction matched
   **byte-for-byte at the equation tuple/residual tuple level**,
   and every extracted result had exactly the same complete set of
   satisfying assignments as the input CNF. Explicit controls
   included missing XOR clauses, both contradictory parities,
   signed duplicates, empty clauses, malformed literals, and
   single-unit parity at variable 256.
3. **12/12** end-to-end source counts from both extractors matched
   the analytic answer of **2**, independently confirmed by Ganak
   on the *unsimplified original* source; in all 12 benchmark
   variants the Rust/Python source adapters agreed.

All benchmarks used identical **R-004 adaptive native source
preprocessing** in both the Python-extractor and Rust-extractor arms.
Thus the only software switch under comparison is the exact XOR
recognizer. Timings include preprocessing, source parsing,
cross-language conversion and the downstream exact coefficient
counter; they do not isolate the Rust kernel or exclude overhead.

## Full source-to-count timings

Two timed repetitions per arm on the same GitHub-hosted runner;
reported medians in milliseconds. Independent Ganak validates
each count but its engine timing is not directly comparable.

| n | Family | Python extractor + CRC | Rust extractor + CRC | Rust / Python |
|---:|---|---:|---:|---:|
| 8 | forcing | 0.9701 | 0.2187 | 0.225 |
| 8 | forcing + implied units | 0.6667 | 0.1446 | 0.217 |
| 8 | parity | 0.4685 | 0.1839 | 0.393 |
| 16 | forcing | 0.4953 | 0.3539 | 0.715 |
| 16 | forcing + implied units | 0.3842 | 0.2382 | 0.620 |
| 16 | parity | 1.6885 | 0.6754 | 0.400 |
| 32 | forcing | 1.5564 | 1.1789 | 0.757 |
| 32 | forcing + implied units | 1.0373 | 0.7737 | 0.746 |
| 32 | parity | 7.6051 | 3.3928 | 0.446 |
| 64 | forcing | 5.4337 | 4.5911 | 0.845 |
| 64 | forcing + implied units | 3.2675 | 2.7441 | 0.840 |
| 64 | parity | 38.0817 | 21.0635 | 0.553 |

The n=64 parity whole-pipeline case was about **1.81× faster**
with the Rust XOR extractor, preprocessing included. The n=64
forcing case improved by only ~1.18× because the adaptive
simplifier had already reduced the CNF to 63 units before either
extractor ran. Some smaller cases had larger ratios, but two
repeats on one shared machine are inadequate to claim an
out-of-sample stable speedup. Results do not imply general
SAT/#SAT improvement or new mathematical complexity results.

## Remaining Python and Lean boundaries

Witnora now implements **three distinct native Rust operations**:

1. Bounded indexed exact factor variable-elimination component
   counting (R-001/R-002).
2. Exact model-set-preserving source simplification with optional
   binary-sign admission (R-003/R-004).
3. Exact extraction of complete small XOR clause gadgets (R-005).

Python still owns the remaining source orchestration, separator
selection, affine/coefficient engine, research queue and regression
reference. Lean still owns its independent formalization/checker.

Next target: profile and port an **end-to-end coefficient-engine
subcomponent** (rather than additional per-stage bindings), retain
hard resource caps and independently compare operation budgets and
complete counts across held-out sources. Re-evaluate CPU memory,
Python↔Rust serialization, and whether a single native source-to-count
entry point is more effective than many small crossing calls.

The research queue is not self-modifying and does not send updates to
a closed ChatGPT conversation.
