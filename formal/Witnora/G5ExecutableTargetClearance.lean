import Witnora.G5IndexedPivotClearance
import Witnora.G5EmittedPivotPass
import Witnora.G5SourceStepSemantics

/-!
# Actual executable target-row clearance

A successful call to the stateful emitOne generator reads a target row
and either emits a checked indexed XOR or performs a genuine no-op.
When its pivot row contains the scheduled variable, the resulting
observable target row always excludes that variable.

Unlike the source-order map theorem, this applies directly to
SourceState.step and its proof-carrying append-only DAG.
-/

namespace Witnora.G5ExecutableTargetClearance

open Witnora.G5Trace
open Witnora.G5IndexedOperationEmitter
open Witnora.G5IndexedRowValueRefinement
open Witnora.G5SourceStepSemantics
open Witnora.G5EmittedPivotPass
open Witnora.G5IndexedPivotClearance

/-- Every successfully emitted single-target pivot update clears the
    selected variable from the actual source working-row view. -/
theorem emitOne_clears_target
    (initial : List Row) (v pivotSlot targetSlot : Nat)
    (state result : SourceState initial) (operations : List Op)
    (pivotRef targetRef : Nat) (pivotRow targetRow : Row)
    (hne : targetSlot ≠ pivotSlot)
    (hpivot : state.refs[pivotSlot]? = some pivotRef)
    (htarget : state.refs[targetSlot]? = some targetRef)
    (hpivotRow : state.dag.rows[pivotRef]? = some pivotRow)
    (htargetRow : state.dag.rows[targetRef]? = some targetRow)
    (hvPivot : v ∈ pivotRow.coefficients)
    (h : emitOne initial v pivotSlot targetSlot state =
      some (operations, result)) :
    ∃ newRow,
      workingRow initial result targetSlot = some newRow ∧
      v ∉ newRow.coefficients := by
  have hview : workingRow initial state targetSlot =
      some targetRow := by
    simp [workingRow, htarget, htargetRow]
  by_cases hv : v ∈ targetRow.coefficients
  · cases hs : state.step initial (.addRowXor targetSlot pivotSlot) with
    | none =>
        simp [emitOne, hview, hv, hs] at h
    | some updated =>
        simp [emitOne, hview, hv, hs] at h
        rcases h with ⟨hops, hresult⟩
        subst result
        have hexact := xor_step_exact initial state
          targetSlot pivotSlot targetRef pivotRef
          targetRow pivotRow hne htarget hpivot htargetRow hpivotRow
        have heq : updated =
            xorUpdatedState initial state targetSlot targetRef pivotRef
              targetRow pivotRow htargetRow hpivotRow :=
          Option.some.inj (hs.symm.trans hexact)
        subst updated
        exact verified_indexed_xor_clears_target initial state v
          targetSlot targetRef pivotRef targetRow pivotRow
          htarget htargetRow hpivotRow hv hvPivot
  · simp [emitOne, hview, hv] at h
    rcases h with ⟨hops, hresult⟩
    subst result
    exact ⟨targetRow, hview, hv⟩

/-- The actual emitOne path, whether XOR or no-op, leaves every
    unrelated live working slot exactly unchanged. This supplies
    preservation of the pivot and previously processed targets. -/
theorem emitOne_preserves_other_slot
    (initial : List Row) (v pivotSlot targetSlot otherSlot : Nat)
    (state result : SourceState initial) (operations : List Op)
    (pivotRef targetRef : Nat) (pivotRow targetRow : Row)
    (hne : targetSlot ≠ pivotSlot)
    (hother : otherSlot ≠ targetSlot)
    (hpivot : state.refs[pivotSlot]? = some pivotRef)
    (htarget : state.refs[targetSlot]? = some targetRef)
    (hpivotRow : state.dag.rows[pivotRef]? = some pivotRow)
    (htargetRow : state.dag.rows[targetRef]? = some targetRow)
    (hvalid : ∀ (slot ref : Nat),
      state.refs[slot]? = some ref → ref < state.dag.rows.length)
    (h : emitOne initial v pivotSlot targetSlot state =
      some (operations, result)) :
    workingRow initial result otherSlot =
      workingRow initial state otherSlot := by
  have hview : workingRow initial state targetSlot =
      some targetRow := by
    simp [workingRow, htarget, htargetRow]
  by_cases hv : v ∈ targetRow.coefficients
  · cases hs : state.step initial (.addRowXor targetSlot pivotSlot) with
    | none =>
        simp [emitOne, hview, hv, hs] at h
    | some updated =>
        simp [emitOne, hview, hv, hs] at h
        rcases h with ⟨hops, hresult⟩
        subst result
        have hexact := xor_step_exact initial state
          targetSlot pivotSlot targetRef pivotRef
          targetRow pivotRow hne htarget hpivot htargetRow hpivotRow
        have heq : updated =
            xorUpdatedState initial state targetSlot targetRef pivotRef
              targetRow pivotRow htargetRow hpivotRow :=
          Option.some.inj (hs.symm.trans hexact)
        subst updated
        have hslots := xor_all_slots initial state targetSlot
          targetRef pivotRef targetRow pivotRow htarget
          htargetRow hpivotRow hvalid otherSlot
        simpa [hother] using hslots
  · simp [emitOne, hview, hv] at h
    rcases h with ⟨hops, hresult⟩
    subst result
    rfl

#print axioms Witnora.G5ExecutableTargetClearance.emitOne_preserves_other_slot

#print axioms Witnora.G5ExecutableTargetClearance.emitOne_clears_target

end Witnora.G5ExecutableTargetClearance
