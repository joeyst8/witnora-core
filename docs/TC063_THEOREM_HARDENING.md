# TC-063 Theorem Hardening

v2.23 hardens `TC-063 Bounded Separator-Affine Collapse Theorem`.

The hardened status is `RESTRICTED_THEOREM_WITH_PROOF_OBLIGATIONS`, not
`THEOREM_PROVEN_UNQUALIFIED`.

TC-063 remains restricted to `SAF(c,r)`: fixed separator bound `c` and
supported exact affine extraction bound `r`. Polynomiality holds only for fixed
`c`; the exponential dependence on `c` is explicit.

The hardening package adds formal lemma statements, proof-sketch-to-obligation
mapping, a structural SAF membership validator, polynomial bound accounting,
explicit dependency on G5 affine checker soundness, scaling evidence for
`n=64` and `n=128`, and stricter claim-boundary checks.

Scaling tests support implementation behavior only. They do not substitute for
proof. Native certificates are not DRAT/LRAT/FRAT proofs unless exported and
externally checked.

Nonclaims: no P vs NP progress, no all-SAT claim, no hierarchy completeness,
no polynomial-time SAT for arbitrary formulas, and no unqualified theorem-proven
claim.
