# Witnora-Core Theory Notes

## Strictness of W_1 over raw primal treewidth-1 formulas

Define the family F_n with variable mapping:

- x = 1
- y_i = i + 1 for 1 <= i <= n

The formula is:

```text
F_n =
(x or y_1 or y_2 or ... or y_n)
and
AND_{i=1..n} (not x or not y_i)
```

Let C be the long clause:

```text
C = (x or y_1 or ... or y_n)
```

For each i, let:

```text
D_i = (not x or not y_i)
```

The original primal graph P(F_n) contains a clique on:

```text
{x, y_1, ..., y_n}
```

This clique is created by the long clause C, because every pair of variables
appearing together in a clause is adjacent in the primal graph. The clique has
size n + 1, so the treewidth of P(F_n) is at least n.

The clause C is blocked on literal x. For every clause D_i containing not x,
the resolvent of C and D_i on x is:

```text
(y_1 or ... or y_n or not y_i)
```

This resolvent contains both y_i and not y_i, so it is tautological. Therefore
Blocked Clause Elimination removes C.

After removing C, the remaining formula is:

```text
AND_{i=1..n} (not x or not y_i)
```

Its primal graph is a star centered at x, with one edge from x to each y_i. A
star has treewidth 1.

Therefore F_n is in W_1 even though tw(P(F_n)) is unbounded as n grows. This
shows that the certified preprocessing collapse class W_1 strictly contains
formulas beyond the raw primal-treewidth-1 CNF base class.

This does not imply anything about P vs NP. It shows only that the implemented
certified preprocessing collapse class is strictly larger than the raw
bounded-treewidth base class for this explicit infinite family.
