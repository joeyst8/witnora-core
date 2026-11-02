# TC-063 G5/G14: genuine two-component separator on archived Dubois20

Status: `LEAN_KERNEL_CHECK_PENDING` pending GitHub Actions verification.

## Structure found without supplying a separator

From the 40 archived source-exact XOR equations for the 160-clause / 60-variable
Dubois20 CNF, reconstruct the primal graph (pairwise edges among variables in
each three-literal source clause). An exhaustive vertex-cut audit finds:

- Connected primal graph of 60 variables and 118 edges.
- No one-variable articulation points.
- Nineteen two-variable cuts; `{10,29}` splits it into equally sized
  connected components of 29 remaining variables each.
- A: equation groups `0..9` and `30..39` (20 groups, 80 source clauses).
- B: equation groups `10..29` (20 groups, 80 source clauses).
- All groups belong exclusively to A or B after eliminating separator
  variables 10 and 29. The four groups containing separator literals are
  `9`, `10`, `29`, `30`.

Each component's own XOR equations cancel all internal variables, yielding:

| Component | Aggregate XOR consequence | If separator XOR is... |
| --- | --- | --- |
| A | `x10 XOR x29 = 1` | `0`: A is UNSAT |
| B | `x10 XOR x29 = 0` | `1`: B is UNSAT |

Thus all **four separator assignments** have a refuted component. The
contradiction is established by two **independent local G5 derivations**;
neither local proof uses the original full-CNF UNSAT theorem.

## New Lean claims

`theory/TC063DuboisTwoComponentCover.lean` proves:

1. `source_component_iff`: the exact 40-group original source formula is the
   conjunction of the two disjoint 20-group source components.
2. `componentA_separator_parity`: the 20 A source-clause groups imply
   `x10 XOR x29 = true`, via their exact CNF→XOR lemmas and G5 trace steps.
3. `componentB_separator_parity`: the 20 B source-clause groups imply
   `x10 XOR x29 = false`, via their own exact CNF→XOR lemmas and an explicit
   nine-step pair-propagation derivation.
4. `componentA_exact` / `componentB_exact`: literal substitution into each
   component is definitionally equal to its source clauses when given the
   separator's current values.
5. `source_two_component_exact`: no original clause is dropped or introduced
   when composing the two residuals at the separator's true assignment.
6. `two_bit_assignment_cover`: all four Boolean separator assignments refute
   at least one substituted component.
7. `dubois20_two_component_unsat_cover`: source UNSAT follows from this G14
   branch cover, without citing global `source_unsat` or full-certificate
   `certificate_inconsistent`.

`tests/test_tc063_dubois_two_component.py` audits the original equation
fixture, ownership, 29/29 connectivity, literal replacement, 20+20 row
partition, aggregate GF(2) consequences, and coverage of four assignments.

## Limitations / next objective

This is a concrete **end-to-end example** of the desired G14 component logic,
not the universal `SAF(c,r)` theorem. In particular, Python currently checks
graph construction and component ownership; Lean currently takes the two
explicit source-component definitions and proves their exact composition.
The indexed DIMACS parser/refinement, arbitrary separator recognition and
graph decomposition, generic local G5 checker, bounded-class complexity, and
Python-to-Lean implementation correspondence remain open. The selected
benchmark is a deliberately structured parity contradiction, not evidence of
new solver speed on general SAT instances. The exact original DIMACS byte
hash remains
`82059aba0e5773644b386eb6bcbe53680655390cb041873a3cb3e93f7bd896a7`.
