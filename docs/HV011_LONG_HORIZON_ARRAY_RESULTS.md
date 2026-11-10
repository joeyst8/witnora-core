# HV-011 — 32/64-transition array BMC reaches UNKNOWN under fixed cutoff

**Date:** 2026-11-10. **Status:** completed exact precommitted experiment; **no additional safety proof or counterexample**.

The separately precommitted protocol is `docs/HV011_LONG_HORIZON_ARRAY_PROTOCOL.md` (commit `986755ecec6cbf9a05f65208f9bef9aeed29d538`). This is a transparent post-HV-010 development extension, not a rewrite of the 0/1/2/4/8/16-depth results.

Input remained the **unaltered** HLS HKU 32-named array design, SHA-256 `93fb87c152dc8b7fc3e709f1d56a6ab1178ac782340a1b84b86ee69f8fa40c49`. Reused the pinned mechanical generator `research/hv010_btor2_bmc.py` and Bitwuzla 0.6.1 with `--lang btor2 --time-limit 20000 --memory-limit 2048` per run.

| Experiment | Max transitions | Frames | Constraints | Bad instances | Bitwuzla stdout |
|---|---:|---:|---:|---:|---|
| Original safety | 32 | 33 | 839 | 33 | `unknown` |
| Original safety | 64 | 65 | 1,671 | 65 | `unknown` |
| Original + H1 violation probe | 32 | 33 | 839 | 66 | `unknown` |
| Original + H1 violation probe | 64 | 65 | 1,671 | 130 | `unknown` |

All calls exited process code 0 and printed exactly **`unknown`** (no per-bad verdicts). **Exit 0 here is not a successful safety result.** Under the fixed 20-second time limit these four questions remain unresolved. The generated-file fingerprints, exact counts and statuses are in `research/results/hv011_long_horizon_array_bmc.json`.

The earlier HV-010 **UNSAT** checks at depths through 16 stand; they do **not** imply safety at 32 or 64. The longer probes do not establish a reachable H1 counterexample either.

**Research interpretation:** Plain combinational time-unrolling of this word-level array design has hit a practical proof/solver limit within this setup. The next honest comparison is with established sequential induction/PDR/IC3 or certificate-producing word-level methods on the **same** source, time and memory budgets. Only a checker-accepted safety witness and then a rigorous competitive comparison could advance a substantive research claim. No new Witnora algorithm, performance benefit or novelty is asserted. Prior frozen combinational holdouts stay untouched.