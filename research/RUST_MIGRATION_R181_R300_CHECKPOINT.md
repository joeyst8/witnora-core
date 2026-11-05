# Witnora R-181–R-300 research verification checkpoint

This ledger extends the verified R-180 migration research frontier with
**120 named research/testing checkpoints**, not 120 newly migrated original
Python files. The research default stays Python; Rust proof generation is
an opt-in candidate backend; independent RUP and external `drat-trim` proof
checks, Lean obligations and source-CNF identity remain trust boundaries.

| Frontier | New research evidence | Verification |
| --- | --- | --- |
| R-181–R-200 | 20 independently enumerated source-CNF/SAT proof controls; 480 mixed SAT/UNSAT seeded cases with native comparison | Focused CI [#41955093214](https://github.com/joeyst8/witnora-core/actions/runs/41955093214) green |
| R-201–R-220 | Real pinned external DRAT acceptance, forged proof rejection, exact resource-cap controls | Focused CI [#41955834503](https://github.com/joeyst8/witnora-core/actions/runs/41955834503) green |
| R-221–R-240 | Complete contradictory XOR original-CNF proof scaling, widths 1–10; measured `2**w-1` proof clauses | Focused CI [#41956471056](https://github.com/joeyst8/witnora-core/actions/runs/41956471056) green |
| R-241–R-260 | Sparse chain, `2*n` source clauses, `n` proof clauses through 80 variables | Focused CI [#41956982135](https://github.com/joeyst8/witnora-core/actions/runs/41956982135) green |
| R-261–R-280 | Shortest odd-parity cycle witness and full-original-CNF proof; example 40-vertex proof shrinks 67 to 21 clauses | Focused CI [#41957568052](https://github.com/joeyst8/witnora-core/actions/runs/41957568052) green |
| R-281–R-299 | Independent exhaustive minimum odd-cycle oracle; 72 held-out contradictory graphs, 24 SAT controls, 16 improvements and no regressions in the sample | Focused CI [#41958473142](https://github.com/joeyst8/witnora-core/actions/runs/41958473142) green |
| R-300 | Manifest accounting, gap-free test names, pinned checker/workflow audit and original sources preserved | Focused CI [#41958473142](https://github.com/joeyst8/witnora-core/actions/runs/41958473142) green |

Independent external `drat-trim` is pinned to upstream revision
`2e3b2dc0ecf938addbd779d42877b6ed69d9a985` in the focused workflow.

## Scientific interpretation

- The exponential proof growth in the full width-`w` contradictory XOR family
  reflects a *complete CNF input that itself has `2**w` clauses*. It is not
  a resolution lower-bound theorem.
- Sparse chains and cycle-guided selection show a contrasting linear-sized
  family and smaller certificates on frozen synthetic graphs. Such finite
  evidence does not establish general computational advantage.
- The shortest-cycle witness selector only applies to explicitly encoded
  **binary XOR graph edges**; it is not a general SAT proof shortcut.
- A DRAT proof is accepted only by an actual independent checker over the
  unchanged original CNF; the Python/Rust differential is an additional
  consistency check, not the independent final verifier.

## Unchanged migration accounting

- Original Python files preserved: **560**.
- `not_migrated`: **470**.
- `parallel_reference`: **76**.
- `partial_native_verified`: **14**.
- No original Python source file migrated by the 120 new test milestones.
- Not a completed full Python-to-Rust migration, formal Lean proof, P-vs-NP
  result, release approval, or permission to merge into `main`.

**Final R-300 research sign-off:** focused native GitHub Actions
[#41958473142](https://github.com/joeyst8/witnora-core/actions/runs/41958473142)
completed successfully. Signed off for further independent research review
only; the draft branch remains unmerged and no main-branch/release approval
is inferred.
