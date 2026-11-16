# HV-022B preregistration — terminal-cycle comparison suppression
Date: 2026-11-16 America/Chicago, after HV-022A local alignment checks, **before** the following exhaustively enumerated control tests.
Source: same SHA-admitted public BTOR2 mirror; unchanged transition.
Inspect original nodes 114 (counter i1 == 8), 157 (Boolean terminal), 306-309 (next stage-1 enable), 328-329 (latched terminal comparison), and 260-262 (result comparator enable).
Hypothesis B1: for every 4-bit counter c, reset r and stage-enable e0, original node 309 (next stage-1 enable) is exactly (!r) & e0 & (c != 8).
Hypothesis B2: original node 328 (next latched icmp34) is exactly (FSM_bit4 ? (c == 8) : old_icmp34). Original compare-enable node262 at the successor state can only be 1 if successor's stage-1 enable is 1; combined with B1 this implies previous counter != 8, e0=1 and !reset. This is a one-step property for arbitrary states, not an invariant or reachability theorem.
Controls: enumerate all 16 c, both reset bits, both e0 bits, both old comparator bits, both previous FSM_bit4 values, and both future FSM_bit4 values (512 cases). Include a mutant claim en1' = !reset&e0 (omitting sentinel exclusion), and require at least one counterexample at c=8.
Failure: any deviation of original expression from B1/B2 or lack of mutant rejection means this experiment fails.
Novelty: expected ordinary HLS pipeline control scheduling; no novelty, runtime win or chip-safety certificate claimed. Holdouts untouched.
