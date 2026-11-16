# HV-014 — Combined one-hot/controller-result candidate still fails induction

**Date:** 2026-11-10 America/Chicago. **Status:** single preregistered H3 witness check **FAILED**; no chip-safety certificate obtained. Protocol `docs/HV014_PREDECLARED_FSM_RESULT_WITNESS_H3.md` committed first at `91618b3e9e6efbdb8c8d2ec72bd57a168bc44ac5`.

Input was exact source `processed_hl_arr_access_32_arr.btor2` with SHA-256 `93fb87c152dc8b7fc3e709f1d56a6ab1178ac782340a1b84b86ee69f8fa40c49`.

## Frozen hypothesis H3

Strengthened original safety with both:
- **FSM validity:** original node `99` checks that controller node14 equals one of exactly six canonical one-hot values; `100 = not 99` is invalid encoding, added as a bad output.
- **H1:** `FSM_bit5 -> final_result_latch`, violation `27 && !22` (the candidate from HV-010).

No circuit input/state, init, next, or original bad was changed; appended exactly:

```btor2
407 not 1 22
408 and 1 27 407
409 bad 100
410 bad 408
```

Witness file SHA-256 `d418c0df30a159a99415df8271da8ebb647d7742094ccd447c75d3a8b48c39f1`. Generator is `research/hv014_h3_witness.py` SHA-256 `176fb9d0643044089ec87151f7b4dc6413b38ad45bede1cd8d1f6b430f3fbd40`.

## Checker result

Ran pinned Cerbtora 2.0.0 commit `983a21c440f8e4f25b1e8be8bd759332fee21e88` using Bitwuzla 0.6.1, `TIME=20 SPACE=2048`. Exact observable obligations:

| Obligation | Verdict |
|---|---|
| Reset | Pass |
| Transition | Pass |
| Property | Pass |
| Base | Pass |
| **Inductive step** | **FAIL: SAT** (`Bad property 801 satisfiable.`) |

Full check exit code **1**; no accepted witness.

This is consistent with the earlier H1 (fails induction) and HV-013 (arbitrary invalid FSM encodings can contribute to induction counterexamples). It shows **eliminating invalid multi-hot FSM encodings alone does not discharge all proof obligations**. H3's failing step could arise through the result latch or array data relationship; the checker result alone does not isolate which. The design's safety was not disproven, and the result is neither a discovery nor a verified speedup.

**Stop condition:** no further speculative one- or two-clause invariant guesses as a substitute for an established invariant generator. Next move: establish a genuine Pono 2.0 array-IC3SA/AVR baseline and extract an independently checked reachable-state invariant. Keep the draft PR open and all holdouts frozen.
