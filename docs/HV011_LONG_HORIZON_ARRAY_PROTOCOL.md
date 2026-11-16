# HV-011 — Longer-horizon array BMC, predeclared before testing

**Date:** 2026-11-10. Start after HV-010 was fully archived in draft PR #145; this is transparently a **sequential, exploratory development extension**. It does not retroactively change HV-010's fixed depth ladder.

Use exactly the same unchanged SoSy-Lab 32-named HLS word-level array BTOR2 source at pinned SHA-256 `93fb87c152dc8b7fc3e709f1d56a6ab1178ac782340a1b84b86ee69f8fa40c49`, same `research/hv010_btor2_bmc.py` generator and Bitwuzla 0.6.1.

**Fixed tests, in order**:
1. BMC original bads at depth **32** with `--depth 32`.
2. BMC original bads at depth **64** with `--depth 64`.
3. Reachability of failed H1 (`FSM_bit5 && !result_latch`) with original bads at depth **32** and **64**, using `--probe-h1`.

Each Bitwuzla invocation: `--lang btor2 --time-limit 20000 --memory-limit 2048`. Preserve all original transition/init semantics, report number of checked properties, SHA-256, exact SAT/UNSAT/UNKNOWN statuses, and tool exit. Stop a test if it exceeds resources; unknown is not unsat. No new algorithm, proof, or novelty claim from bounded checking. No untouched holdouts or 128-named second design tested.