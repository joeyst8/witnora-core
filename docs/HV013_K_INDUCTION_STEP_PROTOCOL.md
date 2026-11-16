# HV-013 — Frozen unstrengthened k-induction step ladder

**Date:** 2026-11-10 America/Chicago, before first HV-013 solver run. Same previously used **development** HLS array source (pinned SHA-256 `93fb87c152dc8b7fc3e709f1d56a6ab1178ac782340a1b84b86ee69f8fa40c49`); no untouched holdouts.

**Goal:** identify whether *plain safety-property k-induction*, without new invariants, can prove this design. Prior Cerbtora original-self-witness k=1 step was SAT. The HV-010 bounded base was UNSAT at depths 0..16.

## Exact fixed tests

1. Generate the original BTOR2 unrolling for `k=1,2,4,8,16` with archived `research/hv010_btor2_bmc.py`. Check SHA pinned source and unchanged generator.
2. Mechanically transform each unrolling into a **k-inductive step query**: remove the seven initial-state constraints; preserve all 26 transition equalities for every step; constrain *all original safety bad predicates* to **false** at frames `0..k-1`; assert original bad predicate at frame `k`. All source state/input expressions remain unchanged; no reset constraint in the induction step. One SAT result at step k means this particular k-induction obligation is NOT valid; UNSAT would be a successful induction step, subject to matching UNSAT base and translation checks.
3. Check with pinned Bitwuzla 0.6.1 at `--lang btor2 --time-limit 20000 --memory-limit 2048`, exactly k=1,2,4,8,16 in order; record exit, SAT/UNSAT/UNKNOWN and transformed query digests. UNKNOWN is not a proof.
4. Validate k=1 step against HV-009 original-model Cerbtora SAT-step failure; additionally confirm a simple separate Boolean toy to guard against vacuous UNSAT if practicable.

No new theorem or method is asserted: k-induction is well-established. If all SAT, next priority is Pono 2.0/AVR word-level invariant synthesis rather than more scalar-only speculative templates. This is a development experiment and leaves draft PR #145 open.
