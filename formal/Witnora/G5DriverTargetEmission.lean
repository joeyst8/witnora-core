import Witnora.G5DriverXorOrderBridge
import Witnora.G5SourceStepSemantics

/-!
# Executable single-target Gaussian elimination emission

A genuine Gaussian pivot update (where the chosen variable is present
in the target row) can be represented by the existing source operation
ADD_ROW_XOR target pivot. Its source interpreter, independent G5 replay,
and direct Gaussian driver row semantics all agree.

The per-target theorem is the building block for compiling a complete
eliminatePass and ultimately eliminateVariables into indexed operations.
-/

namespace Witnora.G5DriverTargetEmission

open Witnora.G5Trace
open Witnora.G5Certificate
open Witnora.G5TerminatingPivot
open Witnora.G5IndexedOperationEmitter
open Witnora.G5IndexedRowValueRefinement
open Witnora.G5RowTableRelation
open Witnora.G5SourceStepSemantics
open Witnora.G5DriverXorOrderBridge

/-- Emit exactly one source XOR operation if the target contains the
    pivot variable, otherwise leave the target unchanged. -/
def emitTarget (v targetSlot pivotSlot : Nat) (targetRow : Row) :
    List Witnora.G5IndexedBridge.Operation :=
  if v ∈ targetRow.coefficients
    then [.addRowXor targetSlot pivotSlot]
    else []

theorem emitTarget_active (v targetSlot pivotSlot : Nat)
    (targetRow : Row) (h : v ∈ targetRow.coefficients) :
    emitTarget v targetSlot pivotSlot targetRow =
      [.addRowXor targetSlot pivotSlot] := by
  simp [emitTarget, h]

theorem emitTarget_inactive (v targetSlot pivotSlot : Nat)
    (targetRow : Row) (h : v ∉ targetRow.coefficients) :
    emitTarget v targetSlot pivotSlot targetRow = [] := by
  simp [emitTarget, h]

/-- A real pivot elimination can always be emitted as one checked indexed
    source operation with exactly the replayed target-first XOR row.
    Its semantic equation is the one used by the Gaussian driver. -/
theorem active_elimination_emits_exactly
    (bound v : Nat) (initial : List Row)
    (state : SourceState initial) (rows : List Row)
    (targetSlot pivotSlot targetRef pivotRef : Nat)
    (targetRow pivotRow : Row)
    (hrel : TableRel initial state rows)
    (hne : targetSlot ≠ pivotSlot)
    (htarget : state.refs[targetSlot]? = some targetRef)
    (hpivot : state.refs[pivotSlot]? = some pivotRef)
    (htargetRow : state.dag.rows[targetRef]? = some targetRow)
    (hpivotRow : state.dag.rows[pivotRef]? = some pivotRow)
    (hvalid : ∀ (slot ref : Nat),
      state.refs[slot]? = some ref → ref < state.dag.rows.length)
    (hactive : v ∈ targetRow.coefficients) :
    ∃ next nextRows,
      state.step initial (.addRowXor targetSlot pivotSlot) = some next ∧
      applyStep rows (.addXor targetSlot pivotSlot) = some nextRows ∧
      TableRel initial next nextRows ∧
      nextRows[targetSlot]? = some (xorRow targetRow pivotRow) ∧
      (∀ a : Nat → Bool,
        RowHolds bound (eliminateTarget v pivotRow targetRow) a ↔
        RowHolds bound (xorRow targetRow pivotRow) a) := by
  have hrowsTarget : rows[targetSlot]? = some targetRow := by
    simpa [TableRel, workingRow, htarget, htargetRow]
      using (hrel targetSlot).symm
  have hrowsPivot : rows[pivotSlot]? = some pivotRow := by
    simpa [TableRel, workingRow, hpivot, hpivotRow]
      using (hrel pivotSlot).symm
  refine ⟨xorUpdatedState initial state targetSlot targetRef pivotRef
      targetRow pivotRow htargetRow hpivotRow,
    rows.set targetSlot (xorRow targetRow pivotRow), ?_, ?_, ?_, ?_, ?_⟩
  · exact xor_step_exact initial state targetSlot pivotSlot
      targetRef pivotRef targetRow pivotRow hne
      htarget hpivot htargetRow hpivotRow
  · exact applyStep_addXor_exact rows targetSlot pivotSlot
      targetRow pivotRow hne hrowsTarget hrowsPivot
  · exact xor_preserves_table_relation initial state rows
      targetSlot targetRef pivotRef targetRow pivotRow hrel
      htarget htargetRow hpivotRow hvalid
  · exact row_lookup_set_self rows targetSlot targetRow
      (xorRow targetRow pivotRow) hrowsTarget
  · intro a
    simpa [eliminateTarget, hactive] using
      xorRow_comm_holds bound pivotRow targetRow a

/-- If no elimination is required, both driver and emitter leave the
    target row unchanged, and the emitted trace is empty. -/
theorem inactive_elimination_is_noop
    (v targetSlot pivotSlot : Nat) (pivotRow targetRow : Row)
    (hinactive : v ∉ targetRow.coefficients) :
    eliminateTarget v pivotRow targetRow = targetRow ∧
      emitTarget v targetSlot pivotSlot targetRow = [] := by
  simp [eliminateTarget, emitTarget, hinactive]

#print axioms Witnora.G5DriverTargetEmission.active_elimination_emits_exactly
#print axioms Witnora.G5DriverTargetEmission.inactive_elimination_is_noop

end Witnora.G5DriverTargetEmission
