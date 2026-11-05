# R-481–R-500: bounded research sign-off and unresolved questions

The final sign-off is an auditable **research gate ledger**, not 200 source-file
migrations or an algorithmic breakthrough. R-481–R-499 assert preserved Python
code, option defaults, 560-file manifest status totals, named contiguous gate
coverage, pinned independent external DRAT and focused CI workflow wiring.
R-500 executes `scripts.audit_witnora_r500` and the focused native CI.

Scientific findings and limitations:

1. R-301–R-340 finds exact smallest contradictory GF(2) row subsets under
   explicit caps and verifies source provenance. The DP state space is
   exponential in augmented linear rank in the worst case.
2. R-341–R-360 constructs matched-size XOR families with equal variable,
   constraint, clause and degree counts but different algebraic rank and
   exporter proof lengths. This is a structural diagnostic **for this method**,
   not a representation-independent general complexity measure.
3. R-361–R-380 establishes gauge and renaming invariance of the smallest
   contradictory subset and state count, while showing a negative result:
   20 of 64 seeded UNSAT gauge pairs changed exporter proof-clause count.
4. R-381–R-400 demonstrates exact resource ceilings; at 16 cycle variables
   the syndrome DP visits 65,536 states even though the candidate proof has
   only 31 clauses. Its cap is a refusal to search, not a SAT or UNSAT answer.
5. R-401–R-480 checks nonlinear background CNFs, disconnected contradictory
   components, independent Gaussian rank, and fail-closed original-source
   and proof-budget controls. These extend adversarial coverage without
   proving new asymptotic lower bounds.

Trust boundary: Python remains default. Native Rust is opt-in. Real independent
`drat-trim` verifies each original-CNF UNSAT candidate; internal RUP and
exhaustive truth-table oracles are additional controls. Lean/kernel proof
obligations, generalized SAT claims, and the full 560-file Python→Rust
migration remain unfinished.

Sign-off command:

```sh
python -m scripts.audit_witnora_r500
WITNORA_DRAT_TRIM=/path/to/pinned/drat-trim python -m unittest tests.test_r500_manifest_audit -v
```

Run the focused workflow on draft PR #122. A local static audit alone cannot
verify GitHub Actions execution or justify merging into `main`.

Verified research checkpoint: focused native GitHub Actions run
[#41963416866](https://github.com/joeyst8/witnora-core/actions/runs/41963416866)
completed successfully through R-500 on commit
`9c918f4f318fe58de1cb3243e8280e888f2416a4`.
