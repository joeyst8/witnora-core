import Witnora.G5RowTableRelation

/-!
# Source operation and independent G5 replay step agreement

The verified DAG-backed interpreter and the independent G5Trace.applyStep
execute the same row updates for legal indexed operations, with exact
reference and DAG lookup witnesses. These are executable source-step
refinement lemmas, not merely hypothetical list update lemmas.
-/

namespace Witnora.G5SourceStepSemantics

open Witnora.G5Trace
open Witnora.G5IndexedOperationEmitter
open Witnora.G5IndexedRowValueRefinement
open Witnora.G5RowTableRelation

theorem swap_step_exact
    (initial : List Row) (state : SourceState initial)
    (i j leftRef rightRef : Nat)
    (hi : state.refs[i]? = some leftRef)
    (hj : state.refs[j]? = some rightRef) :
    state.step initial (.swapRows i j) =
      some (swapUpdatedState initial state i j leftRef rightRef) := by
  simp [SourceState.step, hi, hj, swapUpdatedState]

theorem xor_step_exact
    (initial : List Row) (state : SourceState initial)
    (target source targetRef sourceRef : Nat)
    (targetRow sourceRow : Row)
    (hne : target ≠ source)
    (hi : state.refs[target]? = some targetRef)
    (hj : state.refs[source]? = some sourceRef)
    (ht : state.dag.rows[targetRef]? = some targetRow)
    (hs : state.dag.rows[sourceRef]? = some sourceRow) :
    state.step initial (.addRowXor target source) =
      some (xorUpdatedState initial state target targetRef sourceRef
        targetRow sourceRow ht hs) := by
  have hneq : (target == source) = false := decide_eq_false hne
  simp [SourceState.step, hneq, hi, hj, ht, hs, xorUpdatedState]

theorem swap_agrees_with_replay
    (initial : List Row) (state : SourceState initial)
    (rows : List Row) (i j leftRef rightRef : Nat)
    (leftRow rightRow : Row)
    (hrel : TableRel initial state rows)
    (hne : i ≠ j)
    (hi : state.refs[i]? = some leftRef)
    (hj : state.refs[j]? = some rightRef)
    (hl : rows[i]? = some leftRow)
    (hr : rows[j]? = some rightRow) :
    ∃ next nextRows,
      state.step initial (.swapRows i j) = some next ∧
      applyStep rows (.swap i j) = some nextRows ∧
      TableRel initial next nextRows := by
  refine ⟨swapUpdatedState initial state i j leftRef rightRef,
    (rows.set i rightRow).set j leftRow, ?_, ?_, ?_⟩
  · exact swap_step_exact initial state i j leftRef rightRef hi hj
  · exact applyStep_swap_exact rows i j leftRow rightRow hl hr
  · exact swap_preserves_table_relation initial state rows
      i j leftRef rightRef leftRow rightRow hrel hne hi hj hl hr

theorem xor_agrees_with_replay
    (initial : List Row) (state : SourceState initial)
    (rows : List Row)
    (target source targetRef sourceRef : Nat)
    (targetRow sourceRow : Row)
    (hrel : TableRel initial state rows)
    (hne : target ≠ source)
    (hi : state.refs[target]? = some targetRef)
    (hj : state.refs[source]? = some sourceRef)
    (ht : state.dag.rows[targetRef]? = some targetRow)
    (hs : state.dag.rows[sourceRef]? = some sourceRow)
    (hvalid : ∀ (slot ref : Nat),
      state.refs[slot]? = some ref → ref < state.dag.rows.length) :
    ∃ next nextRows,
      state.step initial (.addRowXor target source) = some next ∧
      applyStep rows (.addXor target source) = some nextRows ∧
      TableRel initial next nextRows := by
  have hrowTarget : rows[target]? = some targetRow := by
    simpa [TableRel, workingRow, hi, ht] using (hrel target).symm
  have hrowSource : rows[source]? = some sourceRow := by
    simpa [TableRel, workingRow, hj, hs] using (hrel source).symm
  refine ⟨xorUpdatedState initial state target targetRef sourceRef
      targetRow sourceRow ht hs,
    rows.set target (xorRow targetRow sourceRow), ?_, ?_, ?_⟩
  · exact xor_step_exact initial state target source targetRef sourceRef
      targetRow sourceRow hne hi hj ht hs
  · exact applyStep_addXor_exact rows target source targetRow sourceRow
      hne hrowTarget hrowSource
  · exact xor_preserves_table_relation initial state rows
      target targetRef sourceRef targetRow sourceRow hrel hi ht hs hvalid

#print axioms Witnora.G5SourceStepSemantics.swap_step_exact
#print axioms Witnora.G5SourceStepSemantics.xor_step_exact
#print axioms Witnora.G5SourceStepSemantics.swap_agrees_with_replay
#print axioms Witnora.G5SourceStepSemantics.xor_agrees_with_replay

end Witnora.G5SourceStepSemantics
