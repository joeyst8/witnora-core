import Witnora.G5SchedulerPivotClearance

/-!
# Executable G5 schedule with a witnessed final candidate list

The original emitter returns its source operations and final DAG state,
but not the slots still eligible after retiring selected pivot rows.
This instrumented emitter records that list while running exactly the
same pivot decisions and source operations.

The projection theorem proves that erasing the extra list recovers
the original executable scheduler, so final active-row normal-form
claims can be stated without ambiguity.
-/

namespace Witnora.G5TrackedSurvivors

open Witnora.G5Trace
open Witnora.G5IndexedOperationEmitter
open Witnora.G5IndexedPivotSelection
open Witnora.G5IndexedScheduledEmitter
open Witnora.G5EmittedPivotPass

/-- The same finite scheduled emitter, augmented only with its final
    list of surviving candidate row slots. -/
def emitScheduleTracked (initial : List Row) :
    List Nat → List Nat → SourceState initial →
      Option (List Op × SourceState initial × List Nat)
  | [], candidates, state => some ([], state, candidates)
  | v :: remaining, candidates, state =>
      match choosePivot initial v state candidates with
      | none => emitScheduleTracked initial remaining candidates state
      | some (pivotSlot, _) => do
          let targets := candidates.filter (fun slot => slot != pivotSlot)
          let (firstOps, updated) ←
            emitPass initial v pivotSlot targets state
          let (restOps, finished, survivors) ←
            emitScheduleTracked initial remaining targets updated
          return (firstOps ++ restOps, finished, survivors)

/-- Every tracked execution has exactly the same operation list and
    final proof-carrying state as the uninstrumented G5 scheduler. -/
theorem tracked_execution_matches_schedule
    (initial : List Row)
    (variables candidates : List Nat)
    (state finished : SourceState initial)
    (operations : List Op) (survivors : List Nat)
    (h : emitScheduleTracked initial variables candidates state =
      some (operations, finished, survivors)) :
    emitSchedule initial variables candidates state =
      some (operations, finished) := by
  induction variables generalizing candidates state finished operations survivors with
  | nil =>
      simp [emitScheduleTracked] at h
      rcases h with ⟨hops, hfinished, hsurvivors⟩
      subst operations
      subst finished
      simp [emitSchedule]
  | cons v rest ih =>
      cases hp : choosePivot initial v state candidates with
      | none =>
          have hrest :
              emitScheduleTracked initial rest candidates state =
                some (operations, finished, survivors) := by
            simpa [emitScheduleTracked, hp] using h
          simpa [emitSchedule, hp] using
            ih candidates state finished operations survivors hrest
      | some choice =>
          cases choice with
          | mk pivotSlot pivotRow =>
              let targets := candidates.filter (fun slot => slot != pivotSlot)
              cases he : emitPass initial v pivotSlot targets state with
              | none =>
                  simp [emitScheduleTracked, hp, targets, he] at h
              | some first =>
                  cases first with
                  | mk firstOps updated =>
                      cases hr : emitScheduleTracked initial rest targets updated with
                      | none =>
                          simp [emitScheduleTracked, hp, targets, he, hr] at h
                      | some second =>
                          cases second with
                          | mk restOps pair =>
                          cases pair with
                          | mk result survivorsRest =>
                                  simp [emitScheduleTracked, hp, targets, he, hr] at h
                                  rcases h with ⟨hops, hfinished, hsurvivors⟩
                                  subst operations
                                  subst finished
                                  subst survivors
                                  have hrest := ih targets updated result
                                restOps survivorsRest hr
                                  simpa [emitSchedule, hp, targets, he, hrest]

/-- The final tracked slots are a subset of the starting candidates:
    successful pivot retirement removes candidates but never adds them. -/
theorem tracked_survivors_subset
    (initial : List Row)
    (variables candidates : List Nat)
    (state finished : SourceState initial)
    (operations : List Op) (survivors : List Nat)
    (h : emitScheduleTracked initial variables candidates state =
      some (operations, finished, survivors)) :
    ∀ slot ∈ survivors, slot ∈ candidates := by
  induction variables generalizing candidates state finished operations survivors with
  | nil =>
      simp [emitScheduleTracked] at h
      rcases h with ⟨hops, hfinished, hsurvivors⟩
      subst survivors
      intro slot hm
      exact hm
  | cons v rest ih =>
      cases hp : choosePivot initial v state candidates with
      | none =>
          have hrest :
              emitScheduleTracked initial rest candidates state =
                some (operations, finished, survivors) := by
            simpa [emitScheduleTracked, hp] using h
          exact ih candidates state finished operations survivors hrest
      | some choice =>
          cases choice with
          | mk pivotSlot pivotRow =>
              let targets := candidates.filter (fun slot => slot != pivotSlot)
              cases he : emitPass initial v pivotSlot targets state with
              | none =>
                  simp [emitScheduleTracked, hp, targets, he] at h
              | some first =>
                  cases first with
                  | mk firstOps updated =>
                      cases hr : emitScheduleTracked initial rest targets updated with
                      | none =>
                          simp [emitScheduleTracked, hp, targets, he, hr] at h
                      | some second =>
                          cases second with
                          | mk restOps pair =>
                          cases pair with
                          | mk result survivorsRest =>
                                  simp [emitScheduleTracked, hp, targets, he, hr] at h
                                  rcases h with ⟨hops, hfinished, hsurvivors⟩
                                  subst survivors
                                  intro slot hm
                                  exact (List.mem_filter.mp
                                (ih targets updated result restOps
                                  survivorsRest hr slot hm)).1

#print axioms Witnora.G5TrackedSurvivors.tracked_execution_matches_schedule
#print axioms Witnora.G5TrackedSurvivors.tracked_survivors_subset

end Witnora.G5TrackedSurvivors
