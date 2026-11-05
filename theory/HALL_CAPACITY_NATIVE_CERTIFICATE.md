# Hall / Capacity Native Certificate

This note states the proof-sketch shape used by the v2.5
`G4_ORBIT_CAPACITY_COUNTING_PROTOTYPE` checker.

## Setting

The CNF contains assignment variables `x[item,resource]`.

For each item `i` in a demand subset `S`, the original CNF contains an
at-least-one clause saying that `i` must choose one allowed resource in `N(i)`.

For each resource `r` in the neighborhood `N(S)`, the original CNF contains
capacity clauses proving that at most `cap(r)` of the items using `r` may select
it.

## Certificate

The certificate records:

- the assignment-variable grid;
- the demand subset `S`;
- the neighborhood `N(S)`;
- resource capacities;
- source-clause identifiers for demand and capacity obligations;
- the counts `|S|` and `capacity(N(S))`;
- the inequality `|S| > capacity(N(S))`.

## Soundness Sketch

Every satisfying assignment would need to assign each item in `S` to at least
one resource in `N(S)`. The capacity clauses restrict the total number of items
that can be assigned into `N(S)` to at most `capacity(N(S))`. If
`|S| > capacity(N(S))`, no assignment can satisfy all recorded clauses.

The checker verifies the source clauses and the arithmetic. It does not rely on
heuristic orbit merging, and it does not emit a DRAT claim.

## Scope

This is a native certificate for the provided subset `S`. It is not a complete
matching solver, allocation solver, arbitrary pseudo-Boolean solver, lower-bound
theorem, or P vs NP result.
