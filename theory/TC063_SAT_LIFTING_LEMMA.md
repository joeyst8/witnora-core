# TC-063 SAT Lifting Lemma

Status: `FORMALIZED_PROOF_SKETCH`

If there exists one separator assignment `alpha` such that every residual
component under `alpha` is SAT, then the union of `alpha` and all component
witnesses satisfies the original CNF, provided the combined assignment is
verified against the original CNF.

Proof obligations:

- Component variable sets are disjoint outside `S`.
- Component witnesses agree with `alpha`.
- No cross-component residual clause remains.
- Final original-CNF witness verification passes.
