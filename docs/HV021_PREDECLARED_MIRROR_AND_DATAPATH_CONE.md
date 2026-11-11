# HV-021 — Preregistered mirror semantic admission and datapath-cone extraction

Date: 2026-11-11 America/Chicago. Development task only, downstream of HV-020. **Preregistered before computing unrolled mirror digest and before running the dependency extractor.**

## Why this experiment
Original source `processed_hl_arr_access_32_arr.btor2` (SoSy-Lab GitLab commit e19d110544fe7481763894f479b223aaa95fa582, previously SHA256 `93fb87c152dc8b7fc3e709f1d56a6ab1178ac782340a1b84b86ee69f8fa40c49`) is inaccessible in the current cloud browser owing to a site-served security challenge. Independent open GitHub mirror now located at `CyanoKobalamyne/hwmcc-benchmarks`, path `array/2024/hku/safe/processed_hl_arr_access_32_arr.btor2`. Its raw hash differs from the pinned upstream file: **do not conflate the bytes.**

Official HWMCC'24 results file `hwmcc/hwmcc.github.io/2024/hwmcc24_btor2_array.csv` contains rows for the specific 32-width task. In the competition configuration, btormc, btor2-cert, Pono and nuXmv time out around 3601 seconds; AVR returns `unknown` after about 3559 seconds. These results are historic HWMCC'24 data, **not evidence that 2026 versions of these tools cannot solve it**.

## Frozen gate A: semantic equivalence proxy
1. Fetch the unchanged `research/hv010_btor2_bmc.py` from existing draft PR #145. This parser removes comments and cosmetic signal names, but retains BTOR2 operations, source IDs, every init/next/bad, all 26 state transitions and every array expression.
2. Allow only the unroller's input SHA guard to accept the GitHub mirror raw hash in an isolated scratch copy; do not modify the archived script or original raw circuit.
3. Run the same generator at **depth 1, no controls, no extra probes**. Compare its `output_sha256` with the previously archived canonical pinned-source depth1 unroller SHA256: `51d1fd32b8bd7c70ab437daed7ed1bd0d419326ce7b9a6b50792529850e9d94b`.
4. **Acceptance criterion:** exact bytewise equality of deterministic depth1 unroller outputs. This implies the parsed source records relevant to this unroller—including array operations and all 26 next-state rules—produce an identical two-frame representation. It does not establish byte identity of the original files, independent solver soundness, or full formal equivalence of arbitrary source languages.
5. **Negative control:** change one source node's bad-output reference in isolated memory and require the generated unroller digest to change. If baseline mismatches or negative control fails, **do not run subsequent datapath study as if the source matched.**

## Frozen gate B: exact target cone (only if A passes)
1. Start at source node `265 next 1 22 264` (result register), follow all expression operands and state references recursively, stop at state/input leaves. Include `319` array-state node and `320/397` reads only when reachable from the cone.
2. Record the exact sorted node IDs, leaf state and input IDs; record whether the cone intersects the array state, memory read and comparison node 166. Avoid invented clock or memory assumptions.
3. Cross-check `bad(t+1) = full_n(t) & FSM_bit5(t) & !result_reg(t)` against the syntactic node statements of this admitted mirror.
4. A cone listing is **not** a discovered invariant or proof. If it reveals a memory dependency, define the next *falsifiable* trial for a certifying model checker, do not claim safety.

## Historic/novelty safeguards
- HWMCC'24 official benchmark/results source: https://hwmcc.github.io/2024/ and https://zenodo.org/records/14156844 .
- AutoINV FCCM2026, LLM4PDR 2026, and Pono 2.0 already cover many generic HLS or word-level invariant generators; no assertion of conceptual novelty from this analysis.
- No frozen holdouts touched; no solver runs until protocol and toolchain are independently validated. PR remains **draft**.
