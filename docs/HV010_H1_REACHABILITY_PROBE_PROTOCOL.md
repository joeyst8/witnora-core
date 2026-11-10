# HV-010 — Preregistered H1 reachability probe

**Date:** 2026-11-10. Follows negative H1/H2 Cerbtora admission and bounded original-property UNSAT through depth 16.

On unchanged SHA-pinned 32-array BTOR2 development case, use the existing mechanical BMC unroller with an *additional* bad at each frame encoding the **H1 hypothesis violation**, `FSM_bit5 && !final_result_latch` (original BTOR2 nodes 27 and 22). Run exactly depths 0,1,2,4,8,16 with Bitwuzla 0.6.1, 20,000ms/2048MiB per model. Report original-bad and H1-probe verdicts independently, and verify generator gives same original bounded-bad results. A SAT probe would falsify H1 at that horizon, not necessarily original safety; all UNSAT probes would show only bounded H1 evidence, not induction or global invariance.

This is conventional bounded invariant falsification and is **not** a new theorem or technique. No untouched holdout case will be tested.