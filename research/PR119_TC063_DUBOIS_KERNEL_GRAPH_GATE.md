# TC-063: executable source-clause graph cut gate for Dubois20

Status: `LEAN_KERNEL_CHECK_PENDING`.

This experiment targets the last concrete graph trust boundary from the
previous two-component proof. A new Lean file,
`theory/TC063DuboisCheckedGraph.lean`, represents **every one of the 160
archived original source clauses**, as `CNF (Fin 60)` with original DIMACS
variable `i` represented by `Fin 60` index `i-1`.

It constructs an explicit graph-cut checker that scans every clause and every
ordered pair of literals within that clause. The generic Lean theorem
`checkNoCrossEdges_sound` proves that a `true` checker result implies the
previous module's semantic `NoCrossEdges` premise for any list CNF and
component-labeling function.

For the actual Dubois20 fixture, Lean then evaluates these obligations by
kernel reduction (using `decide`, **not `native_decide`**):

- `duboisGraphCheck`: all 1,440 within-clause ordered literal pairs obey the
  cut `{DIMACS variables 10,29}` and the A/B component labels.
- `duboisOwnerComplete`: all 60 variables, across **all four separator
  assignments**, are either fixed separator variables or assigned a
  component owner.
- `duboisNoEmptyResidual`: all four actual conditioned formulas have no
  empty reduced clause (the generic theorem separately treats such clauses
  as contradictions).
- `duboisOwnedResidualCover`: every reduced clause for every separator
  assignment is covered by exactly one of the two ownership classes using
  the previously kernel-checked generic graph-to-owner soundness theorem.

An independent regression test,
`tests/test_tc063_dubois_checked_graph_fixture.py`, verifies the Lean clause
array against all 160 source clauses in their archived order, their literal
signs and variable indices. Earlier fixtures separately check sourceGroup
four-clause encodings against the same 160-clause archive. The exact
decompressed DIMACS byte hash remains
`82059aba0e5773644b386eb6bcbe53680655390cb041873a3cb3e93f7bd896a7`.

## Important remaining boundaries

- Lean proves facts about the 160 source clauses **embedded in Lean**.
  The original DIMACS text parser, source SHA validation, JSON extraction
  certificate, and Python-to-Lean fixture generator/refinement still require
  formal verification. Python tests protect those boundaries meanwhile.
- These graph premises connect to the generic ownership theorem. The separate
  concrete G5/G14 proof already derives local contradictions and source
  UNSAT. A single unified theorem linking both represented data models and
  the operational Python recognizer remains future work.
- A concrete parity benchmark does not establish novelty, speed advantage,
  or universal SAT solvability. Full TC-063 remains restricted and open.
