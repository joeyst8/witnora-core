import Witnora.G5TrackedSurvivors

/-!
# Global final-survivor normal form for the executable G5 scheduler

Once all scheduled variables have been processed, every final active
candidate row excludes every processed variable. The proof composes
the actual scheduler's selected-pivot and no-pivot branches, permanent
clearance, and the exact tracked-scheduler correspondence.
-/

namespace Witnora.G5GlobalSurvivorNormalForm

open Witnora.G5Trace
open Witnora.G5IndexedOperationEmitter
open Witnora.G5IndexedPivotSelection
open Witnora.G5IndexedScheduledEmitter
open Witnora.G5ScheduledAbsenceInvariant
open Witnora.G5FullScheduleAbsence
open Witnora.G5SelectedPivotPersistence
open Witnora.G5SchedulerPivotClearance
open Witnora.G5TrackedSurvivors
open Witnora.G5ExecutablePassClearance
open Witnora.G5EmittedPivotPass
open Witnora.G5SourceTraceSafety
open Witnora.G5IndexedRowValueRefinement

/-- Each processed variable is absent from all final active rows. -/
def ResidualNormalForm (initial : List Row) (variables : List Nat)
    (state : SourceState initial) (survivors : List Nat) : Prop :=
  ∀ v ∈ variables, AbsentOn initial v state survivors

private theorem nodup_filter_slots (slots : List Nat)
    (pred : Nat → Bool) (h : slots.Nodup) :
    (slots.filter pred).Nodup := by
  induction slots with
  | nil => simp
  | cons slot rest ih =>
      have hnot : slot ∉ rest := (List.nodup_cons.mp h).1
      have hrest : rest.Nodup := (List.nodup_cons.mp h).2
      simp only [List.filter_cons]
      split
      · apply List.nodup_cons.mpr
        constructor
        · intro hm
          exact hnot (List.mem_filter.mp hm).1
        · exact ih hrest
      · exact ih hrest

/-- Kernel-checked global normal form: every successfully scheduled
    variable disappears from every final surviving row, for arbitrary
    finite variable schedules and initially distinct candidate slots. -/
theorem tracked_schedule_residual_normal_form
    (initial : List Row)
    (variables candidates : List Nat)
    (state finished : SourceState initial)
    (operations : List Op) (survivors : List Nat)
    (hnd : candidates.Nodup)
    (hvalid : LiveRefsValid initial state)
    (h : emitScheduleTracked initial variables candidates state =
      some (operations, finished, survivors)) :
    ResidualNormalForm initial variables finished survivors := by
  induction variables generalizing candidates state finished operations survivors with
  | nil =>
      intro v hm
      simp at hm
  | cons w rest ih =>
      have hmatch := tracked_execution_matches_schedule initial
        (w :: rest) candidates state finished operations survivors h
      cases hp : choosePivot initial w state candidates with
      | none =>
          have hrest :
              emitScheduleTracked initial rest candidates state =
                some (operations, finished, survivors) := by
            simpa [emitScheduleTracked, hp] using h
          have hnormal := ih candidates state finished operations
            survivors hnd hvalid hrest
          have hhead := schedule_skipped_head_stays_absent initial w
            rest candidates state finished operations hvalid hp hmatch
          have hsubset := tracked_survivors_subset initial rest
            candidates state finished operations survivors hrest
          intro v hm
          rcases List.mem_cons.mp hm with heq | htail
          · subst v
            intro slot hs row hrow
            exact hhead slot (hsubset slot hs) row hrow
          · exact hnormal v htail
      | some choice =>
          cases choice with
          | mk pivotSlot pivotRow =>
              let targets := candidates.filter (fun slot => slot != pivotSlot)
              have hndTargets : targets.Nodup :=
                nodup_filter_slots candidates
                  (fun slot => slot != pivotSlot) hnd
              cases he : emitPass initial w pivotSlot targets state with
              | none =>
                  simp [emitScheduleTracked, hp, targets, he] at h
              | some first =>
                  cases first with
                  | mk firstOps updated =>
                      cases hr : emitScheduleTracked initial rest targets updated with
                      | none =>
                          simp [emitScheduleTracked, hp, targets, he, hr] at h
                      | some second =>
                          rcases second with ⟨restOps, result, survivorsRest⟩
                          simp [emitScheduleTracked, hp, targets, he, hr] at h
                          rcases h with ⟨hops, hfinished, hsurvivors⟩
                          subst finished
                          subst survivors
                          have hreplay := emitPass_replays initial w
                            pivotSlot targets state updated firstOps he
                          have hvalidUpdated : LiveRefsValid initial updated :=
                            foldlM_preserves_valid initial firstOps state
                              updated hvalid
                              (by simpa [executeFrom] using hreplay)
                          have hnormal := ih targets updated result
                            restOps survivorsRest hndTargets hvalidUpdated hr
                          have hhead := schedule_selected_head_stays_clear
                            initial w pivotSlot rest candidates state result
                            (firstOps ++ restOps) pivotRow hnd hvalid hp
                            (by simpa [emitSchedule, hp, targets, he,
                              (tracked_execution_matches_schedule initial
                                rest targets updated result restOps
                                survivorsRest hr)] using hmatch)
                          have hsubset := tracked_survivors_subset initial
                            rest targets updated result restOps
                            survivorsRest hr
                          intro v hm
                          rcases List.mem_cons.mp hm with heq | htail
                          · subst v
                            intro slot hs row hrow
                            exact hhead slot (hsubset slot hs) row hrow
                          · exact hnormal v htail

#print axioms Witnora.G5GlobalSurvivorNormalForm.tracked_schedule_residual_normal_form

end Witnora.G5GlobalSurvivorNormalForm
