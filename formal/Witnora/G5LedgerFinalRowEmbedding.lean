import Witnora.G5RetiredSlotStability
import Witnora.G5RetiredPivotLedger

/-!
# Every retired indexed G5 pivot is present in the final row table

The pivot ledger saves row values at selection time. A selected pivot
slot is never a target of its own pass and is excluded from every later
candidate set. Therefore every saved pivot row is exactly dereferenceable
at some original candidate slot in the final proof-carrying source state.

This is a one-directional ledger-to-final-table correspondence. The
converse, that all original slots are partitioned into retired pivots
and final survivors, remains to be proved.
-/

namespace Witnora.G5LedgerFinalRowEmbedding

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

/-- Every saved pivot row has an exact final working-row witness in
    a slot drawn from the original schedule candidates. -/
theorem ledger_entries_are_final_working_rows
    (initial : List Row)
    (variables candidates : List Nat)
    (state : SourceState initial) (outcome : PivotOutcome initial)
    (hvalid : LiveRefsValid initial state)
    (h : emitScheduleWithPivots initial variables candidates state =
      some outcome) :
    ∀ entry ∈ outcome.pivots, ∃ slot ∈ candidates,
      workingRow initial outcome.finalState slot = some entry.2 := by
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
          exact ih candidates state outcome hvalid hrest
      | some choice =>
          cases choice with
          | mk pivotSlot pivotRow =>
              let targets := candidates.filter (fun slot => slot != pivotSlot)
              have hpivotMem : pivotSlot ∈ candidates :=
                (choosePivot_sound initial v state candidates
                  pivotSlot pivotRow hp).1
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
                            simp [emitSchedule, hp, targets, he,
                              htailSchedule]
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
                          intro entry hm
                          rcases List.mem_cons.mp hm with heq | hrestMem
                          · subst entry
                            exact ⟨pivotSlot, hpivotMem, hchosen⟩
                          · obtain ⟨slot, hslot, hrow⟩ :=
                              htail entry hrestMem
                            exact ⟨slot, (List.mem_filter.mp hslot).1, hrow⟩

#print axioms Witnora.G5LedgerFinalRowEmbedding.ledger_entries_are_final_working_rows

end Witnora.G5LedgerFinalRowEmbedding
