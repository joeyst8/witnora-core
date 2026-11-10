# HV-010 — Frozen development-only FSM invariant hypothesis (before witness test)

**Date:** 2026-11-10. This is a **single exploratory, pre-declared witness candidate** for a previously used HV-009 **development** circuit. It does **not** touch any unrun holdout.

Input: `processed_hl_arr_access_32_arr.btor2`, the unchanged HWMCC-related HKU array circuit at SoSy-Lab repo commit `e19d110544fe7481763894f479b223aaa95fa582`; SHA-256 `93fb87c152dc8b7fc3e709f1d56a6ab1178ac782340a1b84b86ee69f8fa40c49`.

## Observation and strictly limited candidate

The source includes a six-bit FSM latch, BTOR2 node 14, with its bit 5 extracted as node 27, and a result latch at node 22. A downstream comparison of input and FSM bit 5 contributes to the transition of two helper state bits, nodes 43 and 45, whose conjunction defines the bad output (node 48).

**Candidate H1:** Strengthen the original witness property with `not(FSM_bit5 and not(result_latch))`. Preserve *all* original inputs, state latches, reset equations, next-state equations and the original bad property. In the witness only, add a second `bad` for `FSM_bit5 && !result_latch` (using original node 27 and 22, Boolean sort node 1). This is an existing inductive-strengthening methodology, not a Witnora original algorithm. No claim of true invariant until checked.

**Single frozen attempt:** generate the augmented witness from the original SHA-pinned file, run existing Cerbtora 2.0.0/Bitwuzla 0.6.1 with TIME=20 SPACE=2048, capture exact check results and exit code. If failed, do not call the model UNSAFE. If accepted, note this is a full *externally checker-accepted witness* for one HLS array benchmark, but not an independent SMT proof-log verification, a new algorithm, a generalizable advantage or a result about the memory-array datapath specifically.

Additional hypotheses may be proposed later only as separately labeled development exploration, never post-hoc disguised as pre-registered holdout results. The older `tv80`, `spi`, `systemcaes` holdouts remain untouched.
