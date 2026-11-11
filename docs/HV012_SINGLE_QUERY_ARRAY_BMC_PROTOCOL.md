# HV-012 — Frozen single-query bounded array safety encoding protocol

**Date:** 2026-11-10 (America/Chicago). Recorded before any HV-012 solver tests. This is an *exploratory development-only* follow-up after the fixed HV-011 32/64-depth multi-bad checks returned UNKNOWN.

## Exact unchanged model/tooling
- SoSy-Lab word-level-hwmc-benchmarks at GitLab commit `e19d110544fe7481763894f479b223aaa95fa582`, file `array/btor2/hku-array/processed_hl_arr_access_32_arr.btor2`, SHA-256 `93fb87c152dc8b7fc3e709f1d56a6ab1178ac782340a1b84b86ee69f8fa40c49`.
- Fixed original `research/hv010_btor2_bmc.py` transition system unroller from HV-010. Cerbtora 2.0.0/Bitwuzla 0.6.1 pinned native build.
- Completely isolated scratch copies; no modifications to original benchmark or previously untouched design holdouts.

## Precommitted diagnostic and test order
1. Recreate ordinary unrolled original source at **depth 16**, compare its original output SHA-256 to the HV-010 archived record. This is only a reconstruction check.
2. Transform its existing **N** distinct `bad` outputs into **one** BTOR2 `bad` whose predicate is the OR of all original frame-specific `bad` predicates. Leave *all* inputs, state/timeframe expressions, reset/next constraints bit-for-bit unchanged in the generated program. Repeat for depths **16, 32, 64**, in that order. `N=depth+1`. The replacement preserves the semantics of *existence of any bad frame up to the selected horizon*. The output SHA of each transformed file is recorded.
3. For a SAT-positive check, combine the normal 16-frame bads with a known satisfiable `ap_start` input bad in frame 0, then OR those signals. Expect a SAT control.
4. Run one Bitwuzla 0.6.1 `--lang btor2 --time-limit 20000 --memory-limit 2048` invocation per transformed model, capture **verbatim** verdict, elapsed wall time, exit code. Unknown is a genuine unknown and process exit code 0 is not a safety proof.

Fixed depth-32/64 original multi-bad outputs were already UNKNOWN in HV-011 at the same cutoff. This test assesses whether *standard single-query BMC aggregation*, without algorithm innovation, helps the same models; it is not a controlled tool-runtime speedup claim. No claim of safety beyond the tested finite horizon or novelty from ordinary BMC.
