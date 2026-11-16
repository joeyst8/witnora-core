# HV-018 — Predeclared one-hot controller invariant isolation

**Date:** 2026-11-10 America/Chicago. **Frozen before generation/solving.**

## Purpose and prior-art gate

HV-014 combined an exactly-one-active FSM condition (original BTOR2 node 100 is the violation indicator) with a speculative result-latch implication H1. Cerbtora rejected the **combined** witness on its induction step. That rejection does **not** identify whether the FSM legality clause itself is inductive. This diagnostic isolates the controller lemma using ordinary 1-induction, which is standard prior art, not a proposed Witnora breakthrough.

## Fixed source, transformation and queries

- **Source:** unchanged HKU HLS `processed_hl_arr_access_32_arr.btor2`, exact SHA256 `93fb87c152dc8b7fc3e709f1d56a6ab1178ac782340a1b84b86ee69f8fa40c49`.
- **Lemma:** `L(s) = (original node 99 == true)` where node 99 is an OR of the six legal one-hot FSM states; violation is original node 100. No assumptions about unrelated registers, no H1.
- Reuse the previously admitted `hv010_btor2_bmc.py` original unroller at depth 0 and 1. For each time frame locate the emitted image of original node 100 deterministically from the source node sequence and count of emitted sort declarations. Reject if source hash, unroller structure, or constraint counts do not match expected.
- **Base:** retain all original 7 initial equalities, replace sole time-zero bad with `bad node100_at_t0`. Ask SAT/UNSAT.
- **Inductive step:** from depth-1 original unroller remove exactly 7 initial constraints, keep 26 transition equalities, replace original bad queries with `constraint NOT node100_at_t0` and `bad node100_at_t1`. Ask SAT/UNSAT.
- **Positive control:** same uninitialized one-step system *without* the previous-frame legality constraint, ask `bad node100_at_t0`; should be SAT if invalid arbitrary FSM states exist.
- Use SHA-pinned originally built Bitwuzla 0.6.1 (HV-010 provenance), three independent subprocesses, each 20-second wall timeout and 2 GiB address cap. Record exact hashes and output. If all three expected verdicts hold, conclude only that FSM legality is 1-inductive. Do **not** infer safety of original bad node 48 or claim an accepted Cerbtora witness.
- No alteration of original source or its bad condition; transform generated queries only. No additional invariant, property, or solver tuning after results.

## Why this matters

A validated controller-only lemma isolates the source of H3 failure to the combination, not necessarily to one-hot control. It can become a candidate ingredient in later proof discovery. It is not novel algorithmic content, and a proof of the complete HLS property still requires an independently admitted witness.
