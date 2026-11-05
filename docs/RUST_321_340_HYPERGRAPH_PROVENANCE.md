# R-321–R-340: fail-closed hypergraph proof provenance

The shortest GF(2) subsystem witness is independently audited before proof
export. The audit requires canonical distinct source-row indices, an exact
complete original-CNF encoding for every selected XOR equation, retention of
every witness source clause in the original CNF, and an odd XOR dependency
with empty variable support. This is an additional safeguard; only the
independent RUP and real pinned `drat-trim` checker certify UNSAT output.

R-321–R-323 audit unary/ternary/quaternary source patterns. R-324–R-331
reject missing original clauses, incomplete/forged row metadata, duplicate,
unsorted and out-of-range indices, empty or algebraically consistent witnesses.
R-332–R-337 test seeded witness replay, source removal, exact proof budgets
and original CNF clause permutations. R-338 retains proof correctness under
additional non-XOR CNF; R-339 protects satisfiable controls; R-340 runs a
64-seed original-CNF RUP batch. Separate Rust and independent external checker
tests cover held-out cases.

**Local status:** 20 named tests and pinned external proof checker passed;
native CI pending. All interfaces remain research-only and bounded, the
Python path stays default, and no main-branch release is authorized.
