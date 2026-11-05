# Rust R-004: Exact adaptive source-preprocessing admission

Status: **verified** on research branch `research/w-crc-001-asymmetric-v1`,
draft PR #122; no merge and no change to TC-063 Lean proof files.

Dedicated verified Rust/PyO3 workflow:
https://github.com/joeyst8/witnora-core/actions/runs/41737533969

## Problem inherited from R-003

The exact native R-003 consensus simplifier can collapse a 4,032-clause,
64-variable forcing 2-CNF to 63 explicit unit clauses. Its prior
negative control was a pairwise parity 2-CNF with the same n and clause
count but **no direct consensus pairs**: it retained all 4,032 clauses
yet cost time to attempt simplification. Thus preprocessing should not
be unconditionally invoked on every source representation.

## Native admission heuristic

`rust/witnora-ve/src/source_preprocess.rs` now exports
`source_admission_heuristic`, which:

1. Validates every literal against the declared source variable universe.
2. Admits empty/unit clauses and clauses with length other than two
   for possible exact native normalization.
3. For ordinary binary clauses, groups by the two variable IDs and
   accumulates a four-bit polarity mask: ++, +-, -+, --.
4. Admits the source if any support contains two clause signs differing
   in precisely one literal, the prerequisite for direct consensus.
5. Otherwise returns false, permitting a no-op fast path.

The new PyO3 entry point is `simplify_source_adaptive_native`.
The Python source adapter accepts the **explicit opt-in**
`source_preprocessor="rust_adaptive"`; the default remains
`"none"`, and `"rust_consensus"` still forces complete bounded
simplification.

**Safety boundary:** The admission predicate is *only a heuristic for
when to spend preprocessing effort*, not a SAT test, complexity
measure or proof of global irreducibility. A false result may skip
other useful simplifications, such as eliminating duplicate clauses.
It never changes the meaning of a CNF: the false branch passes the
original clauses unchanged; the true branch uses the R-003 exact
model-set-preserving transformations. A too-small admission
clause-visit budget returns incomplete, not an unjustified answer.
A skipped source reports `passes=0` and
`RustSourceSimplification.skipped=True`.

## Independent verification

The dedicated Rust workflow passed:

- **10/10 Rust tests**, including new forcing/parity admission controls,
  malformed-literal rejection and the existing 280 randomized complete
  truth-table checks for exact R-003 transformation.
- **5/5 Python integration tests**, including 120 new seeded random CNF
  complete satisfying-assignment-set comparisons under adaptive mode,
  exact recovery on n=16/32/64 implied-unit cases, no-op identity on
  all parity cases and cap refusal checks.
- **12/12** `rust_adaptive` source-to-count results of 2, matching
  independent Ganak; **12/12** unconditional native exact counts.
- The old non-preprocessed source counter still returned
  `INCOMPLETE_BUDGET` on three logically redundant-unit encodings.

## End-to-end timings on verified hosted CI runner

All figures below are medians of **two timed source-to-count repeats**.
They include the full Python source adapter, the PyO3 call, the Rust
admission check, exact simplification if admitted, and downstream CRC
counting. These are not native-kernel-only times. Ganak was run
independently to validate the exact model counts; its timing is a
different engine metric.

| n | Source | Raw CRC (ms) | Always simplify (ms) | Adaptive (ms) | Adaptive skipped |
|---:|---|---:|---:|---:|---|
| 8 | forcing base | 0.9027 | 0.3620 | 0.1169 | no |
| 8 | forcing + units | 2.1568 | 0.1204 | 0.0910 | no |
| 8 | parity | 0.3099 | 0.3698 | 0.2915 | yes |
| 16 | forcing base | 4.8872 | 0.3508 | 0.2986 | no |
| 16 | forcing + units | incomplete | 0.2775 | 0.2169 | no |
| 16 | parity | 1.1313 | 1.2804 | 1.1627 | yes |
| 32 | forcing base | 33.4509 | 1.0913 | 1.0524 | no |
| 32 | forcing + units | incomplete | 0.7392 | 0.7153 | no |
| 32 | parity | 5.0763 | 5.9948 | 5.4823 | yes |
| 64 | forcing base | 257.0102 | 10.1735 | 3.8213 | no |
| 64 | forcing + units | incomplete | 2.3119 | 2.4621 | no |
| 64 | parity | 27.2697 | 29.8219 | 28.1516 | yes |

The entry check correctly skipped **4/4 parity** cases and admitted
**8/8 forcing** cases. n=64 parity's overhead versus raw fell from
~9.4% with unconditional preprocessing to ~3.2% with adaptive
preprocessing **on this runner**. n=64 forcing base improved roughly
**67.3x** over raw, admission included. The relative speed of adaptive
and always-simplify can vary with contention; notably the n=64
unconditional forcing time was substantially slower in this repeated
hosted run than R-003's prior run. Two repetitions are too few to
support robust universal ranking or speedup inference.

## Scientific interpretation and next work

This result improves a practical representation-sensitive prototype
without establishing any new mathematical invariant. Correctness is
still established through Boolean identities and finite adversarial
tests rather than Lean certification.

Next:
1. Evaluate adaptive admission on a **held-out mixed-width source
   corpus** with both negative controls and genuine resolvents.
2. Measure Rust/Python bridge copying and end-to-end memory.
3. Port the small XOR source extractor and associated stable
   normalization to Rust, retaining an independent Python reference.
4. If Lean formal verification is desired, design auditable
   transformation certificates for unit-reduction and consensus.

The research automation queue remains finite/read-only and does not
generate its own experiments or post to a closed ChatGPT thread.
