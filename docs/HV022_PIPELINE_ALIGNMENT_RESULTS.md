# HV-022 — Actual 8×8 RAM, pipeline alignment and terminal-cycle gating

**Date:** 2026-11-16 (America/Chicago). **Status:** conditional transition identities and exhaustive control checks PASS; end-to-end safety proof **NOT obtained**. Draft Witnora PR #145; no frozen holdout used.

**Source**: unchanged public mirror `CyanoKobalamyne/hwmcc-benchmarks` revision `57174f5d6f575aedcfe83694b35ec8e7b83043fc`, path `array/2024/hku/safe/processed_hl_arr_access_32_arr.btor2`, normalized-admitted in HV-021, raw SHA-256 `cfa12d67ca508b686e2c2609962fac74919e7448ca8a379d2527cdeba65d58bc`. Original SoSy-Lab source bytes still not reacquired; see HV-021 provenance caveat.

## Correction to earlier research summaries

The benchmark filename contains `32_arr`, **but its RAM BTOR2 sort is `318 sort array 81 6`, where sort 81 is 3-bit and sort 6 is 8-bit**. It therefore has eight addressable locations with eight data bits each. Calling this an explicit **32-element array** was misleading and is corrected here. The filename's `32` is not a reliable statement of the encoded RAM depth. The model also has eight separate 8-bit shadow registers. Do not market this case as industrial-sized RAM on the basis of its filename.

## HV-022A — stage-alignment result

Derived by direct substitution of original source nodes (so a conditional algebraic identity, *not* a novel solver theorem):

- `E(t) = FSM_bit4(t) & pp1_iter0(t)` (node 153).
- When E is true, RAM address (node 194) is the low three bits of counter state 60, and RAM read enable (node 197) is true.
- `q0(t+1) = RAM(t)[counter(t) mod 8]` (node 321).
- `phi(t+1) = selected_shadow(t)` (node 316) for counter values 0 through 7, with exact shadow selection:
  - indices 0,1,2,3: source states 188,181,182,183 respectively, from mux node 236;
  - indices 4,5,6,7: source states 184,185,186,187 respectively, from mux node 223.
- When counter = 8, terminal flag node 114 is true; the phi mux selects the unconstrained 8-bit input node 310. RAM still reads address zero due truncation to three bits. Thus **no unconditional RAM-phi equality at the terminal cycle**.

Exact conditional identity at arbitrary state/input valuation, stage enabled, counter i in [0,7]:

```
q0_next == phi_next
  IF AND ONLY IF
RAM_before[ i ] == shadow_before[ i ]
```

Original BTOR2 forward-evaluator controls:

| Trial | Pass | Fail |
|---|---:|---:|
| Random unconstrained stage-enabled samples (9 counters × 140) | 1,260 | 0 |
| Forced RAM/shadow equal (9 counters × 64) | 576 | 0 |
| Forced RAM/shadow unequal (9 counters × 64) | 576 | 0 |
| Stage disabled with unrelated read disabled: both registers hold (9 counters × 64) | 576 | 0 |

All 1,728 forced/hold cases plus 2,520 original random configurations (of which 1,260 had stage enabled) were evaluated against the unchanged node graph. **These are implementation controls and finite tests**; the unrestricted one-step identity is justified by literal substitutions of the pinned BTOR2 equations. Example deliberate false terminal claim counterexample from an *arbitrary*, not necessarily reachable, state: i=8, RAM[0]=145, input310=146; therefore q0_next=145 and phi_next=146.

## HV-022B — why terminal comparison is gated off

The follow-up was predeclared in `docs/HV022B_PREDECLARED_TERMINAL_GATING.md` before exhaustive testing. From nodes 306–309, independent of previous controller phase:

```
pp1_iter1(t+1)
  = !ap_rst(t) && pp1_iter0(t) && (counter(t) != 8)
```

From nodes 328–329:

```
icmp34_reg(t+1)
  = FSM_bit4(t) ? (counter(t)==8) : icmp34_reg(t)
```

The actual comparison gate is node 262: `FSM_bit4(t+1) && pp1_iter1(t+1) && !icmp34_reg(t+1)`. Therefore any **next-cycle** comparison event implies `counter(t)!=8`, `pp1_iter0(t)=1`, and `ap_rst(t)=0`. This implication does **NOT** by itself imply `FSM_bit4(t)=1`; that extra predecessor-phase fact is a separate reachable-state timing obligation.

Exhaustive evaluation of original BTOR2 control cone at all 16 counter values, both reset values, both pp1_iter0 values, both previous icmp34 values, both previous FSM_bit4 values, both successor FSM_bit4 values: **512/512 passed** for stage-enable equation, 512/512 for icmp34 equation, and **512/512** for comparison implication; 45 cases had next-cycle comparison enabled. An intentionally false mutant equation omitting the counter==8 block was rejected in **8/512** combinations, all at counter 8.

## What is still NOT proved

1. **Reachable controller timing:** If a comparison is executed at time t+1, did the prior RAM/phi capture event E(t) actually occur? The last comparison implication gives pp1_iter0(t) but does *not* by itself give FSM_bit4(t).
2. **Reachable RAM/shadow coherence:** During the relevant capture, does RAM[i] equal the selected shadow byte? They are *not* equal for arbitrary assignments. Must account for the producer write index, shadow-register update index and pipeline delays.
3. **Inductive preservation and original safety:** Prove the clocked result latch remains valid until a final write; then obtain independent Cerbtora/Bitwuzla witness acceptance for the unchanged original safety property.

No full BTOR2 safety proof, no newly accepted certificate, no new algorithm, no out-of-sample improvement, and no verified speedup from HV-022. Established HLS read/write dependence, IC3/PDR and array abstraction are prior art; notably Pono 2.0 (FM 2026) has array-aware IC3SA and finite-index CEGP, and IC3-Evolve (IJCAI 2026) provides proof/witness-gated search. Avoid duplicate claims.

## Proposed next falsifiable task (HV-023)

Predeclare **controller-phase bridge** + **per-address RAM/shadow validity/provenance** candidate, then test under the exact original init/next relations with an established solver, an invalid-witness control and Cerbtora independent checker. Start on this development model; leave previously frozen holdouts untouched. If phase bridge fails on a reachable counterexample, do not assume the RAM equality. Only after an accepted certificate and multiple baselines consider original mechanism research.

Artifacts:
- `docs/HV022_PREREGISTERED_PIPELINE_ALIGNMENT.md`
- `docs/HV022B_PREDECLARED_TERMINAL_GATING.md`
- `research/hv022_pipeline_alignment.js`
- `research/hv022_terminal_gating.js`
- `research/results/hv022_pipeline_alignment_and_terminal_gating.json`
- this report.
