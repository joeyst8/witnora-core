# HV-020 — Preregistered exact one-step safety reduction (development case only)

**Date:** 2026-11-11 America/Chicago. **Status:** protocol only, before new audit script/results. This is **not** a new algorithm, novel theorem, or full chip-safety certificate.

## Provenance and preservation
- Frozen SoSy-Lab/HKU HWMCC'24-derived source `array/btor2/hku-array/processed_hl_arr_access_32_arr.btor2` at upstream GitLab commit `e19d110544fe7481763894f479b223aaa95fa582`; original SHA-256 `93fb87c152dc8b7fc3e709f1d56a6ab1178ac782340a1b84b86ee69f8fa40c49`.
- No modification to original benchmark, init/next transitions, inputs, witness, or holdouts.
- Repository's existing HV-010–019 results are prior evidence; this is a follow-up **development-only structural audit** and cannot be presented as a preselected unseen test.

## Frozen claim to test
The original bad output is `B(t)=s45(t) & !s43(t)` (original 47,48,406). Original transition equations are:
- `s43(t+1)=!write_enable(t) | result_reg(t)` (nodes 273-275).
- `s45(t+1)=!s43(t+1)` (nodes 276-277).
- `write_enable(t)=full_n(t) & FSM_bit5(t)` (nodes 25-31; low-bit slice of two concats ANDed).

Consequently, **for any original state and any original inputs, without reachable-state assumptions**,

`B(t+1) <=> full_n(t) & FSM_bit5(t) & !result_reg(t).`

This is a *single-step combinational identity*, **not** the assertion that this expression is unreachable. It means original unbounded safety reduces after initialization to a reachability invariant `(full_n & FSM_bit5) -> result_reg`, together with the original `B(0)=false` reset obligation. This candidate target is weaker than the earlier H1 `FSM_bit5 -> result_reg`.

## Validation procedure and gates
1. Confirm each quoted source node equation against the previously SHA-pinned transcript/source; mark source hash as previously verified if source bytes cannot be reaccessed this turn, and **never imply a fresh hash recheck**.
2. Exhaustively evaluate all eight Boolean valuations of `(full_n,FSM_bit5,result_reg)` with the exact transition equations. Require 8/8 equality and 8/8 complementary next-state relations. Since the transition makes `B(t+1)` independent of both pre-state latch values, also enumerate all four `(s43,s45)` pre-state valuations: require 32/32 equality.
3. Positive control: assert a deliberately incorrect alternative `write_enable | !result_reg` and require a mismatch, to detect a vacuous test harness.
4. Record a machine-readable result plus executable deterministic audit script, and separately report status of **unbounded reachable-state safety** as UNKNOWN until an independently checked invariant/proof exists.

## Prior-art novelty guard
- AutoINV, arXiv:2604.22285 (FCCM 2026), already generates HLS FSM one-hot and other helper properties, ranks helper relevance by CTIs, and side-loads proven clauses. https://arxiv.org/html/2604.22285v1
- LLM4PDR, arXiv:2609.30131 (2026), already uses LLM-generated predicates, clauses, and helper assertions with solver-side checks for word-level PDR including BTOR2, HLS, and memory controllers. https://arxiv.org/abs/2609.30131
- Agentic-IC3, arXiv:2609.27162 (2026), already studies agent-guided semantic IC3 search. https://arxiv.org/abs/2609.27162
- Pono 2.0 (FM 2026) already implements array-aware SMT-based model checking and IC3SA. https://www.sosy-lab.org/research/pub/2026-FM.Pono_2.0_A_Versatile_SMT-Based_Model_Checker_for_Safety_and_Liveness.pdf

**Admissible claim if all gates pass:** exact structural slicing of the single development benchmark's *one-cycle bad predicate*, helpful for targeting a later proof search. **Not admissible:** proof of unbounded safety, algorithmic novelty, speedup, industry deployment, proof of any untested holdout.

## Next independent gate
Solve `Init => I`, `I & T => I'`, and `I => (!full_n | !FSM_bit5 | result_reg)` for a full inductive invariant `I` over the original transition system, using independent certificate/witness acceptance and baseline comparisons. If no checker is available, record this as **not run** rather than a pass.
