# R-039: native bounded failed-literal probing

**Verified green:** https://github.com/joeyst8/witnora-core/actions/runs/41770881275

## Actual module conversion

Previously untouched `witnora_core/forced_relation_probe.py`
now has an independent Rust counterpart at
`rust/witnora-ve/src/failed_literal_probe.rs`.

The port supports assumption-driven unit-conflict detection, variable
priority by descending source incidence, a bounded candidate list,
positive/negative assumption contradiction tests, justified forced
unit additions, the both-assumptions-conflict sentinel, final unit
propagation and canonical candidate SHA-256 identity. Audit metadata
matches the original Python fields. The adapter is opt-in only.

This is **standard** failed-literal inference and preserves
satisfiability, **not** necessarily the original set of assignments.
No novelty or Lean proof is claimed.

## Verification evidence

`tests/test_forced_relation_rust.py` exercises **1,000** seeded
CNF inputs, compares direct unit-conflict results against Python,
and checks the exact final candidate CNF and all metadata for
bounded probes. Contradictory units and invalid probe budgets
are independently tested. A Rust ownership compile error discovered
in the first CI attempt was fixed before the successful final run.
The entire Rust/Python/Ganak workflow passed.

## Trust and inventory

**27** parallel Rust reference modules, **533** original Python
files still not migrated and **0** originals retired. The default
Python algorithms, final verifier and Lean trust remain unchanged.
