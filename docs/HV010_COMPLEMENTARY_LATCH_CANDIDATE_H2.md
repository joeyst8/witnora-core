# HV-010 — Second frozen development-only witness candidate H2 (before checker test)

**Date:** 2026-11-10. H1 has already failed *only* Cerbtora's inductive-step obligation. H2 is proposed afterwards, **not** a pre-registered original holdout, and uses the same development case. This is an explicit sequential research iteration.

## Source and exact candidate

Input is unchanged `processed_hl_arr_access_32_arr.btor2`, SHA-256 `93fb87c152dc8b7fc3e709f1d56a6ab1178ac782340a1b84b86ee69f8fa40c49`.

Original state bits `43` and `45` have `init 43=1` (node 44), `init 45=0` (node 46), `next 43=274` (node 275), and `next 45=276` (node 277), with `276 not 1 274`. Their exclusive-or ought to remain 1 in any reachable state independent of datapath values.

**H2:** `43 XOR 45 = 1`, equivalent to `not(43==45)`. Preserve the entire source verbatim and append:

```
407 xor 1 43 45
408 not 1 407
409 bad 408
```

This is a simple *known* complementary-latch invariant; it is not new science and in particular does not reason about array data. Purpose is to establish one independently checker-accepted whole-model safe certificate as an engineering baseline.

**Frozen test:** existing Cerbtora 2.0.0/Bitwuzla 0.6.1 `check ORIGINAL H2_WITNESS` with `TIME=20 SPACE=2048`, record process exit and all five check obligations. This is H2's first run. Do not alter circuit semantics, do not use previously untouched holdouts, do not claim a speedup/breakthrough.