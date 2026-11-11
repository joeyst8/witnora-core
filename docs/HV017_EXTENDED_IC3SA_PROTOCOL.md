# HV-017 — Predeclared extended incumbent IC3SA calibration

**Date:** 2026-11-10 America/Chicago. **Registered before solver run.**

HV-015/016 found that first-party Pono 2.0 (published FM 2026) using Bitwuzla returned UNKNOWN after its default 10-frame bound and then hit a 20-second timeout with `--bound 1000000` on the unmodified HKU array BTOR2 model. Before attempting a Witnora algorithmic hypothesis, test whether this established array-aware IC3SA solver decides the target with an extended but controlled budget.

- **Frozen model:** SoSy-Lab `processed_hl_arr_access_32_arr.btor2`, SHA256 `93fb87c152dc8b7fc3e709f1d56a6ab1178ac782340a1b84b86ee69f8fa40c49`. One bad property `b0`. Do not add assumptions or strengthen property.
- **Frozen incumbent:** Pono 2.0 tag `v2.0.0` commit `c81aa363f4c1b1d4f05669478d9a94c16a0d4b44`, its built-in IC3SA, Bitwuzla public backend commit `122f27f9518269cd9c1ebf0efced37dfd7f845e6`.
- **Exactly one run:** `./build/pono --engine ic3sa --bound 1000000 --smt-solver bzla --show-invar <pinned model>`.
- **Limits:** external `timeout --signal=TERM --kill-after=2s 120s`, `ulimit -v 2097152` (2 GiB virtual address cap). Record stdout, stderr, exit, verdict, and approximate wall time. An OS timeout is UNKNOWN. The `--show-invar` flag only requests Pono's candidate invariant if it prints `unsat`; that is NOT an independent witness. No second run or property retuning.
- **Scientific interpretation:** A successful `unsat` from an established engine means Witnora must treat it as incumbent proof claim, requiring separate independent certification. An UNKNOWN still says nothing about safety and does not prove a new method could work. Only future predeclared same-budget comparisons with independent certificate validation can support Witnora progress.
