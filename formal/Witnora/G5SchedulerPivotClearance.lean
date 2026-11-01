import Witnora.G5SelectedPivotPersistence

/-!
# Pivot-choice consequences of the actual indexed G5 scheduler

The public schedule entry point itself, rather than an externally
chosen pivot, guarantees that a selected variable is permanently
cleared from the survivors of its first pass. Skipped variables were
already absent and remain absent as the schedule continues.
-/

namespace Witnora.G5SchedulerPivotClearance

open Witnora.G5Trace
open Witnora.G5IndexedOperationEmitter
open Witnora.G5IndexedRowValueRefinement
open Witnora.G5IndexedPivotSelection
open Witnora.G5IndexedScheduledEmitter
open Witnora.G5ScheduledAbsenceInvariant
open Witnora.G5FullScheduleAbsence
open Witnora.G5SelectedPivotPersistence
open Witnora.G5ExecutablePassClearance
open Witnora.G5EmittedPivotPass
open Witnora.G5SourceTraceSafety

/-- Filtering a list of distinct candidate slots cannot create duplicates. -/
private theorem nodup_filter_candidates (slots : List Nat)
    (pred : Nat → Bool) (h : slots.Nodup) :
    (slots.filter pred).Nodup := by
  induction slots with
  | nil =>
      simp
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

/-- If pivot selection finds v at the first scheduled step, then
    the full actual scheduler eliminates v from every non-pivot
    candidate, and all later scheduled steps retain that clearance. -/
theorem schedule_selected_head_stays_clear
    (initial : List Row) (v pivotSlot : Nat)
    (remaining candidates : List Nat)
    (state finished : SourceState initial) (operations : List Op)
    (pivotRow : Row)
    (hnd : candidates.Nodup)
    (hvalid : LiveRefsValid initial state)
    (hp : choosePivot initial v state candidates =
      some (pivotSlot, pivotRow))
    (h : emitSchedule initial (v :: remaining) candidates state =
      some (operations, finished)) :
    AbsentOn initial v finished
      (candidates.filter (fun slot => slot != pivotSlot)) := by
  let targets := candidates.filter (fun slot => slot != pivotSlot)
  have hndTargets : targets.Nodup := by
    exact nodup_filter_candidates candidates
      (fun slot => slot != pivotSlot) hnd
  have hpivotNot : pivotSlot ∉ targets := by
    simp [targets]
  obtain ⟨_, hpivot, hv⟩ :=
    choosePivot_sound initial v state candidates pivotSlot pivotRow hp
  cases he : emitPass initial v pivotSlot targets state with
  | none =>
      simp [emitSchedule, hp, targets, he] at h
  | some first =>
      cases first with
      | mk firstOps updated =>
          cases hr : emitSchedule initial remaining targets updated with
          | none =>
              simp [emitSchedule, hp, targets, he, hr] at h
          | some second =>
              cases second with
              | mk restOps result =>
                  simp [emitSchedule, hp, targets, he, hr] at h
                  rcases h with ⟨hops, hresult⟩
                  subst finished
                  exact selected_pivot_stays_clear_through_remainder
                    initial v pivotSlot remaining targets state
                    updated result firstOps restOps pivotRow
                    hndTargets hpivotNot hpivot hv hvalid he hr

/-- A skipped variable really was absent from all candidate rows;
    subsequent scheduled operations cannot introduce it. -/
theorem schedule_skipped_head_stays_absent
    (initial : List Row) (v : Nat)
    (remaining candidates : List Nat)
    (state finished : SourceState initial) (operations : List Op)
    (hvalid : LiveRefsValid initial state)
    (hp : choosePivot initial v state candidates = none)
    (h : emitSchedule initial (v :: remaining) candidates state =
      some (operations, finished)) :
    AbsentOn initial v finished candidates := by
  have habs : AbsentOn initial v state candidates :=
    choosePivot_none_absent initial v state candidates hp
  have hrest : emitSchedule initial remaining candidates state =
      some (operations, finished) := by
    simpa [emitSchedule, hp] using h
  exact emitSchedule_preserves_absent_candidates initial v
    remaining candidates state finished operations hvalid habs hrest

#print axioms Witnora.G5SchedulerPivotClearance.schedule_selected_head_stays_clear
#print axioms Witnora.G5SchedulerPivotClearance.schedule_skipped_head_stays_absent

end Witnora.G5SchedulerPivotClearance
