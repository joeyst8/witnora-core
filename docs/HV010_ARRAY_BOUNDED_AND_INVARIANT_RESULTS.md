# HV-010 — Real-array bounded diagnostic and failed invariant admission

**Date:** 2026-11-10. **Status:** Experiment complete, **no unbounded safety certificate or algorithmic breakthrough**. Draft PR #145 remains open and draft.

## Objective and unchanged benchmark

Continue chip-verification evaluation with the exact publicly sourced HKU HLS array model selected in HV-009, retaining the input semantics. Investigate a practical Cerbtora-accepted safety witness and obtain independent bounded evidence when simple invariant candidates fail. No old combinational holdout or new 128-named array candidate was consumed.

- Source: SoSy-Lab `word-level-hwmc-benchmarks`, commit `e19d110544fe7481763894f479b223aaa95fa582`.
- File: `array/btor2/hku-array/processed_hl_arr_access_32_arr.btor2`.
- SHA-256: `93fb87c152dc8b7fc3e709f1d56a6ab1178ac782340a1b84b86ee69f8fa40c49`.
- Public YAML `expected_verdict: true` (expected safe, **not** used as a solver result).
- The source contains a word-level memory array, 26 state nodes, 26 next equations, 7 initialization equations, 10 input nodes and one original `bad` condition.
- Checker: Cerbtora 2.0.0 with Bitwuzla 0.6.1 (fixed HV-009 build). Each checker invocation used `TIME=20 SPACE=2048`.

## Witness admission: two genuine negative results

Both hypotheses were committed to the draft GitHub branch **before their first check**, in order:

1. `docs/HV010_FSM_INVARIANT_CANDIDATE_H1.md`: **H1** says `FSM_bit5 -> final_result_latch`. The SHA-pinned generator appended BTOR2 nodes `407 not 1 22; 408 and 1 27 407; 409 bad 408` (with a descriptive comment on the last line). Witness SHA-256 `f0cbaf95ecf7c7136e5ac33f705cecbf5e0faaf0b9c896e794dde33dd1e81fd7`. **Cerbtora exit 1**, reset/transition/property/base checks passed, **step SAT / failed**. No inductive proof.
2. `docs/HV010_COMPLEMENTARY_LATCH_CANDIDATE_H2.md`: **H2** says `XOR(state43, state45)=1`, backed by source initialization and complementary next-state equations. Append BTOR2 `407 xor 1 43 45; 408 not 1 407; 409 bad 408`. Witness SHA-256 `2f5210372f96abc69da21a64c44b1c9fe626eec40770dac3e7f075128a332f8c`. **Cerbtora exit 1**, reset/transition/property/base passed, **step SAT / failed**. The complementarity relationship itself is insufficient for the original safety claim.

A failed *inductive step* does **not** mean a reachable violation was found. This is a classic distinction between `not inductive` and `false in reachable states`.

## A useful reduction of the original safety question

In the source, node `48 = 45 && !43` is the original bad predicate. Node `274 = !31 || 22`; nodes `275` and `277` set the next helper latches `43'=274` and `45'=!274`. Consequently, beginning at time step 1, a bad condition is possible precisely when the **prior** step has `31 && !22`.

Node `31` is the write-enable expression depending on the FSM's bit 5 and an input. So safety depends on making sure that the result latch is not clear when write-enable is asserted. This locates the burden of proof at a controller-to-result boundary. Establishing the required reachable relation may ultimately require data/array invariants; the two simple control-latch templates did not establish it.

This is **analysis of the existing chip logic**, not a new theorem.

## Mechanically generated bounded model checking

The depth ladder and conditions were committed first in `docs/HV010_BOUNDED_CHIP_DIAGNOSTIC_PROTOCOL.md`. Script `research/hv010_btor2_bmc.py` (SHA-256 `dd5e1791369eaea5c47801781659f83c8d0de7e3fa83ce6d03b95df4e88ba120`) verifies original SHA, time-copies all state/input and bit-vector/array operators, copies all initialization and transition equalities, and checks original `bad` at each time step.

`bitwuzla --lang btor2 --time-limit 20000 --memory-limit 2048` returned:

| Max transition depth | Frames | Original bad checks | Solver verdict |
|---:|---:|---:|---|
| 0 | 1 | 1 | **All UNSAT** |
| 1 | 2 | 2 | **All UNSAT** |
| 2 | 3 | 3 | **All UNSAT** |
| 4 | 5 | 5 | **All UNSAT** |
| 8 | 9 | 9 | **All UNSAT** |
| 16 | 17 | 17 | **All UNSAT** |

At depth 16: 17 frames, 423 equalities/constraints (7 resets + 16×26 next equalities), 17 original-bad checks, 146,487-byte generated model, SHA-256 `85fb4e83bb4dbf81776fcbc29fa1027c5f405d10e05799fc8227387f9c325689`.

**Positive control:** At depth 0, append a known-satisfiable `bad` on unconstrained `ap_start` input. Bitwuzla reports the original bad UNSAT and the control bad SAT, confirming the test can detect satisfiable `bad` conditions. This checks important solver-facing wiring, though it is not independent validation of the entire translation.

## H1 reachable-state probe

Precommitted in `docs/HV010_H1_REACHABILITY_PROBE_PROTOCOL.md`. Repeated the same depths but added an H1 violation bad `FSM_bit5 && !result_latch` in **every** frame, while retaining the original bad property. Every original-bad and H1 probe was **UNSAT** at depths **0, 1, 2, 4, 8 and 16** (34 checks at depth 16). Probe-depth-16 SHA-256 `325d3f1894b876f73e4fde9a9e64f2f6a00aadaf01603dbf0020e7174c07a7aa`.

Thus H1 is **not 1-inductive as presented**, but **no reachable violation of H1 was found through 16 transitions**. Distinguishing these two outcomes is the strongest technical lesson of this increment.

## Reproduction

```bash
python research/hv010_invariant_witness.py model.btor2 H1.btor2 --candidate h1
python research/hv010_invariant_witness.py model.btor2 H2.btor2 --candidate h2
TIME=20 SPACE=2048 /path/to/cerbtora/check model.btor2 H1.btor2
TIME=20 SPACE=2048 /path/to/cerbtora/check model.btor2 H2.btor2

python research/hv010_btor2_bmc.py model.btor2 depth16.btor2 --depth 16
/path/to/bitwuzla --lang btor2 --time-limit 20000 --memory-limit 2048 depth16.btor2

python research/hv010_btor2_bmc.py model.btor2 h1_probe16.btor2 --depth 16 --probe-h1
/path/to/bitwuzla --lang btor2 --time-limit 20000 --memory-limit 2048 h1_probe16.btor2
```

Replace `model.btor2` with the exact SHA-pinned corpus file. The full per-depth output fingerprints and controls are in `research/results/hv010_bounded_array_diagnostics.json`.

## Hard frontier gate and next target

**What is established:** public-chip transition semantics preserved; two negative 1-induction admission results; bounded original safety and bounded H1 through 16 steps; SAT-positive control passed. These are established methods, not original Witnora techniques.

**What is not established:** an unbounded certificate, invariant completeness, generalization to other chips, any advantage over PDR/IC3 or industrial formal equivalence, independent proof-logging of each Bitwuzla UNSAT call, or a new algorithm.

**Next priority:** build a reproducible, certificate-producing **array-aware strengthening** or a known PDR/IC3/k-induction baseline capable of resolving the current proof obligation. Before claiming novelty, compare against published and current approaches in word-level memory verification and externally check every generated witness. Keep older `tv80`, `spi`, `systemcaes` untouched; keep PR draft until the novelty gate is met.