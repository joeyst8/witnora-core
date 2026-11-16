# HV-015 — Predeclared Pono 2.0 array-aware incumbent baseline

**Date:** 2026-11-10 America/Chicago. **Before any Pono solver run.** Pono 2.0 (tag `v2.0.0`, Git commit `c81aa363f4c1b1d4f05669478d9a94c16a0d4b44`) is a published, established SMT-based hardware model checker, not a Witnora invention.

**Source and frozen target:** Same unchanged SoSy-Lab `processed_hl_arr_access_32_arr.btor2`, GitLab benchmark commit `e19d110544fe7481763894f479b223aaa95fa582`, SHA-256 `93fb87c152dc8b7fc3e709f1d56a6ab1178ac782340a1b84b86ee69f8fa40c49`. No second array benchmark or combinational holdouts.

**Build gate:** Attempt to build the official Pono v2.0.0 release in *isolated scratch* with its documented `contrib/setup-smt-switch.sh`, `contrib/setup-btor2tools.sh`, and `configure.sh` procedures. Explicitly avoid MathSAT custom-licensed backend and any external proprietary binary. Use public Bitwuzla/cvc5 dependencies and cap build concurrency for limited memory. If build fails or requires unavailable privilege/credentials, stop safely and report inability to compare, not a solver failure.

**If build succeeds:** Freeze Pono CLI flags by inspecting `--help`, run the original model once with built-in **IC3SA (array-capable)** and once with **k-induction** under matched **20 seconds / ~2 GiB** per engine wherever CLI supports it. Capture process exit, literal verdict, wall time, exact command and tool commits. Do not claim a `safe` verdict is independently certified without Cerbtora-accepted witness; Pono 2.0 paper states it does not yet export safety witness circuits, though its API can expose invariants.

**Novelty gate:** IC3SA, array abstraction, syntax-guided reasoning, and invariant checking are existing science. This is a control for our benchmark, not a candidate new algorithm. Relevant originals: [Pono official repo](https://github.com/stanford-centaur/pono), [Pono 2.0 FM 2026](https://doi.org/10.1007/978-3-032-26220-2_1), [Cerbtora IJCAR 2026](https://doi.org/10.1007/978-3-032-32589-1_17).
