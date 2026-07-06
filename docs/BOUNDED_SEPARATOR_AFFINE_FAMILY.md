# Bounded Separator-Affine Family

v2.22 introduces `G14_BOUNDED_SEPARATOR_AFFINE_FAMILY_THEOREM`.

This is a restricted infinite-family theorem layer, not a general SAT solver
and not a new broad separator operator. The family is `SAF(c,r)`: CNFs with a
variable separator `S` of size at most fixed `c`, such that every assignment to
`S` leaves independent residual components that are exact affine CNFs accepted
by G5 under supported arity bound `r`.

## SAT Rule

SAT is certified only when there exists one separator assignment `alpha` for
which every residual component is SAT. Witnora combines `alpha` with component
witnesses and verifies the full assignment against the original CNF directly.

## UNSAT Rule

UNSAT is certified only when every separator assignment is covered: for each
`alpha`, at least one residual component has a verified affine UNSAT
certificate. One blocked assignment is not enough.

## Polynomial Boundary

Recognition enumerates separator candidates and all separator assignments. The
bound is polynomial only for fixed separator bound `c` and supported exact
affine extraction bound `r`. The exponential dependence on `c` is explicit.

## Nonclaims

v2.22 does not prove P vs NP, all SAT, hierarchy completeness, arbitrary
separator collapse, or DRAT. Native separator-affine certificates are native
unless an external proof is exported and checked.
