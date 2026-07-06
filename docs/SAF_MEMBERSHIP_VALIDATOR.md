# SAF Membership Validator

`witnora_core.tc063_theorem_hardening.validate_saf_membership` validates
structural membership in `SAF(c,r)`.

The validator reconstructs the primal graph, checks or discovers a separator
`S` with `|S| <= c`, computes components after removing `S`, enumerates all
separator assignments, substitutes each assignment into the original CNF,
localizes residual clauses, rejects cross-component residual clauses, and
checks every residual component through the G5 exact affine checker path.

The validator is structural. It does not by itself certify SAT or UNSAT. SAT
and UNSAT claims require the TC-063 separator-affine certificate and checker.

Accepted validation status: `SAF_MEMBER_VERIFIED`.

Rejected validation status: `SAF_MEMBER_REJECTED`.

No P vs NP, all-SAT, hierarchy-completeness, DRAT, or unqualified theorem
claim is made by the validator.
