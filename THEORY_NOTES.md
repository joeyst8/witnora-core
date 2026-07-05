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

Witnora-Core v0.9.3 uses this fact conservatively. When it detects that a set
of CNF clauses exactly equals the full forbidden-assignment encoding for an XOR
equation, it may add that equation as an implied constraint while retaining the
source clauses in the CNF. This is satisfiability-preserving for SAT witnesses:
any final SAT assignment is still checked against the original CNF and the
detected XOR equations.

This is not heuristic XOR mining and not a CryptoMiniSat-style extractor.
Sidecar XOR equations have a different status: they define a combined
`CNF and XOR` input problem and are not claimed to be implied by the CNF alone.
XOR-native UNSAT remains native-only unless a separate proof bridge verifies.
v0.9.3 adds such a bridge only for detected-CNF XOR contradictions whose source
clauses are already present in the original CNF.

## Bounded XOR-to-DRAT Bridge Soundness

For detected-CNF XOR equations, the exact source clauses are part of the
original formula. If those detected XOR equations are inconsistent, Witnora may
use Gaussian elimination to guide a bounded resolution/RUP proof construction
from those source clauses.

Gaussian elimination is not treated as the certification authority. A DRAT
claim is accepted only when:

- the proof base is `original.dimacs`,
- every claimed XOR equation used by the bridge came from detected CNF source
  clauses already present in the original formula,
- the generated `proof.drat` passes Witnora's internal RUP-subset checker, and
- real `drat-trim` verifies `proof.drat` against `original.dimacs`.

If any of these checks fails, or if the proof exceeds the configured width or
proof-size cap, Witnora falls back to native XOR UNSAT and does not claim DRAT
verification.

v0.9.3.1 separates public labels from internal route labels. A detected-CNF XOR
contradiction may be discovered by the native XOR route, but if real
`drat-trim` verifies the exported proof against `original.dimacs`, the public
benchmark category is `UNSAT_DRAT_EXPORTED_VERIFIED`. Native-only XOR
contradictions, including sidecar-only contradictions that define a combined
`CNF and XOR` problem, are reported separately as `UNSAT_XOR_NATIVE_ONLY` and
are not counted as externally verified original-CNF UNSAT.

Sidecar XOR equations do not have this status. They define a combined
`CNF and XOR-sidecar` problem. Without first encoding those sidecar equations
into a combined proof base, a sidecar contradiction must not be claimed as an
original-CNF DRAT proof.

## v0.9.4 Diagnostic Claim Boundary

The official CNFgen XOR diagnostic is a measurement artifact, not a theorem
upgrade. It can show that a particular instance moved from `NO_COLLAPSE_FOUND`
to `UNSAT_XOR_NATIVE_ONLY` or to `UNSAT_DRAT_EXPORTED_VERIFIED`, but only the
latter is externally DRAT verified against `original.dimacs`. A diagnostic
proof-cap skip is not a hardness statement and not a DRAT failure theorem; it
only means Witnora did not export a bounded proof under the configured cap.

## v0.9.5 Tseitin Certification Claim Boundary

v0.9.5 does not add a new XOR detection theorem. It takes exact detected-CNF
XOR equations already present in official CNFgen Tseitin encodings and attempts
to certify the resulting XOR contradiction through a bounded resolution proof.
For a detected-CNF XOR row to count as externally certified, `proof.drat` must
verify with real `drat-trim` against `original.dimacs`.

The v0.9.5 proof bridge may turn a row such as `tseitin_10` from
`UNSAT_XOR_NATIVE_ONLY` into `UNSAT_DRAT_EXPORTED_VERIFIED`. Larger rows remain
native-only if they exceed explicit row-width, proof-size, proof-byte, or time
caps. Such a cap result is not a hardness claim and not a claim that no DRAT
proof exists.
