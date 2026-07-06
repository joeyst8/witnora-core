# Graph Separator Lift Certificate

The v2.15 graph-separator certificate is a native separator-lift certificate
for finite rows.

## Soundness Obligations

Given a CNF formula `F` and separator `S`, the checker reconstructs the primal
graph and verifies that removing `S` creates the claimed components. Each
non-separator clause must be assigned to one component. A clause whose
non-separator variables span multiple components is an invalid cross-component
clause and the certificate is rejected.

## SAT Witness Lift

If each component has a witness under the same separator assignment, then the
candidate global assignment is the union of:

- the separator assignment;
- each component witness.

The checker does not trust this by construction. It verifies the combined
assignment against the original CNF.

## UNSAT Separator Cover

For UNSAT, the certificate must cover every possible separator assignment. For
each assignment, at least one component must have a verified contradiction
after conditioning on that separator assignment.

This is a native covering argument. It is not a DRAT proof.

## Non-Claims

G8 is a prototype. It does not prove a family theorem, graph-separator
completeness, lower bounds against prior grammars, hierarchy completeness, or
P vs NP progress.
