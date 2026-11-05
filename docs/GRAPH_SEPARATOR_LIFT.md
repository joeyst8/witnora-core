# Graph Separator Lift

v2.15 adds `G8_GRAPH_SEPARATOR_LIFT_PROTOTYPE`, promoted from v2.14's
`GRAPH_SEPARATOR_OBSTRUCTION -> GRAPH_SEPARATOR_LIFT` recommendation.

G8 uses the primal graph model:

- variables are graph nodes;
- two variables share an edge when they co-occur in a clause;
- removing the separator variables must produce valid components;
- every non-separator clause must belong to exactly one component;
- cross-component clauses not mediated by the separator are rejected.

## SAT Lift

For SAT lift, every component witness must be compatible with the same
separator assignment. The checker combines the separator assignment and the
component witnesses, then verifies the combined assignment directly against the
original CNF.

## UNSAT Cover

For UNSAT lift, one blocked separator assignment is not enough. The checker
requires every separator assignment to be listed and covered by at least one
verified component contradiction.

## Boundary

The G8 certificate is native. It is not a DRAT proof unless an external proof
against the original CNF is exported and checked. v2.15 does not claim graph
separator completeness, grid-coloring family theorems, lower bounds, hierarchy
completeness, or P vs NP progress.

Duplicate rows already handled by prior grammars are marked
`GRAPH_SEPARATOR_NO_NEW_DELTA`.

## Commands

```bash
python -m witnora_core.graph_separator_lift run --out-root outputs/v2.15-graph-separator-lift --strict
python -m witnora_core.graph_separator_lift check --cnf <original.cnf> --certificate <graph_separator_certificate.json>
```
