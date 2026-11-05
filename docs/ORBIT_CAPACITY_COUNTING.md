# Orbit Capacity Counting

v2.5 introduces `G4_ORBIT_CAPACITY_COUNTING_PROTOTYPE`, the first implemented
prototype promoted from the v2.4 Operator Genesis queue.

## Operator Origin

The candidate was generated as `ORBIT_COUNTING_COLLAPSE`. v2.5 implements the
safe core of that idea as native Hall/capacity-deficit certification.

## Formula Shape

The supported prototype uses assignment variables:

`x[item,resource] = item is assigned to resource`

For each item in the recognized structure, the original CNF must contain an
at-least-one clause over its allowed resources. For each resource, the original
CNF must contain exact capacity clauses. Capacity one is represented by full
pairwise AMO clauses; capacity greater than one is accepted only for the exact
generated at-most-c encoding checked by the certificate verifier.

## Native Deficit Certificate

For a subset `S` of items, the checker expands:

- every item in `S`;
- the allowed-neighborhood resources `N(S)`;
- every source ALO clause for the items in `S`;
- every capacity clause for resources in `N(S)`;
- the arithmetic comparison `|S| > capacity(N(S))`.

If all obligations pass, the public category is
`UNSAT_ORBIT_CAPACITY_NATIVE_CERTIFIED`.

## Orbit Compression Boundary

Orbit summaries help discover and display the deficit. They are not trusted by
themselves. If orbit compression is used, the checker must expand the compressed
evidence back to concrete items, resources, clauses, and capacities.

## Duplicate Controls

Complete matching formulas such as `complete_match_3_2` duplicate the G3
standard pigeonhole pattern. They are marked
`DUPLICATE_OF_G3_PIGEONHOLE_PATTERN` or `G4_NO_NEW_DELTA` and are not counted as
the main v2.5 operator jump.

## Claim Boundary

v2.5 does not claim:

- DRAT verification for orbit-capacity rows;
- a full matching solver;
- a full allocation solver;
- a complete Hall theorem solver over arbitrary CNF;
- a G4 strictness theorem;
- P vs NP progress.

The allowed claim is a native, checker-backed Hall/capacity-deficit certificate
for exact generated assignment CNFs.
