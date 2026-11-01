import Witnora.G5EmittedPivotPass
import Witnora.G5FiniteTraceCorrespondence

/-!
# Independent replay for generated G5 pivot passes

The executable pivot-pass generator emits only source ADD_ROW_XOR
operations. This automatically discharges the non-self-swap condition
of the verified finite-trace interpreter correspondence.

Thus every successful generated pass has an independently replayed
G5Trace row table with exactly matching observable working rows.
-/

namespace Witnora.G5PivotPassIndependentReplay

open Witnora.G5Trace
open Witnora.G5IndexedOperationEmitter
open Witnora.G5RowTableRelation
open Witnora.G5SourceTraceSafety
open Witnora.G5FiniteTraceCorrespondence
open Witnora.G5EmittedPivotPass

/-- An emitted target step contains no swap and hence satisfies the
    finite-trace simulator's legal-operation condition. -/
theorem emitOne_no_self_swaps
    (initial : List Row) (v pivotSlot targetSlot : Nat)
    (state result : SourceState initial) (operations : List Op)
    (h : emitOne initial v pivotSlot targetSlot state =
      some (operations, result)) :
    ∀ op ∈ operations, NoSelfSwap op := by
  cases hr : Witnora.G5IndexedRowValueRefinement.workingRow
      initial state targetSlot with
  | none =>
      simp [emitOne, hr] at h
  | some targetRow =>
      by_cases hv : v ∈ targetRow.coefficients
      · cases hs : state.step initial (.addRowXor targetSlot pivotSlot) with
        | none =>
            simp [emitOne, hr, hv, hs] at h
        | some updated =>
            simp [emitOne, hr, hv, hs] at h
            rcases h with ⟨hops, hresult⟩
            subst operations
            intro op hm
            simp at hm
            subst op
            trivial
      · simp [emitOne, hr, hv] at h
        rcases h with ⟨hops, hresult⟩
        subst operations
        simp

/-- The whole generated pivot pass contains only legal source operations,
    for any finite input target sequence. -/
theorem emitPass_no_self_swaps
    (initial : List Row) (v pivotSlot : Nat)
    (targets : List Nat) (state result : SourceState initial)
    (operations : List Op)
    (h : emitPass initial v pivotSlot targets state =
      some (operations, result)) :
    ∀ op ∈ operations, NoSelfSwap op := by
  induction targets generalizing state operations result with
  | nil =>
      simp [emitPass] at h
      rcases h with ⟨hops, hresult⟩
      subst operations
      simp
  | cons target rest ih =>
      cases hf : emitOne initial v pivotSlot target state with
      | none =>
          simp [emitPass, hf] at h
      | some first =>
          cases first with
          | mk firstOps updated =>
              cases hr : emitPass initial v pivotSlot rest updated with
              | none =>
                  simp [emitPass, hf, hr] at h
              | some second =>
                  cases second with
                  | mk restOps finished =>
                      simp [emitPass, hf, hr] at h
                      rcases h with ⟨hops, hresult⟩
                      subst operations
                      intro op hm
                      rcases List.mem_append.mp hm with hfirst | hrest
                      · exact emitOne_no_self_swaps initial v pivotSlot
                          target state updated firstOps hf op hfirst
                      · exact ih updated restOps hr op hrest

/-- The independent G5 row-list replay matches every observable row of
    any successful generated pivot pass, starting at any related valid
    source/table state pair. -/
theorem emitPass_independent_replay
    (initial : List Row) (v pivotSlot : Nat)
    (targets : List Nat) (state result : SourceState initial)
    (rows : List Row) (operations : List Op)
    (hvalid : LiveRefsValid initial state)
    (hrel : TableRel initial state rows)
    (hpass : emitPass initial v pivotSlot targets state =
      some (operations, result)) :
    ∃ finalRows,
      replay rows (operations.map toReplayStep) = some finalRows ∧
      TableRel initial result finalRows := by
  exact foldlM_simulates initial operations state result rows
    hvalid hrel
    (emitPass_no_self_swaps initial v pivotSlot targets
      state result operations hpass)
    (emitPass_replays initial v pivotSlot targets
      state result operations hpass)

/-- Practical entry point: starting with the actual source interpreter
    and original rows, every successful emitted pass has an independent
    replay with exactly the same working-row view. -/
theorem emitted_from_initial_replays
    (initial : List Row) (v pivotSlot : Nat)
    (targets : List Nat) (result : SourceState initial)
    (operations : List Op)
    (hpass : emitPass initial v pivotSlot targets
      (SourceState.start initial) = some (operations, result)) :
    ∃ finalRows,
      replay initial (operations.map toReplayStep) = some finalRows ∧
      TableRel initial result finalRows := by
  exact emitPass_independent_replay initial v pivotSlot targets
    (SourceState.start initial) result initial operations
    (start_valid initial) (start_table_relation initial) hpass

#print axioms Witnora.G5PivotPassIndependentReplay.emitOne_no_self_swaps
#print axioms Witnora.G5PivotPassIndependentReplay.emitPass_no_self_swaps
#print axioms Witnora.G5PivotPassIndependentReplay.emitPass_independent_replay
#print axioms Witnora.G5PivotPassIndependentReplay.emitted_from_initial_replays

end Witnora.G5PivotPassIndependentReplay
