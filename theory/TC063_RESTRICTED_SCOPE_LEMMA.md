# TC-063 Restricted Scope Lemma

Status: `FORMALIZED_PROOF_SKETCH`

TC-063 applies only to `SAF(c,r)`, not all SAT, not arbitrary separators, not
unbounded `c`, and not arbitrary affine-looking formulas.

Proof obligations:

- Reject or mark non-SAF inputs diagnostic-only.
- Reject fake completeness, P vs NP, and all-SAT claims.
- Reject HARD/UNKNOWN statuses.
