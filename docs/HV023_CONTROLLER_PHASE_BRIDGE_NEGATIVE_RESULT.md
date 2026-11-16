# HV-023 — A legal one-hot predecessor does not imply the RAM-read pipeline stage

Date: 2026-11-16. This is a **negative one-step test**, not an unsafe hardware trace.
Predeclared in `docs/HV023_PREDECLARED_CONTROLLER_PHASE_BRIDGE.md` before the test.
Source: unchanged HV-021-admitted BTOR2 mirror, SHA-256 `cfa12d67ca508b686e2c2609962fac74919e7448ca8a379d2527cdeba65d58bc`.

## Candidate tested

The tempting timing lemma `comparison_enabled(t+1) => FSM_bit4(t)` was **FALSIFIED** by a fully specified *unrestricted predecessor* valuation with a **legal one-hot controller**.

- Previous FSM (state 14): decimal **8** (state bit3, not bit4). This is a valid one-hot code.
- Previous pp1_iter0 (state 112): **1**; counter (state 60): **0**; reset input3: **0**; previous icmp34 state176: **0**. Other required predecessor inputs/states set to zero except full_n input5=1.
- Original BTOR2 node 258: next FSM **16** (state bit4).
- Original node 308: next pp1_iter1 **1**.
- Original node 328: next terminal comparator **0**.
- Original node 262 evaluated on these next registers: comparison enable **1**.

The direct Boolean comparator expression and original node 262 agree.

**Meaning:** Merely proving controller one-hotness and comparison enable does **not** establish that the preceding clock was in stage bit4. An induction proof must either prove a stronger reachable-state entry/warm-up condition, or separately handle a first comparison cycle after entering stage4. This is a precision improvement to HV-022, not a novel scientific method.

**Safety caveat:** This is an unrestricted single-transition assignment. It has **NOT** been shown reachable from the specified initial state. It cannot establish an unsafe chip, negate previous bounded UNSAT results, or provide a full proof. No end-to-end Cerbtora witness, new algorithm, or speedup.

Reproduction values and exact source-node IDs: `research/results/hv023_phase_bridge_counterexample.json`. Previous frozen holdouts unchanged.

## Next sound gate

Construct and test the actual reachable entry-to-stage warm-up condition with original initialization and 26 transition equations, **then** the per-address RAM/shadow correspondence; submit any full invariant to the independently checking Cerbtora stack. Avoid declaring an equality invariant until the entry-cycle issue has been resolved.
