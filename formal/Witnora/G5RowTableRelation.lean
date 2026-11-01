import Witnora.G5SourceTraceSafety

/-!
# G5 exact row-table relation

The indexed DAG interpreter's observable slots correspond pointwise to
an independent working List Row. Verified XOR and distinct swap updates
preserve that relation with G5Trace's concrete row-list updates.
-/

namespace Witnora.G5RowTableRelation

open Witnora.G5Trace
open Witnora.G5IndexedOperationEmitter
open Witnora.G5IndexedRowValueRefinement
open Witnora.G5IndexedViewSimulation

def TableRel (initial : List Row)
    (state : SourceState initial) (rows : List Row) : Prop :=
  ∀ slot, workingRow initial state slot = rows[slot]?

theorem row_lookup_set_self (xs : List Row) (i : Nat)
    (old replacement : Row) (hi : xs[i]? = some old) :
    (xs.set i replacement)[i]? = some replacement := by
  induction xs generalizing i with
  | nil =>
      cases i <;> simp at hi
  | cons head tail ih =>
      cases i with
      | zero => rfl
      | succ j =>
          have ht : tail[j]? = some old := by simpa using hi
          simpa [List.set] using ih j ht

theorem row_lookup_set_other (xs : List Row)
    (target other : Nat) (replacement : Row)
    (hne : target ≠ other) :
    (xs.set target replacement)[other]? = xs[other]? := by
  induction xs generalizing target other with
  | nil =>
      cases target <;> cases other <;> rfl
  | cons head tail ih =>
      cases target with
      | zero =>
          cases other with
          | zero => exact False.elim (hne rfl)
          | succ j => rfl
      | succ i =>
          cases other with
          | zero => rfl
          | succ j =>
              have hn : i ≠ j := by
                intro h
                exact hne (congrArg Nat.succ h)
              simpa [List.set] using ih i j hn

theorem xor_preserves_table_relation
    (initial : List Row) (state : SourceState initial)
    (rows : List Row)
    (targetSlot targetRef sourceRef : Nat)
    (targetRow sourceRow : Row)
    (hrel : TableRel initial state rows)
    (ht : state.refs[targetSlot]? = some targetRef)
    (htr : state.dag.rows[targetRef]? = some targetRow)
    (hsr : state.dag.rows[sourceRef]? = some sourceRow)
    (hvalid : ∀ (slot ref : Nat),
      state.refs[slot]? = some ref → ref < state.dag.rows.length) :
    TableRel initial
      (xorUpdatedState initial state targetSlot targetRef sourceRef
        targetRow sourceRow htr hsr)
      (rows.set targetSlot (xorRow targetRow sourceRow)) := by
  intro slot
  rw [xor_all_slots initial state targetSlot targetRef sourceRef
    targetRow sourceRow ht htr hsr hvalid slot]
  by_cases heq : slot = targetSlot
  · subst slot
    have hrow : rows[targetSlot]? = some targetRow := by
      simpa [TableRel, workingRow, ht, htr] using (hrel targetSlot).symm
    simp [row_lookup_set_self rows targetSlot targetRow
      (xorRow targetRow sourceRow) hrow]
  · rw [row_lookup_set_other rows targetSlot slot
      (xorRow targetRow sourceRow) (Ne.symm heq)]
    simp [heq, hrel slot]

theorem swap_preserves_table_relation
    (initial : List Row) (state : SourceState initial)
    (rows : List Row) (i j leftRef rightRef : Nat)
    (leftRow rightRow : Row)
    (hrel : TableRel initial state rows)
    (hne : i ≠ j)
    (hi : state.refs[i]? = some leftRef)
    (hj : state.refs[j]? = some rightRef)
    (hl : rows[i]? = some leftRow)
    (hr : rows[j]? = some rightRow) :
    TableRel initial
      (swapUpdatedState initial state i j leftRef rightRef)
      ((rows.set i rightRow).set j leftRow) := by
  intro slot
  rw [swap_all_slots initial state i j leftRef rightRef hne hi hj slot]
  by_cases hsi : slot = i
  · subst slot
    have hfirst := row_lookup_set_self rows i leftRow rightRow hl
    have hsecond := row_lookup_set_other (rows.set i rightRow)
      j i leftRow (Ne.symm hne)
    simp [hsecond, hfirst, hrel j, hr]
  · by_cases hsj : slot = j
    · subst slot
      have hpre : (rows.set i rightRow)[j]? = some rightRow := by
        rw [row_lookup_set_other rows i j rightRow hne]
        exact hr
      have hlast := row_lookup_set_self (rows.set i rightRow)
        j rightRow leftRow hpre
      simp [hlast, hrel i, hl, hsi]
    · have hfirst := row_lookup_set_other rows
        i slot rightRow (Ne.symm hsi)
      have hsecond := row_lookup_set_other (rows.set i rightRow)
        j slot leftRow (Ne.symm hsj)
      simp [hfirst, hsecond, hsi, hsj, hrel slot]

#print axioms Witnora.G5RowTableRelation.row_lookup_set_self
#print axioms Witnora.G5RowTableRelation.row_lookup_set_other
#print axioms Witnora.G5RowTableRelation.xor_preserves_table_relation
#print axioms Witnora.G5RowTableRelation.swap_preserves_table_relation

end Witnora.G5RowTableRelation
