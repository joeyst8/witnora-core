# HV-022 — Predeclared register-alignment and sentinel-index audit
Date: 2026-11-16 (America/Chicago). This preregistration precedes the executable sample-based audit. Development benchmark only; frozen holdouts untouched.

## Purpose
Investigate the actual memory/pipeline consistency obligation downstream of HV-021, using unchanged admitted public BTOR2 mirror (GitHub `CyanoKobalamyne/hwmcc-benchmarks`, revision `57174f5d6f575aedcfe83694b35ec8e7b83043fc`, path `array/2024/hku/safe/processed_hl_arr_access_32_arr.btor2`). Do not modify model, semantics, transitions, or original bad predicate.

## Sanity/known facts to check from parsed source
- `318 sort array 81 6`, with `81 sort bitvec 3` and `6 sort bitvec 8`: RAM is indexed by **3 bits (8 addresses), data 8 bits**, regardless of filename `32_arr`. Prior descriptions of a 32-element array were too loose; correct this explicitly.
- `153 = state112 & FSM_bit4` is stage-1 enable; `194` selects address from stage-1 counter state60 when 153, and `197=153|40` is RAM-read enable.
- `316` is next register 164 (expected/phi); `321` is next register 165 (RAM output). `311` and `314` are selection gates based on high counter bits and terminal comparison `114=(state60 == 8)`.
- Hypothesis H4: Under 153 with counter state60 in [0,7], the truth of `next(q0)==next(phi)` is exactly equality of `RAM[counter_low3]` and the selected shadow register. Counter 8 is a distinct terminal/sentinel case: next(phi) uses unconstrained input310 and RAM reads address0; unconditional equivalence can fail.
- Try a deliberate invalid hypothesis H4-mutant: equality holds at the terminal index 8 regardless of input310; require a concrete counterexample.

## Method and gates
1. Fetch the same public source via the connected GitHub integration, parse every node (sort, input, state, combinational expression, init/next/bad). Fail closed if expected source equations/widths or node labels differ.
2. Evaluate the *original BTOR2* node graph with deterministic pseudorandom state assignments (including arbitrary 8-byte arrays), using exact finite bit-vector widths, and check H4 across all nine counter values 0..8, both 153=0 and 153=1 where meaningful, plus both other-read conditions. Include a held-out wrong candidate to ensure test rejects a false identity.
3. If H4 holds in samples, derive it symbolically by substitution of nodes 194,197,316,321. Note this is a **conditional identity from existing transition logic**, not a reachability or inductiveness theorem. If a counterexample occurs, record and revisit, do not claim proof.
4. Report the first concrete sentinel counterexample, if obtained, without printing any sensitive data. Publish reproducible source, result counts, and a proposed full-chip invariant trial.
5. Do not run new model checker, claim full safety, novelty, or speedup unless an actual independently checked certificate is produced. Explicitly keep historical HWMCC24 timeouts distinct from current results.
