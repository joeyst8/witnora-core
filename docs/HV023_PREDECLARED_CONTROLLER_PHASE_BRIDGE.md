# HV-023 preregistration — controller-phase bridge falsification
Date: 2026-11-16 America/Chicago. Development case only; frozen holdouts untouched. Committed before the test.

Question: Does `comparison_enable(t+1)` necessarily imply `FSM_bit4(t)`, even when the *preceding* FSM encoding is legal one-hot? This is a possible but unproven bridge between HV-022's local datapath equality and the actual comparison event.

Frozen test:
1. Use the same SHA-256 admitted BTOR2 source as HV-021/022; no model modifications.
2. Exact predecessor value test: controller state14=8 (legal one-hot bit3), pp1_iter0 state112=1, counter state60=0, ap_rst input3=0, old icmp34 state176=0, all unspecified state/input values may be 0. Evaluate original next FSM `258`, next pp1_iter1 `308`, and next icmp34_reg `328`; evaluate original compare-enable expression `262` in resulting successor state.
3. Original invalid candidate: `comparison_enable(t+1) => FSM_bit4(t)`. If next comparison is 1 while old FSM_bit4 is 0, the candidate is falsified, even though old FSM is one-hot. Report as an *unrestricted predecessor-state counterexample*, NOT a reachable execution from reset.
4. If falsified, do not carry the false bridge into an invariant. The remaining reachability obligation must cover entry-to-stage pipeline warm-up separately.
5. Positive control: compare-enabled formula with next FSM4, next enable, and not-next terminal comparator should match node 262.
No unbounded-safety or benchmark-safe claim, novelty or performance claim permitted.
