import Witnora.G5LedgerFinalRowEmbedding

/-!
# Every starting G5 candidate slot is accounted for at termination

The forward ledger embedding proves retired pivot rows appear unchanged
in the final indexed working state. This complementary theorem shows
that no starting candidate position disappears: it is either one of
the returned final survivors, or its exact final row value equals a
recorded retired pivot equation.

Together these form the coverage foundation for exact model equivalence
between the ledger-plus-survivors and all candidate working rows.
-/

namespace Witnora.G5CandidateSlotPartition

open Witnora.G5Trace
open Witnora.G5IndexedOperationEmitter
open Witnora.G5IndexedRowValueRefinement
open Witnora.G5IndexedPivotSelection
open Witnora.G5IndexedScheduledEmitter
open Witnora.G5TrackedSurvivors
open Witnora.G5RetiredPivotLedger
open Witnora.G5RetiredSlotStability
open Witnora.G5EmittedPivotPass
open Witnora.G5SourceTraceSafety

/-- Every starting candidate is either a final survivor or its
    unchanged final row value is represented in the retired ledger.
    The theorem is over actual executed indexed row views. -/
theorem every_candidate_is_retired_or_survives
    (initial : List Row)
    (variables candidates : List Nat)
    (state : SourceState initial) (outcome : PivotOutcome initial)
    (hvalid : LiveRefsValid initial state)
    (h : emitScheduleWithPivots initial variables candidates state =
      some outcome) :
    ∀ slot ∈ candidates,
      (∃ entry ∈ outcome.pivots,
        workingRow initial outcome.finalState slot = some entry.2) ∨
      slot ∈ outcome.survivors := by
  induction variables generalizing candidates state outcome with
  | nil =>
      simp [emitScheduleWithPivots] at h
      subst outcome
      intro slot hm
      exact Or.inr hm
  | cons v rest ih =>
      cases hp : choosePivot initial v state candidates with
      | none =>
          have hrest : emitScheduleWithPivots initial rest candidates state =
              some outcome := by
            simpa [emitScheduleWithPivots, hp] using h
          exact ih candidates state outcome hvalid hrest
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
                          have htailTracked := pivot_ledger_refines_tracked
                            initial rest targets updated remainder hr
                          have htailSchedule :=
                            tracked_execution_matches_schedule initial
                              rest targets updated remainder.finalState
                              remainder.operations remainder.survivors
                              htailTracked
                          have hfull : emitSchedule initial (v :: rest)
                              candidates state =
                              some (firstOps ++ remainder.operations,
                                remainder.finalState) := by
                            simp [emitSchedule, hp, targets, he, htailSchedule]
                          have hchosen := selected_pivot_slot_is_finally_stable
                            initial v pivotSlot rest candidates state
                            remainder.finalState
                            (firstOps ++ remainder.operations) pivotRow
                            hvalid hp hfull
                          have hreplay := emitPass_replays initial v
                            pivotSlot targets state updated firstOps he
                          have hvalidUpdated : LiveRefsValid initial updated :=
                            foldlM_preserves_valid initial firstOps state
                              updated hvalid
                              (by simpa [executeFrom] using hreplay)
                          have htail := ih targets updated remainder
                            hvalidUpdated hr
                          intro slot hm
                          by_cases hslot : slot = pivotSlot
                          · subst slot
                            exact Or.inl ⟨(v, pivotRow),
                              by simp, hchosen⟩
                          · have htarget : slot ∈ targets := by
                              apply List.mem_filter.mpr
                              exact ⟨hm, by simp [hslot]⟩
                            rcases htail slot htarget with hretired | hsurvivor
                            · obtain ⟨entry, hentry, hrow⟩ := hretired
                              exact Or.inl ⟨entry, by simp [hentry], hrow⟩
                            · exact Or.inr hsurvivor

#print axioms Witnora.G5CandidateSlotPartition.every_candidate_is_retired_or_survives

end Witnora.G5CandidateSlotPartition
