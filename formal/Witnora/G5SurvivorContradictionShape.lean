import Witnora.G5GlobalSurvivorNormalForm
import Witnora.G5BackSubstitution

/-!
# Contradiction shape of the executable G5 final survivors

Combine the kernel-checked global absence theorem with an explicit
variable-coverage hypothesis for the final live rows. Every resulting
survivor is a constant Boolean equation: zero equals its RHS.
Thus a true RHS is exactly a contradiction, while a false RHS is
satisfied by every assignment.

Remaining work includes deriving coverage from the initial input and
proving complete contradiction discovery across retained pivot rows.
-/

namespace Witnora.G5SurvivorContradictionShape

open Witnora.G5Trace
open Witnora.G5Certificate
open Witnora.SparseParity
open Witnora.G5IndexedOperationEmitter
open Witnora.G5IndexedRowValueRefinement
open Witnora.G5TrackedSurvivors
open Witnora.G5GlobalSurvivorNormalForm
open Witnora.G5SourceTraceSafety

/-- Coverage by the processed variable schedule at each final live
    survivor, stated explicitly until the source support invariant
    is connected to initial-input validation. -/
def FinalCoverage (initial : List Row) (variables : List Nat)
    (state : SourceState initial) (survivors : List Nat) : Prop :=
  ∀ slot ∈ survivors, ∀ row,
    workingRow initial state slot = some row →
    ∀ v ∈ row.coefficients, v ∈ variables

/-- Under final variable coverage, a completed executable G5 schedule
    leaves every surviving row with empty coefficient support. -/
theorem final_survivor_support_empty
    (initial : List Row)
    (variables candidates : List Nat)
    (state finished : SourceState initial)
    (operations : List Witnora.G5EmittedPivotPass.Op)
    (survivors : List Nat)
    (hnd : candidates.Nodup)
    (hvalid : LiveRefsValid initial state)
    (hcoverage : FinalCoverage initial variables finished survivors)
    (h : emitScheduleTracked initial variables candidates state =
      some (operations, finished, survivors)) :
    ∀ slot ∈ survivors, ∀ row,
      workingRow initial finished slot = some row →
      row.coefficients = [] := by
  have hnormal := tracked_schedule_residual_normal_form initial
    variables candidates state finished operations survivors
    hnd hvalid h
  intro slot hs row hrow
  cases hcoeff : row.coefficients with
  | nil => rfl
  | cons head tail =>
      have hm : head ∈ row.coefficients := by
        simp [hcoeff]
      have hvar : head ∈ variables :=
        hcoverage slot hs row hrow head hm
      have habs := hnormal head hvar slot hs row hrow
      exact False.elim (habs hm)

/-- A constant survivor is satisfiable exactly when its RHS is false.
    In particular, a true RHS is a genuine contradiction for all
    Boolean assignments. -/
theorem empty_support_row_holds_iff
    (bound : Nat) (row : Row)
    (hzero : row.coefficients = []) (assignment : Nat → Bool) :
    RowHolds bound row assignment ↔ row.rhs = false := by
  simp [RowHolds, hzero, sparseParity_empty]

/-- A final survivor is individually unsatisfiable exactly when its RHS
    is true. This theorem relies only on the zero-support result above. -/
theorem survivor_unsat_iff_true_rhs
    (initial : List Row) (bound : Nat)
    (variables candidates : List Nat)
    (state finished : SourceState initial)
    (operations : List Witnora.G5EmittedPivotPass.Op)
    (survivors : List Nat) (slot : Nat) (row : Row)
    (hnd : candidates.Nodup)
    (hvalid : LiveRefsValid initial state)
    (hcoverage : FinalCoverage initial variables finished survivors)
    (h : emitScheduleTracked initial variables candidates state =
      some (operations, finished, survivors))
    (hs : slot ∈ survivors)
    (hrow : workingRow initial finished slot = some row) :
    (¬ ∃ assignment : Nat → Bool, RowHolds bound row assignment) ↔
      row.rhs = true := by
  have hzero := final_survivor_support_empty initial
    variables candidates state finished operations survivors
    hnd hvalid hcoverage h slot hs row hrow
  cases hr : row.rhs with
  | false =>
      simp [empty_support_row_holds_iff bound row hzero, hr]
  | true =>
      simp [empty_support_row_holds_iff bound row hzero, hr]

#print axioms Witnora.G5SurvivorContradictionShape.final_survivor_support_empty
#print axioms Witnora.G5SurvivorContradictionShape.empty_support_row_holds_iff
#print axioms Witnora.G5SurvivorContradictionShape.survivor_unsat_iff_true_rhs

end Witnora.G5SurvivorContradictionShape
