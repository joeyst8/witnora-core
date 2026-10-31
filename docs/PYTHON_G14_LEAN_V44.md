# Python-generated G14 residuals verified with Lean G5 (v44)

Draft PR #45. Successful CI: https://github.com/joeyst8/witnora-core/actions/runs/41240653841

## Actual source path

The Python emitter constructs a canonical `CNFFormula` for the small UNSAT example `(x1 ∨ x2) ∧ (¬x1 ∨ x2) ∧ (¬x2)`. It invokes Witnora's actual `_component_dicts`, `_all_assignments`, and `_condition_by_separator` routines, checks Python's component consistency, and extracts the contradictory residual unit clauses for both separator branches. It also calls the actual `solve_xor_system_gaussian` on derived unit equations and asserts Python reports UNSAT.

The script emits the Python formula's actual canonical DIMACS ASCII byte list, integer token stream, raw signed clauses, branch-specific component CNFs, selected residuals, initial G5 rows and DAG steps into a generated Lean file.

Lean independently checks:
- Whole-document byte parse and exact token/clauses;
- Both separator branches and exact conditioned residual partitions;
- Selected residual component membership;
- Closed G5 clause coverage, sparse support and contradiction steps;
- Source-level UNSAT via `G14ConcreteBridge.checked_ascii_dimacs_g14_unsat`.

The source theorem `GeneratedPythonG14.python_g14_g5_dimacs_unsat` depends only on `[propext, Classical.choice, Quot.sound]`, with no `sorry` or `Lean.ofReduceBool`.

Measured generated Lean verification: **0.45 seconds**, peak resident memory **311,612 KiB**.

## Important boundary

This exercises the genuine Python *conditioning and component* functions, but the G5 step list is a deterministic candidate from the two opposite unit clauses, not a complete export of a native production G5 indexed-operation trace. Lean checks that candidate independently. The instance is tiny and hand-selected; it is not the TC-063 source/certificate collection, and no universal Python refinement or transport theorem is claimed.

Next: generate candidate certificates from real native G5 traces for branch residuals, test multiple structured G14 instances and adversarial changes, and finally target the original TC-063 artifact identity and end-to-end premises.
