# HV-020 — Exact one-step safety reduction verified by exhaustive Boolean audit

**Date:** 2026-11-11 (America/Chicago). **Status:** structural identity **PASS**; unbounded chip-safety result **UNKNOWN**. Development-only follow-up to HV-019.

**Frozen protocol (committed first):** `docs/HV020_PREDECLARED_ONE_STEP_SAFETY_REDUCTION.md` at `0576face508fa450c2c1f5a85865de9b2ce9220e`.

## The actual question
Why does the original chip property remain unproved despite the 1-inductive one-hot FSM lemma? Can we reduce the property exactly to its proof-relevant state relationship, thereby avoiding further guesses?

The published SoSy-Lab/HKU HWMCC'24-derived development file was previously pinned and independently hashed in HV-010–019 (SHA-256 `93fb87c152dc8b7fc3e709f1d56a6ab1178ac782340a1b84b86ee69f8fa40c49`). **Important limitation:** these source bytes were not downloaded or rehashed again in HV-020; this audit trusts the quoted previously inspected node equations, and all results are conditional on their accurate transcription.

## Exact symbolic derivation
Let `f = full_n(t)`, `c = FSM_bit5(t)`, `r = result_reg(t)`; let `a = state43`, `b = state45`.

Original BTOR2 node relationships from the pinned prior inspection:
- `write_enable = f & c` (nodes 25–31; 24-bit concatenation AND followed by bit-zero slice).
- `a' = !write_enable | r` (nodes 273–275).
- `b' = !a'` (nodes 276–277).
- `bad = b & !a` (nodes 47–48; node 406 declares it bad).
- Original initial conditions `a(0)=1`, `b(0)=0` (nodes 44 and 46).

Therefore, for **every** predecessor valuation,
```
bad(t+1) = b' & !a'
         = !a' & !a'
         = !( !write_enable | r )
         = write_enable & !r
         = full_n(t) & FSM_bit5(t) & !result_reg(t).
```
This has no dependence on arbitrary predecessor values of the two latch bits. Moreover, `bad(0)=0` from the original reset. Hence, along original initialized traces, original `G !bad` is logically equivalent to `G (full_n & FSM_bit5 -> result_reg)`. **This is an equivalence of verification targets, not a proof either target holds.**

The new target is weaker than old `FSM_bit5 -> result_reg` (H1). The outcome clarifies that `full_n` gating is genuinely part of the necessary property; it does not provide a datapath invariant or imply an inductive proof.

## Reproducible audit results
Script: `research/hv020_boolean_safety_reduction.py` (SHA-256 `8191521db35f4549e57078abd0e084b73a230edce276bd2646e3ee0b1c0a3ef9`).
Raw output: `research/results/hv020_boolean_safety_reduction.json`.

| Frozen check | Observed | Status |
|---|---:|---|
| `(f,c,r)` Boolean valuations | 8/8 | PASS |
| All four arbitrary `(a,b)` pre-state assignments combined with eight valuations | 32/32 | PASS |
| Four edge-value assignments for each of the two upper 23-bit concatenation slices per pre-state case | 512/512 | PASS |
| Deliberately wrong comparison expression `write_enable OR !result_reg` | 4/8 mismatches | Positive control PASS |
| Read/re-hash complete original source this run | No | NOT RUN |
| Independently checked complete inductive safety witness | None | NOT RUN |
| Proved original unbounded safety | No | UNKNOWN |

The Python audit uses no third-party packages and does *not* invoke an SMT solver. It mechanically exhausts the listed Boolean cases **under the transcribed equations**. It is appropriately a small validation of the symbolic simplification, not third-party certification of the original transition system.

## Strong prior-art overlap, scientifically important
- **AutoINV** (Xiaofeng Zhou et al., FCCM 2026, arXiv:2604.22285): derives HLS one-hot FSM and pipeline/FIFO helpers from RTL/HLS artifacts, uses proof-time CTI feedback to rank helpers, validates them, and side-loads clauses. Their published experiments report 2.23x average / 6.05x maximum speedup against their chosen model-checking baseline. Primary: https://arxiv.org/html/2604.22285v1 . Our HV-018 one-hot lemma and generic helper-selection narrative are **not novel**.
- **LLM4PDR** (Guangyu Hu et al., arXiv:2609.30131, Sep 2026): generates semantic predicates, side-loaded lemmas and helper assertions inside word-level PDR/Pono; tests BTOR2 and HLS designs. Primary: https://arxiv.org/abs/2609.30131 . A generic proposal to ask an LLM for data/array invariants and formally filter them would **redo published work**.
- **Agentic-IC3** (arXiv:2609.27162, Sep 2026): agent-guided IC3 semantic search, direct conceptual prior art. Primary: https://arxiv.org/abs/2609.27162 .
- **Pono 2.0** (FM 2026) has word-level/array-aware IC3SA; this cannot be sold as a Witnora invention. Primary: https://www.sosy-lab.org/research/pub/2026-FM.Pono_2.0_A_Versatile_SMT-Based_Model_Checker_for_Safety_and_Liveness.pdf .

The AutoINV paper itself says its helpers cover HLS FSMs; unlike this BTOR2-only trace we study, its generator also consumes HLS compilation reports and RTL. That difference alone is **not** demonstrated novelty because LLM4PDR already takes BTOR2 as input.

## Next experimental gate (not yet run)
1. Independently check the exact reduced target `G (full_n & FSM_bit5 -> result_reg)` using the full SHA-pinned original BTOR2 file.
2. Inspect concrete failing induction predecessor valuations and determine the **specific datapath/array relationship**, including memory read/write updates, required to exclude spurious unreachable states.
3. Propose **a preregistered falsifiable hypothesis** about lowering the cost of a complete independently certified safety proof (for example, proof-preserving dependency closure across control and array datapath) only after fully auditing AutoINV/LLM4PDR and existing abstract interpretation, k-induction, PDR and Craig-interpolation literature.
4. Compare reproducible total runtime, verification overhead and soundness on named published holdouts, against matched Pono/AVR/IC3SA and any publicly reproducible 2026 helper baselines. A claimed breakthrough requires independent proof validation plus statistically credible advantages on holdouts.

**Honest summary:** HV-020 turned a broad failing safety proof into an exact control-gated datapath obligation. It is a useful debugging result. No unbounded safety proof, novel algorithm, or performance advantage has yet been demonstrated.
