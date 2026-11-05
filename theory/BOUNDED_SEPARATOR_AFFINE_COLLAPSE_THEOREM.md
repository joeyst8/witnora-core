# Bounded Separator-Affine Collapse Theorem

v2.23 hardens TC-063 into `RESTRICTED_THEOREM_WITH_PROOF_OBLIGATIONS` by
factoring this proof sketch into formal lemma records and explicit proof
obligations. The theorem is still restricted to `SAF(c,r)` and is not an
unqualified proven theorem.

Status: `RESTRICTED_FAMILY_THEOREM_PROOF_SKETCH`

This is a restricted family theorem, subject to the stated `SAF(c,r)`
definition and native checker assumptions. It is not P vs NP progress, not a
complete SAT algorithm, not hierarchy completeness, and not DRAT.

## 1. Formal Definition SAF(c,r)

Let `c` and `r` be fixed constants. A CNF formula `F` belongs to `SAF(c,r)` if:

1. `F` has a variable separator `S` with `|S| <= c`.
2. Removing `S` from the primal graph decomposes the remaining variables into
   components `C_1, ..., C_k`.
3. For every assignment `alpha` to `S`, the residual formula `F|alpha`
   decomposes into independent component residuals.
4. Each residual component is an exact affine CNF over GF(2), with supported
   arity bound `r` or another exact affine extraction accepted by G5.
5. Clauses containing separator variables are substituted under `alpha`, then
   satisfied/removed or assigned to exactly one residual component.
6. No cross-component clause remains after separator assignment.

## 2. Theorem Statement

For every `F` in `SAF(c,r)`, Witnora can recognize the separator-affine
structure, enumerate all separator assignments, solve/check every residual
affine component using G5, and emit a native certificate that verifies SAT or
UNSAT under the rules below.

SAT: there exists one separator assignment `alpha` such that every residual
component is SAT. The combined witness `alpha` plus component witnesses is
verified against the original CNF.

UNSAT: every separator assignment `alpha` is covered by at least one residual
component with a verified affine UNSAT certificate.

## 3. Recognition Algorithm

For fixed `c`:

1. Build the primal graph.
2. Enumerate separator candidates of size at most `c`.
3. Remove each candidate separator and compute components.
4. For every separator assignment, substitute into the original CNF.
5. Reject if any residual clause spans multiple components.
6. Accept only if every residual component is exact affine under G5.

## 4. Collapse Algorithm

1. Enumerate all assignments to `S`.
2. For each assignment, solve/check every residual affine component.
3. If some assignment has all SAT components, lift and verify a SAT witness.
4. Otherwise, verify that every assignment has at least one affine-UNSAT
   component and emit the UNSAT cover.

## 5. Certificate Schema

The native certificate records formula hash, separator variables, primal graph
summary, component decomposition, every separator assignment, residual
component affine certificates, SAT witness lift or UNSAT cover, polynomial
bound record, theorem reference, checker status, and claim boundary.

## 6. Checker Algorithm

The checker reconstructs the primal graph, recomputes components, substitutes
every separator assignment into the original CNF, verifies residual component
locality, checks each G5 affine certificate, verifies SAT witnesses against the
original CNF, verifies complete UNSAT covers, and rejects forbidden claims.

## 7. Polynomial Bounds

Candidate separator enumeration costs `O(n^c)`. Separator assignment
enumeration costs `2^c`. Component affine checking is polynomial for fixed
supported affine arity/extraction bound `r`. Therefore recognition and checking
are polynomial for fixed `c` and supported `r`.

The exponential dependence on `c` is explicit and not hidden.

## 8. Soundness Proof Sketch

For a fixed separator assignment, substitution preserves satisfiability under
that assignment. Residual clauses localize to independent components by the
SAF(c,r) condition. Each component result is checked by G5 against exact affine
CNF evidence.

If one assignment makes every component SAT, the union of component witnesses
with the separator assignment satisfies every residual clause. Direct
verification against the original CNF discharges the SAT claim.

If every separator assignment has at least one affine-UNSAT component, then no
assignment to the separator can extend to a full satisfying assignment. Since
all separator assignments are covered, the original formula is UNSAT.

## 9. Completeness Within Family Proof Sketch

For `F in SAF(c,r)`, the recognition algorithm eventually enumerates the
witness separator `S`. By definition, every separator-conditioned residual
component is exact affine and accepted by G5. The collapse algorithm enumerates
all separator assignments. If `F` is SAT, some separator assignment has all
components SAT and yields a lifted witness. If `F` is UNSAT, every separator
assignment must fail in at least one component, producing the complete cover.

## 10. Limitations

The theorem is restricted to `SAF(c,r)`. It does not cover arbitrary separator
formulas, arbitrary PB/cardinality encodings, non-exact affine encodings,
random SAT, circuit-SAT, or formulas requiring lower-bound/proof-complexity
arguments outside the family.

## 11. Nonclaims

- No P vs NP progress.
- No polynomial-time SAT for arbitrary formulas.
- No all-SAT claim.
- No hierarchy completeness claim.
- No DRAT claim unless externally checked.
- No unqualified theorem-proven claim.
- Finite tests do not substitute for the family proof sketch.
