import Witnora.G5IndexedPivotSelection
import Witnora.G5PivotPassIndependentReplay

/-!
# A terminating indexed G5 elimination schedule emitter

The finite variable schedule drives deterministic indexed pivot selection
and the verified source XOR pass emitter. When a variable has no available
pivot, the scheduler skips it. When a pivot is selected, it is removed
from subsequent candidate slots after its complete elimination pass.

The emitted source-operation trace replays exactly to the returned
proof-carrying DAG state, and contains only legal XOR operations.
Matching all residual rows to the older eliminateVariables driver remains
a separate refinement obligation.
-/

namespace Witnora.G5IndexedScheduledEmitter

open Witnora.G5Trace
open Witnora.G5IndexedOperationEmitter
open Witnora.G5EmittedPivotPass
open Witnora.G5IndexedPivotSelection
open Witnora.G5PivotPassIndependentReplay
open Witnora.G5FiniteTraceCorrespondence
open Witnora.G5RowTableRelation
open Witnora.G5SourceTraceSafety

/-- Iterate a finite variable schedule. Each chosen pivot slot is retired
    from future target slots, and all operations are checked while emitted. -/
def emitSchedule (initial : List Row) :
    List Nat → List Nat → SourceState initial →
      Option (List Op × SourceState initial)
  | [], _, state => some ([], state)
  | v :: remaining, candidates, state =>
      match choosePivot initial v state candidates with
      | none => emitSchedule initial remaining candidates state
      | some (pivotSlot, _) => do
          let targets := candidates.filter (fun slot => slot != pivotSlot)
          let (firstOps, updated) ←
            emitPass initial v pivotSlot targets state
          let (restOps, finished) ←
            emitSchedule initial remaining targets updated
          return (firstOps ++ restOps, finished)

/-- A generated scheduled operation trace is exactly executable by the
    actual proof-carrying source interpreter for every finite schedule. -/
theorem emitSchedule_replays
    (initial : List Row)
    (variables candidates : List Nat)
    (state result : SourceState initial) (operations : List Op)
    (h : emitSchedule initial variables candidates state =
      some (operations, result)) :
    executeFrom initial state operations = some result := by
  induction variables generalizing candidates state operations with
  | nil =>
      simp [emitSchedule] at h
      rcases h with ⟨hops, hresult⟩
      subst operations
      subst result
      rfl
  | cons v rest ih =>
      cases hp : choosePivot initial v state candidates with
      | none =>
          have hrest : emitSchedule initial rest candidates state =
              some (operations, result) := by
            simpa [emitSchedule, hp] using h
          exact ih candidates state operations hrest
      | some choice =>
          cases choice with
          | mk pivotSlot pivotRow =>
              let targets := candidates.filter (fun slot => slot != pivotSlot)
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
                          | mk restOps finished =>
                              simp [emitSchedule, hp, targets, he, hr] at h
                              rcases h with ⟨hops, hresult⟩
                              subst operations
                              subst result
                              rw [executeFrom_append]
                              rw [emitPass_replays initial v pivotSlot
                                targets state updated firstOps he]
                              exact ih targets updated restOps hr

/-- Every generated scheduled trace contains only ADD_ROW_XOR operations.
    No source swap or self-swap is introduced by pivot scheduling. -/
theorem emitSchedule_no_self_swaps
    (initial : List Row)
    (variables candidates : List Nat)
    (state result : SourceState initial) (operations : List Op)
    (h : emitSchedule initial variables candidates state =
      some (operations, result)) :
    ∀ op ∈ operations, NoSelfSwap op := by
  induction variables generalizing candidates state result operations with
  | nil =>
      simp [emitSchedule] at h
      rcases h with ⟨hops, hresult⟩
      subst operations
      simp
  | cons v rest ih =>
      cases hp : choosePivot initial v state candidates with
      | none =>
          have hrest : emitSchedule initial rest candidates state =
              some (operations, result) := by
            simpa [emitSchedule, hp] using h
          exact ih candidates state result operations hrest
      | some choice =>
          cases choice with
          | mk pivotSlot pivotRow =>
              let targets := candidates.filter (fun slot => slot != pivotSlot)
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
                          | mk restOps finished =>
                              simp [emitSchedule, hp, targets, he, hr] at h
                              rcases h with ⟨hops, hresult⟩
                              subst operations
                              intro op hmem
                              rcases List.mem_append.mp hmem with hf | hs
                              · exact emitPass_no_self_swaps initial v
                                  pivotSlot targets state updated firstOps
                                  he op hf
                              · exact ih targets updated finished restOps
                                  hr op hs

/-- The entire generated variable schedule agrees with the independent
    G5Trace replay, for any initial related live-reference state. -/
theorem emitted_schedule_independent_replay
    (initial : List Row)
    (variables candidates : List Nat)
    (state result : SourceState initial) (rows : List Row)
    (operations : List Op)
    (hvalid : LiveRefsValid initial state)
    (hrel : TableRel initial state rows)
    (h : emitSchedule initial variables candidates state =
      some (operations, result)) :
    ∃ finalRows,
      replay rows (operations.map toReplayStep) = some finalRows ∧
      TableRel initial result finalRows := by
  exact foldlM_simulates initial operations state result rows
    hvalid hrel
    (emitSchedule_no_self_swaps initial variables candidates
      state result operations h)
    (emitSchedule_replays initial variables candidates
      state result operations h)

#print axioms Witnora.G5IndexedScheduledEmitter.emitSchedule_replays
#print axioms Witnora.G5IndexedScheduledEmitter.emitSchedule_no_self_swaps
#print axioms Witnora.G5IndexedScheduledEmitter.emitted_schedule_independent_replay

end Witnora.G5IndexedScheduledEmitter
