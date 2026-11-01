import Witnora.G5RetiredPivotTriangular
import Witnora.G5InitialSupportCoverage

/-!
# Exact model criterion for executable G5 pivot-ledger plus survivors

The retained pivot equations are triangular and hence simultaneously
satisfiable by certified back-substitution. The final surviving rows
have zero variable support under original-input schedule coverage.
Consequently the combined retained-pivot-plus-survivor system has a
Boolean model exactly when no surviving row has true RHS.

This theorem is a genuine finite-system model criterion, but complete
UNSAT detection for the original input still requires proving that
the pivot ledger and survivors faithfully represent all final working
rows, then transporting equivalence to the original row table.
-/

namespace Witnora.G5LedgerSurvivorModel

open Witnora.G5Trace
open Witnora.G5Certificate
open Witnora.G5IndexedOperationEmitter
open Witnora.G5IndexedRowValueRefinement
open Witnora.G5RetiredPivotLedger
open Witnora.G5RetiredPivotTriangular
open Witnora.G5InitialSupportCoverage
open Witnora.G5SurvivorContradictionShape
open Witnora.G5TrackedSurvivors
open Witnora.G5SourceTraceSafety

/-- There is no contradictory true-RHS row among the final active
    source row views returned by the indexed scheduler. -/
def NoSurvivorContradiction (initial : List Row)
    (outcome : PivotOutcome initial) : Prop :=
  ∀ slot ∈ outcome.survivors, ∀ row,
    workingRow initial outcome.finalState slot = some row →
      row.rhs = false

/-- All retained pivots and every readable surviving working row
    simultaneously hold under one Boolean assignment. -/
def CombinedModel (initial : List Row) (bound : Nat)
    (outcome : PivotOutcome initial) (assignment : Nat → Bool) : Prop :=
  (∀ entry ∈ outcome.pivots,
    RowHolds bound entry.2 assignment) ∧
  (∀ slot ∈ outcome.survivors, ∀ row,
    workingRow initial outcome.finalState slot = some row →
      RowHolds bound row assignment)

/-- Exact existence criterion for the executable ledger-plus-survivor
    equation system: it has a Boolean model iff the residual survivors
    contain no contradiction. Both directions are proved for arbitrary
    finite valid schedules whose variables cover the original input. -/
theorem no_survivor_contradiction_iff_combined_model
    (initial : List Row) (bound : Nat)
    (variables candidates : List Nat)
    (state : SourceState initial) (outcome : PivotOutcome initial)
    (hinput : Covered variables initial)
    (hnd : candidates.Nodup)
    (hvalid : LiveRefsValid initial state)
    (hvars : ∀ v ∈ variables, v < bound)
    (h : emitScheduleWithPivots initial variables candidates state =
      some outcome) :
    NoSurvivorContradiction initial outcome ↔
      ∃ assignment : Nat → Bool,
        CombinedModel initial bound outcome assignment := by
  have htracked := pivot_ledger_refines_tracked initial
    variables candidates state outcome h
  have hzero := final_survivor_support_empty_from_initial
    initial variables candidates state outcome.finalState
    outcome.operations outcome.survivors hinput hnd hvalid htracked
  constructor
  · intro hno
    obtain ⟨assignment, hpivots⟩ :=
      executable_pivot_ledger_has_model initial bound variables
        candidates state outcome hnd hvalid hvars h
    refine ⟨assignment, hpivots, ?_⟩
    intro slot hs row hrow
    have hcoeff := hzero slot hs row hrow
    have hrhs := hno slot hs row hrow
    exact (empty_support_row_holds_iff bound row hcoeff assignment).mpr hrhs
  · rintro ⟨assignment, ⟨_, hsurvivors⟩⟩
    intro slot hs row hrow
    have hcoeff := hzero slot hs row hrow
    have hholds := hsurvivors slot hs row hrow
    exact (empty_support_row_holds_iff bound row hcoeff assignment).mp hholds

/-- Its useful contrapositive: if no Boolean assignment satisfies
    both the real retired pivots and final live survivors, then a true
    RHS must occur in a surviving row. -/
theorem combined_unsat_forces_survivor_contradiction
    (initial : List Row) (bound : Nat)
    (variables candidates : List Nat)
    (state : SourceState initial) (outcome : PivotOutcome initial)
    (hinput : Covered variables initial)
    (hnd : candidates.Nodup)
    (hvalid : LiveRefsValid initial state)
    (hvars : ∀ v ∈ variables, v < bound)
    (h : emitScheduleWithPivots initial variables candidates state =
      some outcome)
    (hunsat : ¬ ∃ assignment : Nat → Bool,
      CombinedModel initial bound outcome assignment) :
    ∃ slot ∈ outcome.survivors, ∃ row,
      workingRow initial outcome.finalState slot = some row ∧
      row.rhs = true := by
  by_contra hbad
  have hno : NoSurvivorContradiction initial outcome := by
    intro slot hs row hrow
    cases hr : row.rhs with
    | false => rfl
    | true =>
        exact False.elim (hbad ⟨slot, hs, row, hrow, hr⟩)
  have hmodel :=
    (no_survivor_contradiction_iff_combined_model initial
      bound variables candidates state outcome hinput hnd
      hvalid hvars h).mp hno
  exact hunsat hmodel

#print axioms Witnora.G5LedgerSurvivorModel.no_survivor_contradiction_iff_combined_model
#print axioms Witnora.G5LedgerSurvivorModel.combined_unsat_forces_survivor_contradiction

end Witnora.G5LedgerSurvivorModel
