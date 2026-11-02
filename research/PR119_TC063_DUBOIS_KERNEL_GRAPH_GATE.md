# TC-063: executable source-clause graph cut gate for Dubois20

Status: `LEAN_KERNEL_CHECKED_BOTH_CONCRETE_GRAPH_CUTS`.

Final verified run: [GitHub Actions #41495709189](https://github.com/joeyst8/witnora-core/actions/runs/41495709189),
commit `b55779a42d0465a17acef0b677a1df0ec1e87b3d`.
All prior proof and fixture steps passed. The three new source/recognizer
fixture checks and both explicit graph-ownership cut theorems passed Lean
4.35.0. Each final ownership theorem reports only standard Lean axioms
`[propext, Classical.choice, Quot.sound]`, with **no `sorryAx`**.

The initial `{10,29}` graph gate passed all Lean compilation steps at
[run #41494881662](https://github.com/joeyst8/witnora-core/actions/runs/41494881662),
commit `3716addf09174515ce9b7dda0e2331fca2cda3c5`.
Its final theorem printed standard axioms `[propext, Classical.choice,
Quot.sound]` with no `sorryAx`.

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

## The actual Python recognizer output

Running `recognize_separator_affine_family` on the exact archived 160 clauses
with `(c=2,r=3)` returned `SEPARATOR_AFFINE_FAMILY_RECOGNIZED` and its *first*
valid cut `{DIMACS variables 1,38}` in approximately 3.5 seconds (97
candidates examined). This is a correct cut but it splits the graph into
**56 and 2** variable components, instead of the **29 and 29** yielded by
our chosen cut `{10,29}`.

The Lean fixture now includes both cuts. Its additional
`recognizedGraphCheck`, `recognizedOwnerComplete`,
`recognizedNoEmptyResidual`, and `recognizedOwnedResidualCover` theorems
kernel-check the exact graph premise and all four residual assignments for
the recognizer's actual selected separator. A separate Python regression
test reconstructs the full formula through the real recognizer and asserts
the recognized cut matches the Lean fixture; if the recognizer's selection
policy changes, the fixture must be re-audited.

Potential performance experiment: compare first-valid separator versus a
balanced-cut policy under **full recognizer time plus all residual component
certificate checks**. No speed claim is justified by the balance difference
alone; searching additional candidates could cost more than it saves.

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
