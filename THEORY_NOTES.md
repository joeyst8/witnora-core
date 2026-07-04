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

## XOR Exact Pattern Soundness

Let `V = {x1, ..., xk}` and let `b` be either 0 or 1. The full CNF encoding of
the XOR equation

```text
x1 xor x2 xor ... xor xk = b
```

contains one clause for every Boolean assignment `a` to `V` with parity not
equal to `b`. The clause for `a` contains:

- `not xi` when `a(xi) = True`
- `xi` when `a(xi) = False`

That clause is falsified exactly by assignment `a` and satisfied by every other
assignment on `V`.

Therefore the conjunction of all forbidden-assignment clauses is satisfied
exactly by the assignments whose parity is `b`. It is equivalent, on the
variables `V`, to the XOR equation.

Witnora-Core v0.9.2 uses this fact conservatively. When it detects that a set
of CNF clauses exactly equals the full forbidden-assignment encoding for an XOR
equation, it may add that equation as an implied constraint while retaining the
source clauses in the CNF. This is satisfiability-preserving for SAT witnesses:
any final SAT assignment is still checked against the original CNF and the
detected XOR equations.

This is not heuristic XOR mining and not a CryptoMiniSat-style extractor.
Sidecar XOR equations have a different status: they define a combined
`CNF and XOR` input problem and are not claimed to be implied by the CNF alone.
XOR-native UNSAT remains native-only in v0.9.2 and is not claimed as DRAT,
LRAT, or FRAT certified.
