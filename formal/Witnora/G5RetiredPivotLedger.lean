import Witnora.G5InitialSupportCoverage

/-!
# A verified ledger of retired G5 pivot equations

The indexed scheduler discards selected pivot slots from its active
candidate set. This instrumented form also records each selected
variable and its exact selected working-row value. Erasing the pivot
ledger recovers the previously verified tracked scheduler with exactly
the same emitted operations, final DAG state, and surviving slots.

This is the foundation for proving triangular retained pivots and
back-substitution completeness rather than assuming them.
-/

namespace Witnora.G5RetiredPivotLedger

open Witnora.G5Trace
open Witnora.G5IndexedOperationEmitter
open Witnora.G5IndexedRowValueRefinement
open Witnora.G5IndexedPivotSelection
open Witnora.G5IndexedScheduledEmitter
open Witnora.G5TrackedSurvivors
open Witnora.G5EmittedPivotPass

structure PivotOutcome (initial : List Row) where
  operations : List Op
  finalState : SourceState initial
  survivors : List Nat
  pivots : List (Nat × Row)

/-- Record selected pivot rows without changing a single source XOR,
    pivot choice, or candidate retirement from the existing scheduler. -/
def emitScheduleWithPivots (initial : List Row) :
    List Nat → List Nat → SourceState initial →
      Option (PivotOutcome initial)
  | [], candidates, state =>
      some ⟨[], state, candidates, []⟩
  | v :: remaining, candidates, state =>
      match choosePivot initial v state candidates with
      | none => emitScheduleWithPivots initial remaining candidates state
      | some (pivotSlot, pivotRow) => do
          let targets := candidates.filter (fun slot => slot != pivotSlot)
          let (firstOps, updated) ←
            emitPass initial v pivotSlot targets state
          let remainder ←
            emitScheduleWithPivots initial remaining targets updated
          return {
            operations := firstOps ++ remainder.operations
            finalState := remainder.finalState
            survivors := remainder.survivors
            pivots := (v, pivotRow) :: remainder.pivots
          }

/-- Erasing the added pivot ledger produces exactly the old tracked
    scheduler's operation trace, final source state, and active slots. -/
theorem pivot_ledger_refines_tracked
    (initial : List Row)
    (variables candidates : List Nat)
    (state : SourceState initial) (outcome : PivotOutcome initial)
    (h : emitScheduleWithPivots initial variables candidates state =
      some outcome) :
    emitScheduleTracked initial variables candidates state =
      some (outcome.operations, outcome.finalState, outcome.survivors) := by
  induction variables generalizing candidates state outcome with
  | nil =>
      simp [emitScheduleWithPivots] at h
      subst outcome
      rfl
  | cons v rest ih =>
      cases hp : choosePivot initial v state candidates with
      | none =>
          have hrest : emitScheduleWithPivots initial rest candidates state =
              some outcome := by
            simpa [emitScheduleWithPivots, hp] using h
          simpa [emitScheduleTracked, hp] using
            ih candidates state outcome hrest
      | some choice =>
          cases choice with
          | mk pivotSlot pivotRow =>
              let targets := candidates.filter (fun slot => slot != pivotSlot)
              cases he : emitPass initial v pivotSlot targets state with
              | none =>
                  simp [emitScheduleWithPivots, hp, targets, he] at h
              | some first =>
                  cases first with
                  | mk firstOps updated =>
                      cases hr : emitScheduleWithPivots initial rest targets updated with
                      | none =>
                          simp [emitScheduleWithPivots, hp, targets, he, hr] at h
                      | some remainder =>
                          simp [emitScheduleWithPivots, hp, targets, he, hr] at h
                          subst outcome
                          have htail := ih targets updated remainder hr
                          simpa [emitScheduleTracked, hp, targets, he, htail]

/-- Each recorded pivot tag is one of the scheduled variables;
    the ledger cannot invent a pivot for an unscheduled variable. -/
theorem ledger_tags_belong_to_schedule
    (initial : List Row)
    (variables candidates : List Nat)
    (state : SourceState initial) (outcome : PivotOutcome initial)
    (h : emitScheduleWithPivots initial variables candidates state =
      some outcome) :
    ∀ entry ∈ outcome.pivots, entry.1 ∈ variables := by
  induction variables generalizing candidates state outcome with
  | nil =>
      simp [emitScheduleWithPivots] at h
      subst outcome
      intro entry hm
      simp at hm
  | cons v rest ih =>
      cases hp : choosePivot initial v state candidates with
      | none =>
          have hrest : emitScheduleWithPivots initial rest candidates state =
              some outcome := by
            simpa [emitScheduleWithPivots, hp] using h
          intro entry hm
          exact List.mem_cons_of_mem v
            (ih candidates state outcome hrest entry hm)
      | some choice =>
          cases choice with
          | mk pivotSlot pivotRow =>
              let targets := candidates.filter (fun slot => slot != pivotSlot)
              cases he : emitPass initial v pivotSlot targets state with
              | none =>
                  simp [emitScheduleWithPivots, hp, targets, he] at h
              | some first =>
                  cases first with
                  | mk firstOps updated =>
                      cases hr : emitScheduleWithPivots initial rest targets updated with
                      | none =>
                          simp [emitScheduleWithPivots, hp, targets, he, hr] at h
                      | some remainder =>
                          simp [emitScheduleWithPivots, hp, targets, he, hr] at h
                          subst outcome
                          intro entry hm
                          rcases List.mem_cons.mp hm with heq | htail
                          · subst entry
                            simp
                          · exact List.mem_cons_of_mem v
                              (ih targets updated remainder hr entry htail)

#print axioms Witnora.G5RetiredPivotLedger.pivot_ledger_refines_tracked
#print axioms Witnora.G5RetiredPivotLedger.ledger_tags_belong_to_schedule

end Witnora.G5RetiredPivotLedger
