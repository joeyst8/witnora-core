import Witnora.G5LedgerSurvivorModel
import Witnora.G5ExecutablePassClearance

/-!
# Indexed G5 retired slot values never change again

The source-indexed scheduler emits updates only to its current active
candidate rows, and removes a selected pivot slot before continuing.
Consequently a slot outside the current candidates is permanently
unchanged by the rest of the finite schedule. A selected pivot row is
also unchanged by its own elimination pass.

This is a source-value bridge needed to identify the retired pivot
ledger with the actual final working row table.
-/

namespace Witnora.G5RetiredSlotStability

open Witnora.G5Trace
open Witnora.G5IndexedOperationEmitter
open Witnora.G5IndexedRowValueRefinement
open Witnora.G5IndexedPivotSelection
open Witnora.G5IndexedScheduledEmitter
open Witnora.G5EmittedPivotPass
open Witnora.G5ExecutablePassClearance
open Witnora.G5SourceTraceSafety

/-- A slot not currently eligible for pivots or target updates stays
    unchanged through the entire remaining executable schedule. -/
theorem schedule_preserves_outside_candidate_slots
    (initial : List Row)
    (variables candidates : List Nat) (otherSlot : Nat)
    (state finished : SourceState initial) (operations : List Op)
    (houtside : otherSlot ∉ candidates)
    (hvalid : LiveRefsValid initial state)
    (h : emitSchedule initial variables candidates state =
      some (operations, finished)) :
    workingRow initial finished otherSlot =
      workingRow initial state otherSlot := by
  induction variables generalizing candidates state finished operations with
  | nil =>
      simp [emitSchedule] at h
      rcases h with ⟨hops, hfinished⟩
      subst finished
      rfl
  | cons v rest ih =>
      cases hp : choosePivot initial v state candidates with
      | none =>
          have hrest : emitSchedule initial rest candidates state =
              some (operations, finished) := by
            simpa [emitSchedule, hp] using h
          exact ih candidates state finished operations
            houtside hvalid hrest
      | some choice =>
          cases choice with
          | mk pivotSlot pivotRow =>
              let targets := candidates.filter (fun slot => slot != pivotSlot)
              have hpivotNot : pivotSlot ∉ targets := by
                simp [targets]
              have hotherNot : otherSlot ∉ targets := by
                intro hm
                exact houtside (List.mem_filter.mp hm).1
              have hpivot := (choosePivot_sound initial v state
                candidates pivotSlot pivotRow hp).2.1
              cases he : emitPass initial v pivotSlot targets state with
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
                          | mk restOps result =>
                              simp [emitSchedule, hp, targets, he, hr] at h
                              rcases h with ⟨hops, hfinished⟩
                              subst finished
                              have hfirst := emitPass_preserves_outside
                                initial v pivotSlot otherSlot targets state
                                updated firstOps pivotRow hpivotNot hotherNot
                                hpivot hvalid he
                              have hreplay := emitPass_replays initial v
                                pivotSlot targets state updated firstOps he
                              have hvalidUpdated : LiveRefsValid initial updated :=
                                foldlM_preserves_valid initial firstOps
                                  state updated hvalid
                                  (by simpa [executeFrom] using hreplay)
                              have htail := ih targets updated result restOps
                                hotherNot hvalidUpdated hr
                              exact htail.trans hfirst

/-- A selected row remains byte-for-byte the same working-row value
    after its own pass and all subsequently scheduled variable passes. -/
theorem selected_pivot_slot_is_finally_stable
    (initial : List Row) (v pivotSlot : Nat)
    (remaining candidates : List Nat)
    (state finished : SourceState initial) (operations : List Op)
    (pivotRow : Row)
    (hvalid : LiveRefsValid initial state)
    (hp : choosePivot initial v state candidates =
      some (pivotSlot, pivotRow))
    (h : emitSchedule initial (v :: remaining) candidates state =
      some (operations, finished)) :
    workingRow initial finished pivotSlot = some pivotRow := by
  let targets := candidates.filter (fun slot => slot != pivotSlot)
  have hpivotNot : pivotSlot ∉ targets := by
    simp [targets]
  have hpivot := (choosePivot_sound initial v state
    candidates pivotSlot pivotRow hp).2.1
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
                  rcases h with ⟨hops, hfinished⟩
                  subst finished
                  have hfirst := emitPass_preserves_outside initial v
                    pivotSlot pivotSlot targets state updated
                    firstOps pivotRow hpivotNot hpivotNot hpivot hvalid he
                  have hreplay := emitPass_replays initial v
                    pivotSlot targets state updated firstOps he
                  have hvalidUpdated : LiveRefsValid initial updated :=
                    foldlM_preserves_valid initial firstOps state updated
                      hvalid (by simpa [executeFrom] using hreplay)
                  have htail := schedule_preserves_outside_candidate_slots
                    initial remaining targets pivotSlot updated result
                    restOps hpivotNot hvalidUpdated hr
                  rw [htail, hfirst]
                  exact hpivot

#print axioms Witnora.G5RetiredSlotStability.schedule_preserves_outside_candidate_slots
#print axioms Witnora.G5RetiredSlotStability.selected_pivot_slot_is_finally_stable

end Witnora.G5RetiredSlotStability
