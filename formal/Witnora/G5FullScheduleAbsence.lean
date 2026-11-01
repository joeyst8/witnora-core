import Witnora.G5ScheduledAbsenceInvariant

/-!
# Permanent absence through the full indexed G5 variable schedule

A successfully emitted scheduled elimination cannot reintroduce a
variable already absent from the candidate set at schedule entry.
The proof handles selected and skipped pivots, retiring pivot slots,
and every executed finite source operation.
-/

namespace Witnora.G5FullScheduleAbsence

open Witnora.G5Trace
open Witnora.G5IndexedOperationEmitter
open Witnora.G5IndexedRowValueRefinement
open Witnora.G5IndexedPivotSelection
open Witnora.G5IndexedScheduledEmitter
open Witnora.G5ScheduledAbsenceInvariant
open Witnora.G5ExecutablePassClearance
open Witnora.G5EmittedPivotPass
open Witnora.G5SourceTraceSafety

/-- Future candidate slots stay inside their original guardedSlots set.
    Consequently all future pivot sources and XOR targets also exclude
    the guardedSlots variable, and no operation can reintroduce it. -/
theorem emitSchedule_preserves_absence_superset
    (initial : List Row) (v : Nat)
    (variables candidates guardedSlots : List Nat)
    (state result : SourceState initial) (operations : List Op)
    (hsubset : ∀ slot ∈ candidates, slot ∈ guardedSlots)
    (hvalid : LiveRefsValid initial state)
    (habs : AbsentOn initial v state guardedSlots)
    (h : emitSchedule initial variables candidates state =
      some (operations, result)) :
    AbsentOn initial v result guardedSlots := by
  induction variables generalizing candidates state result operations with
  | nil =>
      simp [emitSchedule] at h
      rcases h with ⟨hops, hresult⟩
      subst result
      exact habs
  | cons w rest ih =>
      cases hp : choosePivot initial w state candidates with
      | none =>
          have hrest : emitSchedule initial rest candidates state =
              some (operations, result) := by
            simpa [emitSchedule, hp] using h
          exact ih candidates state result operations
            hsubset hvalid habs hrest
      | some choice =>
          cases choice with
          | mk pivotSlot pivotRow =>
              let targets := candidates.filter (fun slot => slot != pivotSlot)
              have hpivotMem : pivotSlot ∈ guardedSlots :=
                hsubset pivotSlot
                  (choosePivot_sound initial w state candidates
                    pivotSlot pivotRow hp).1
              have hpivotRow : workingRow initial state pivotSlot =
                  some pivotRow :=
                (choosePivot_sound initial w state candidates
                  pivotSlot pivotRow hp).2.1
              have htargets : ∀ slot ∈ targets, slot ∈ guardedSlots := by
                intro slot hm
                exact hsubset slot (List.mem_filter.mp hm).1
              have hpivotNot : pivotSlot ∉ targets := by
                simp [targets]
              cases he : emitPass initial w pivotSlot targets state with
              | none =>
                  simp [emitSchedule, hp, targets, he] at h
              | some first =>
                  cases first with
                  | mk firstOps updated =>
                      cases hr : emitSchedule initial rest targets updated with
                      | none =>
                          simp [emitSchedule, hp, targets, he, hr] at h
                      | some second =>
                          cases second with
                          | mk restOps finished =>
                              simp [emitSchedule, hp, targets, he, hr] at h
                              rcases h with ⟨hops, hresult⟩
                              subst result
                              have habsUpdated :=
                                emitPass_preserves_absent_candidates
                                  initial w v pivotSlot targets guardedSlots
                                  state updated firstOps pivotRow
                                  hpivotMem htargets hpivotNot hpivotRow
                                  hvalid habs he
                              have hvalidUpdated :
                                  LiveRefsValid initial updated := by
                                exact foldlM_preserves_valid initial firstOps
                                  state updated hvalid
                                  (by simpa [executeFrom] using
                                    emitPass_replays initial w pivotSlot
                                      targets state updated firstOps he)
                              exact ih targets updated finished restOps
                                htargets hvalidUpdated habsUpdated hr

/-- Entire executable schedule: a variable missing from all input
    candidate rows remains missing from those rows at termination,
    even when later selected pivots are retired from consideration. -/
theorem emitSchedule_preserves_absent_candidates
    (initial : List Row) (v : Nat)
    (variables candidates : List Nat)
    (state result : SourceState initial) (operations : List Op)
    (hvalid : LiveRefsValid initial state)
    (habs : AbsentOn initial v state candidates)
    (h : emitSchedule initial variables candidates state =
      some (operations, result)) :
    AbsentOn initial v result candidates :=
  emitSchedule_preserves_absence_superset initial v
    variables candidates candidates state result operations
    (fun _ hm => hm) hvalid habs h

#print axioms Witnora.G5FullScheduleAbsence.emitSchedule_preserves_absence_superset
#print axioms Witnora.G5FullScheduleAbsence.emitSchedule_preserves_absent_candidates

end Witnora.G5FullScheduleAbsence
