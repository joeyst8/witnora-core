# HV-013 — Plain k-induction fails on the unchanged array chip

**Date:** 2026-11-10 (America/Chicago). Frozen procedure was committed before tests in `docs/HV013_K_INDUCTION_STEP_PROTOCOL.md` (commit `d6a7b20fa1db0249ef34870e08770c5bd0dc373b`).

## Verification question

On the exactly SHA-pinned public HLS array model `processed_hl_arr_access_32_arr.btor2` (`93fb87c152dc8b7fc3e709f1d56a6ab1178ac782340a1b84b86ee69f8fa40c49`), does the original, *unstrengthened* safety predicate become k-inductive by k=1,2,4,8,16?

Standard inductive-step formula: unrestricted initial state at frame 0 (remove the seven source reset constraints), all `26*k` genuine next-state equalities retained, original safety assumed at frames 0 through k−1, original bad queried at frame k. The unroller/generator preserves all bit-vector and array theory terms. Bitwuzla 0.6.1 was invoked with `--lang btor2 --time-limit 20000 --memory-limit 2048` per case.

| k | Inductive-step result | Bitwuzla output |
|---:|---|---|
| 1 | **SAT (fails induction)** | `Bad property 792 satisfiable.` |
| 2 | **SAT (fails induction)** | `Bad property 1202 satisfiable.` |
| 4 | **SAT (fails induction)** | `Bad property 2022 satisfiable.` |
| 8 | **SAT (fails induction)** | `Bad property 3662 satisfiable.` |
| 16 | **SAT (fails induction)** | `Bad property 6942 satisfiable.` |

All exited code 0. This is consistent with HV-009's initial Cerbtora k=1 induction-step rejection. Earlier **bounded base** checks at 0–16 transitions were UNSAT. Thus, for these k values, failure is a lack of inductiveness, **not** evidence of a reachable bug.

## What the SAT witnesses reveal

The Bitwuzla model for k=1 places the *arbitrary* initial induction-frame controller in FSM `100000` and result latch `0` with input write-enable `1`. The helper bits start `43=1, 45=1` (safety initially holds) and transition to `43=0, 45=1` (bad becomes true). Nothing in this **unrestricted** induction start enforces reachability from the reset state.

For k=2 the SAT model begins in FSM `100001` — an invalid, **multi-hot** encoding — with result latch `0`. It transitions to FSM `100000` then `000010`, with the helper bad arising at the end. The actual reset FSM code is `000001`. This is a concrete example of an induction counterexample exploiting controller encodings that are not expected reachable from reset.

That alone does not show that a one-hot invariant suffices: even k=1 uses a one-hot controller with an incompatible result latch. **A combined reachable-state/controller-result and possibly array-data invariant is still needed.**

## Reproduce

```bash
python research/hv010_btor2_bmc.py model.btor2 unroll_k2.btor2 --depth 2
python research/hv013_induction_step.py unroll_k2.btor2 induction_k2.btor2 --k 2
/path/to/bitwuzla --lang btor2 --time-limit 20000 --memory-limit 2048 induction_k2.btor2
```

All source/query hashes and model summaries are archived in `research/results/hv013_unstrengthened_k_induction.json`. Generator `research/hv013_induction_step.py` SHA-256 is `9c894600b190e302a3ee64252b0e6b52baa92d1e26c92ff041b329ec33548152`.

**Novelty gate:** k-induction is an established technique, and these negative results are not breakthroughs. This eliminates an easy route to a safety certificate at k≤16. Next test: predeclare a combined one-hot/reachable-result strengthening and evaluate with Cerbtora; if unsuccessful, prioritize established array-capable Pono 2.0 IC3SA/AVR and rigorous invariant extraction.
