import Witnora.G5ExecutableTargetClearance
import Witnora.G5SourceTraceSafety

/-!
# Full-pass G5 working-row pivot clearance

Generalize the actual single-target clearance and unrelated-slot
preservation theorems to workingRow-level hypotheses, then lift them
through arbitrary finite emitted passes under stable-pivot and
distinct-target conditions. This is the executable normal-form bridge
for contradiction completeness.
-/

namespace Witnora.G5ExecutablePassClearance

open Witnora.G5Trace
open Witnora.G5IndexedOperationEmitter
open Witnora.G5IndexedRowValueRefinement
open Witnora.G5ExecutableTargetClearance
open Witnora.G5EmittedPivotPass
open Witnora.G5SourceTraceSafety

/-- A successfully dereferenced working row yields both its live
    reference and the concrete DAG row lookup witness. -/
theorem workingRow_derefs
    (initial : List Row) (state : SourceState initial)
    (slot : Nat) (row : Row)
    (h : workingRow initial state slot = some row) :
    ∃ ref, state.refs[slot]? = some ref ∧
      state.dag.rows[ref]? = some row := by
  unfold workingRow at h
  cases hr : state.refs[slot]? with
  | none =>
      simp [hr] at h
  | some ref =>
      have hrow : state.dag.rows[ref]? = some row := by
        simpa [hr] using h
      exact ⟨ref, rfl, hrow⟩

/-- Every successful target emitter step clears v, stated only using
    observable working-row lookups rather than internal DAG indices. -/
theorem emitOne_clears_view
    (initial : List Row) (v pivotSlot targetSlot : Nat)
    (state result : SourceState initial) (operations : List Op)
    (pivotRow : Row)
    (hne : targetSlot ≠ pivotSlot)
    (hpivot : workingRow initial state pivotSlot = some pivotRow)
    (hv : v ∈ pivotRow.coefficients)
    (h : emitOne initial v pivotSlot targetSlot state =
      some (operations, result)) :
    ∃ newRow,
      workingRow initial result targetSlot = some newRow ∧
      v ∉ newRow.coefficients := by
  obtain ⟨pivotRef, hpref, hprow⟩ :=
    workingRow_derefs initial state pivotSlot pivotRow hpivot
  cases ht : workingRow initial state targetSlot with
  | none =>
      simp [emitOne, ht] at h
  | some targetRow =>
      obtain ⟨targetRef, htref, htrow⟩ :=
        workingRow_derefs initial state targetSlot targetRow ht
      exact emitOne_clears_target initial v pivotSlot targetSlot
        state result operations pivotRef targetRef pivotRow targetRow
        hne hpref htref hprow htrow hv h

/-- Updating one indexed target preserves any other working-row view,
    for all initially valid live DAG references. -/
theorem emitOne_preserves_other_view
    (initial : List Row) (v pivotSlot targetSlot otherSlot : Nat)
    (state result : SourceState initial) (operations : List Op)
    (pivotRow : Row)
    (hne : targetSlot ≠ pivotSlot)
    (hother : otherSlot ≠ targetSlot)
    (hpivot : workingRow initial state pivotSlot = some pivotRow)
    (hvalid : LiveRefsValid initial state)
    (h : emitOne initial v pivotSlot targetSlot state =
      some (operations, result)) :
    workingRow initial result otherSlot =
      workingRow initial state otherSlot := by
  obtain ⟨pivotRef, hpref, hprow⟩ :=
    workingRow_derefs initial state pivotSlot pivotRow hpivot
  cases ht : workingRow initial state targetSlot with
  | none =>
      simp [emitOne, ht] at h
  | some targetRow =>
      obtain ⟨targetRef, htref, htrow⟩ :=
        workingRow_derefs initial state targetSlot targetRow ht
      exact emitOne_preserves_other_slot initial v pivotSlot
        targetSlot otherSlot state result operations
        pivotRef targetRef pivotRow targetRow hne hother
        hpref htref hprow htrow
        (fun slot ref hr => valid_lookup initial state hvalid slot ref hr)
        h

/-- Accepted single-target emission preserves the live-reference
    invariant through its exact source interpreter replay. -/
theorem emitOne_preserves_valid
    (initial : List Row) (v pivotSlot targetSlot : Nat)
    (state result : SourceState initial) (operations : List Op)
    (hvalid : LiveRefsValid initial state)
    (h : emitOne initial v pivotSlot targetSlot state =
      some (operations, result)) :
    LiveRefsValid initial result := by
  have hrun := emitOne_replays initial v pivotSlot targetSlot
    state result operations h
  exact foldlM_preserves_valid initial operations state result
    hvalid (by simpa [executeFrom] using hrun)

#print axioms Witnora.G5ExecutablePassClearance.workingRow_derefs
#print axioms Witnora.G5ExecutablePassClearance.emitOne_clears_view
#print axioms Witnora.G5ExecutablePassClearance.emitOne_preserves_other_view
#print axioms Witnora.G5ExecutablePassClearance.emitOne_preserves_valid

end Witnora.G5ExecutablePassClearance
