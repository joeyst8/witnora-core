# Proof Motif Generalization Certificate

The v2.18 certificate format is native to Witnora. It is designed to make
proof-motif generalization auditable without trusting similarity.

## Certificate Principle

A generalized motif is trusted only after expansion checks. The checker must
verify:

1. the formula hash matches the original CNF;
2. base motif source clauses exist;
3. generalized template parameter constraints are satisfied;
4. substitutions do not merge variables unsafely;
5. every reuse site expands into valid concrete resolution steps;
6. every derived lemma matches the instantiated proof;
7. the final macro contradiction uses only verified reuse sites.

## Diagnostic Boundary

Near-repetition is useful as obstruction evidence, but it is not proof. Rows
with loose similarity and no checked expansion remain
`PROOF_MOTIF_GENERALIZATION_DIAGNOSTIC_ONLY`.

## Claim Boundary

The certificate is not DRAT unless an external proof against the original CNF
is separately exported and checked. v2.18 makes no theorem, strictness,
completeness, lower-bound, or P vs NP claim.
