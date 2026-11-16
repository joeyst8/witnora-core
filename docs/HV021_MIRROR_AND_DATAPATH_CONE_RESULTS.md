# HV-021 — Admitted mirror and exact two-cycle memory-dependency analysis

**Date:** 2026-11-11 America/Chicago. **Outcome:** both preregistered *structural* gates PASS. **Unbounded safety remains UNKNOWN; no novel solver, speedup or verified full-chip proof.**

Preregistered in `docs/HV021_PREDECLARED_MIRROR_AND_DATAPATH_CONE.md` at commit `a51467580ef2920b65421e36bac005cea98fbc6c`, before running the digest or cone experiment.

## Why the benchmark is a meaningful test, not a fabricated toy
The published HWMCC 2024 array result file `hwmcc/hwmcc.github.io/2024/hwmcc24_btor2_array.csv` names `2024/hku/array/safe/processed_hl_arr_access_32_arr.btor2`:
- `btormc,to,none,3601.001396328211`
- `btor2-cert,to,none,3601.001508632675`
- `pono,to,none,3601.0015649376437`
- `nuxmv,to,none,3601.001548798755`
- `avr,ok,unknown,3559.1757555585355`

These are **HWMCC'24 historic one-hour-limit data**; do not extrapolate to 2026 tool versions or hardware industry performance. Official dataset DOI: https://doi.org/10.5281/zenodo.14156844 ; file source: https://github.com/hwmcc/hwmcc.github.io/blob/main/2024/hwmcc24_btor2_array.csv .

## Gate A — mirror provenance (PASS)
Original SoSy-Lab GitLab pinned SHA: `93fb87c152dc8b7fc3e709f1d56a6ab1178ac782340a1b84b86ee69f8fa40c49` (previous HV010–019). That GitLab page raised a browser security challenge this turn, and was **not bypassed**.

Discovered public independent GitHub copy at https://github.com/CyanoKobalamyne/hwmcc-benchmarks/blob/main/array/2024/hku/safe/processed_hl_arr_access_32_arr.btor2 . Its raw SHA-256 is **different**: `cfa12d67ca508b686e2c2609962fac74919e7448ca8a379d2527cdeba65d58bc` (12,319 bytes). We do not assert byte-identical original files.

We reran the *archived unchanged HV010 unroller* except for its input-file SHA guard, at depth 1 with no other flags. The mirror yielded exactly **14,735 bytes** and SHA-256 `51d1fd32b8bd7c70ab437daed7ed1bd0d419326ce7b9a6b50792529850e9d94b`, which **exactly equals** the earlier HV019 archived unroller digest from the original pinned file. This deterministic unroller covers both frames' complete BTOR2 expressions, 7 initial constraints, all 26 state transitions, array sorts/expressions, and original bad in both frames. Therefore the bytewise output match is strong evidence of equivalence **under the unroller's parser/normalization**, despite differing raw source bytes. It is not an independent formally proved equivalence theorem for arbitrary tools.

Positive control: original digest matched. Negative control: only change the source `406 bad 48` to `406 bad 100` in an isolated temporary copy; the output SHA changed to `ad527adf46c1c487dde8820be35873dd3f4764efc417df9cbd10ca0ffeb24ac0`. Therefore the admission test is not insensitive to the safety output. The mutant was not applied to any original task/holdout.

Reproduction: `research/hv021_mirror_admission.py MIRROR_FILE research/hv010_btor2_bmc.py`, source SHA pinned in script. No duplicated licensed benchmark source committed.

## Gate B — precise memory dependency (PASS)
On admitted source:
- Original bad: `406 bad 48`, with `48 = state45 & !state43`.
- HV020 exact reduction: original bad at next cycle iff `full_n & FSM_bit5 & !result_reg`.
- Result register next equation is `265 next 1 22 264`.
- Its conditional branch `262 = FSM_bit4 & ap_enable_reg_pp1_iter1 & !icmp_ln34_reg` selects `167 = (q0 == ap_phi_reg) & old_result`; another branch `FSM_bit3` forces result true.
- State `165` is the registered memory output `q0`, and state `164` holds the expected/previous pipeline value. Their equality is node **166**.
- State `165` next RHS node321 conditionally reads the array state **319** through node **320** at address node194.
- Array state `319` next RHS node404 includes write node **402**, using read node **397** and masked data logic.

Dependency expansion was deterministic, with one state transition consumed per step:

| Lookback in state transitions | Distinct cone nodes | State leaves | Memory involvement |
|---|---:|---:|---|
| 0 | 16 | 6 | q0/phi equality 166; both are state leaves, no array operation |
| 1 | 151 | 22 | RAM state 319 and array read 320 enter |
| 2 | 252 | 25 | RAM write 402 and array read 397 enter |

Input leaves at depth0: none. Depth1 inputs: `3,4,5,8,75,189,310`. Depth2 adds input `7` (new data). All detailed exact node-ID sets are machine-recorded in `research/results/hv021_mirror_datapath_cone.json`.

This **does not prove** that a particular memory equality remains true. It tells us the relevant relation is temporal across *at least two registers/clock steps*, so naive one-hot-only strengthening misses the array write/read path.

## Scientific significance and novelty gate
- This is an independently reproducible **problem reduction and causality map**, not a new verification algorithm.
- AutoINV (FCCM2026), LLM4PDR (Sep2026), Pono2/IC3SA, and older property slicing/cone-of-influence work cover major classes of predicate discovery and proof search. Our cone calculation is standard.
- The **next falsifiable research task** is to derive an inductive, checker-accepted relationship between expected pipeline value state164, RAM output state165, RAM state319/address194, and result latch state22 that implies the exact reduced target when controller state bit5 and `full_n` are high. The proof must be over all reachable states under the unchanged BTOR2 transitions.
- A meaningful algorithmic result would require an **independently checked proof** plus a predeclared, controlled solve+certificate+check runtime comparison with existing array-aware model checkers (especially 2026 LLM4PDR/AutoINV methods when reproducible). No holdout was run.

## Files and reproducibility
- Protocol: `docs/HV021_PREDECLARED_MIRROR_AND_DATAPATH_CONE.md`.
- Reproduction of digest admission and negative control: `research/hv021_mirror_admission.py` (SHA-256 `1d6858bd4e5a8da7deb7b00752def168d6b18208008a1a2a22c356e0dc6a23d0`).
- Datapath cone: `research/hv021_datapath_cone.py` (SHA-256 `fabb00ff7ddd9dbafd15add4a7da465fc1dd91be04ae0246d16eb52fd0d803b4`).
- Full machine record: `research/results/hv021_mirror_datapath_cone.json`.
- Prior canonical unroller: `research/hv010_btor2_bmc.py`.

**Truth-status:** historical hard benchmark established, normalized mirror admitted, exact dependency cone reported; full proof UNKNOWN, novel algorithm UNDEMONSTRATED.
