# HV-019 — Predeclared control-strengthened original-property 1-induction

**Date:** 2026-11-10 America/Chicago. **Before any HV-019 solver call.**

## Hypothesis and scientific gate

HV-018 found that the controller legality predicate `L(s)=node99` is 1-inductive in the exact published HKU HLS BTOR2 transition system. HV-013 found the original safety property `P(s)=NOT node48` is not 1-inductive without strengthening. Test **exactly one** predeclared strengthening: the verified controller lemma, with no speculative result-latch H1.

This is a known form of auxiliary-invariant strengthening, not a new Witnora algorithm. It may nonetheless produce the first independently certifiable safety proof for this concrete benchmark.

## Fixed query

- **Source** unchanged `processed_hl_arr_access_32_arr.btor2`, SHA256 `93fb87c152dc8b7fc3e709f1d56a6ab1178ac782340a1b84b86ee69f8fa40c49`.
- Reuse the exact HV-010 depth-1 unroller, SHA256 `51d1fd32b8bd7c70ab437daed7ed1bd0d419326ce7b9a6b50792529850e9d94b`. Retain all 26 transition equalities, remove exactly seven initialization constraints, remove the two original bad records.
- Append `constraint NOT bad48_at_t0` (original property holds at frame 0), `constraint NOT bad100_at_t0` (FSM one-hot legal at frame 0), `bad bad48_at_t1` (original property violated at frame 1). The frame-node IDs derive mechanically by the frozen HV-010 source-expression enumeration. Fail closed on mismatches.
- Confirm the original property base k0 UNSAT using already-published HV-010 result, and onehot base+step UNSAT from HV-018; do not silently add other assumptions.
- Solve this one combined step query using pinned Bitwuzla 0.6.1 with **20s wall / 2GiB virtual memory**.
- **Conditional certification** if and only if combined step UNSAT: construct witness exactly by appending `407 bad 100` to the unchanged source, preserving original `406 bad 48`; run official Cerbtora 2.0.0 `check <source> <witness>` under **60s wall / 2GiB**. Record five sub-obligations and exit. Only a checker acceptance can be called certified safe. A rejection means no certificate. If combined step is SAT or UNKNOWN, skip certificate attempt and record the counterexample-to-inductiveness or timeout, which is **not** a reachable unsafe trace.

## Interpretive safeguards

A proof would be a practical verification milestone but the algorithm is established prior art. A SAT step demonstrates only insufficiency of the controller lemma, not unsafety. Either outcome will be preserved in draft PR #145 with exact hashes and complete provenance.
