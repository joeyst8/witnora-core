# HV-010 — Frozen bounded-chip trace diagnostic (before run)

**Date:** 2026-11-10. Development-only analysis of the same HKU HLS `processed_hl_arr_access_32_arr.btor2` SHA-256 `93fb87c152dc8b7fc3e709f1d56a6ab1178ac782340a1b84b86ee69f8fa40c49`.

H1 and H2 strengthening witnesses both failed Cerbtora's **step** check (all other checks passed). That failure alone does not establish a reachable bug or prove safety. We identified that write-enable node31 together with result latch node22 can make the helper bad node48 true in a next state, and verifying prevention of this may depend on the array datapath, not just an FSM.

**Frozen bounded diagnostic:** translate the exact source BTOR2 transition system mechanically to combinational BTOR2 over time frames `k = 0,1,2,4,8,16`. Preserve every input/state/transition/init and include `bad` in every frame. Check each unrolling with Bitwuzla 0.6.1 built in HV-009 using a **20-second** time limit and **2 GiB** memory cap per depth. Report SAT, UNSAT, UNKNOWN/timeout separately, include command and SHA of generation script. Do not modify held-out designs. One bounded UNSAT is not an unbounded proof; a SAT claim requires checking the generated trace rather than relying on the user-facing benchmark YAML label.

The unroller must validate original SHA, enforce unique topological IDs and preserve SMT theory sorts including arrays. No novel algorithm or speedup is claimed for bounded model checking.