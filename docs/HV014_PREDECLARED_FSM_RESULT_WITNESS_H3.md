# HV-014 — Frozen combined FSM-validity + result-latch witness hypothesis H3

**Date:** 2026-11-10 America/Chicago. **Committed before first HV-014 checker attempt.** Same unchanged HLS array *development* model, SoSy-Lab commit `e19d110544fe7481763894f479b223aaa95fa582`, SHA `93fb87c152dc8b7fc3e709f1d56a6ab1178ac782340a1b84b86ee69f8fa40c49`.

## Motivation
HV-013 k=2 step counterexample starts at invalid multi-hot FSM value `100001`, while reset is `000001`. Original circuit nodes `77,80,84,87,91,93` test whether FSM register node14 equals one of six canonical 6-bit one-hot codes; node `99` is OR of these exact equality tests; node `100` is its complement (invalid encoding). H1 `FSM_bit5 -> result_latch` (nodes27,22) was not 1-inductive alone, but no reachable violation of H1 was found to depth16.

**H3 witness, single frozen attempt:** preserve all original inputs/state/resets/next/bad and append exactly

```
407 not 1 22
408 and 1 27 407
409 bad 100
410 bad 408
```

This strengthens safety by demanding both **valid one-hot FSM** and **H1 result-register implication**. No additional state is introduced and the original model is not modified.

Run Cerbtora 2.0.0/Bitwuzla 0.6.1 `TIME=20 SPACE=2048 /path/to/check MODEL H3_WITNESS` **once**, capture all five check obligations, exit and witness digest. If it fails, identify which check; do not label safe model unsafe or claim this invariant proved. If it passes, this is a checker-accepted whole-model witness using old invariant techniques, **not** a Witnora algorithmic breakthrough. No original frozen holdout or second 128-named model touched.
