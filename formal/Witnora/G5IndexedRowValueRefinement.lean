import Witnora.G5IndexedReferenceSafety
import Witnora.G5IndexedOperationEmitter

/-!
# G5 indexed source row-value refinement

A source working slot is a mutable reference into a shared append-only DAG.
These lemmas establish that an XOR update changes the target slot to the
exact derived XOR row, while every unrelated slot keeps its old row value.
This is the semantic local-update invariant for the full interpreter
simulation; it is not the completed Gaussian-to-DAG trace existence proof.
-/

namespace Witnora.G5IndexedRowValueRefinement

open Witnora.G5Trace
open Witnora.G5VerifiedDagEmitter
open Witnora.G5IndexedOperationEmitter

/-- Updating an existing list position makes that value retrievable. -/
theorem lookup_set_self (xs : List Nat) (i old replacement : Nat)
    (hi : xs[i]? = some old) :
    (xs.set i replacement)[i]? = some replacement := by
  induction xs generalizing i with
  | nil =>
      cases i <;> simp at hi
  | cons head tail ih =>
      cases i with
      | zero =>
          rfl
      | succ j =>
          have ht : tail[j]? = some old := by simpa using hi
          simpa [List.set] using ih j ht

/-- Updating one list slot leaves any other slot unchanged. -/
theorem lookup_set_other (xs : List Nat)
    (target other replacement : Nat)
    (hne : target ≠ other) :
    (xs.set target replacement)[other]? = xs[other]? := by
  induction xs generalizing target other with
  | nil =>
      cases target <;> cases other <;> rfl
  | cons head tail ih =>
      cases target with
      | zero =>
          cases other with
          | zero =>
              exact False.elim (hne rfl)
          | succ j =>
              rfl
      | succ i =>
          cases other with
          | zero =>
              rfl
          | succ j =>
              have hn : i ≠ j := by
                intro h
                exact hne (congrArg Nat.succ h)
              simpa [List.set] using ih i j hn

/-- Evaluate a mutable source slot by dereferencing its DAG row index. -/
def workingRow (initial : List Row)
    (state : SourceState initial) (slot : Nat) : Option Row := do
  let ref ← state.refs[slot]?
  state.dag.rows[ref]?

/-- The precise state created by the accepted source XOR branch. -/
def xorUpdatedState
    (initial : List Row) (state : SourceState initial)
    (targetSlot targetRef sourceRef : Nat)
    (targetRow sourceRow : Row)
    (htr : state.dag.rows[targetRef]? = some targetRow)
    (hsr : state.dag.rows[sourceRef]? = some sourceRow) :
    SourceState initial where
  dag := state.dag.append initial
    targetRef sourceRef targetRow sourceRow htr hsr
  refs := state.refs.set targetSlot state.dag.rows.length

/-- The new target slot denotes exactly targetRow XOR sourceRow. -/
theorem xor_target_has_exact_new_row
    (initial : List Row) (state : SourceState initial)
    (targetSlot targetRef sourceRef : Nat)
    (targetRow sourceRow : Row)
    (ht : state.refs[targetSlot]? = some targetRef)
    (htr : state.dag.rows[targetRef]? = some targetRow)
    (hsr : state.dag.rows[sourceRef]? = some sourceRow) :
    workingRow initial
      (xorUpdatedState initial state targetSlot targetRef sourceRef
        targetRow sourceRow htr hsr)
      targetSlot = some (xorRow targetRow sourceRow) := by
  have hset := lookup_set_self state.refs targetSlot
    targetRef state.dag.rows.length ht
  have hnew := Builder.append_new_index initial state.dag
    targetRef sourceRef targetRow sourceRow htr hsr
  simp [workingRow, xorUpdatedState, hset, hnew]

/-- A source slot unaffected by the indexed XOR target still reads exactly
    the same old row; the DAG append preserves its original reference. -/
theorem xor_other_slot_unchanged
    (initial : List Row) (state : SourceState initial)
    (targetSlot otherSlot targetRef sourceRef otherRef : Nat)
    (targetRow sourceRow otherRow : Row)
    (hne : targetSlot ≠ otherSlot)
    (ho : state.refs[otherSlot]? = some otherRef)
    (hro : state.dag.rows[otherRef]? = some otherRow)
    (htr : state.dag.rows[targetRef]? = some targetRow)
    (hsr : state.dag.rows[sourceRef]? = some sourceRow) :
    workingRow initial
      (xorUpdatedState initial state targetSlot targetRef sourceRef
        targetRow sourceRow htr hsr) otherSlot =
      some otherRow := by
  have hset := lookup_set_other state.refs
    targetSlot otherSlot state.dag.rows.length hne
  have hold := Builder.append_preserves_lookup initial state.dag
    targetRef sourceRef otherRef targetRow sourceRow otherRow htr hsr hro
  simp [workingRow, xorUpdatedState, hset, ho, hold]

#print axioms Witnora.G5IndexedRowValueRefinement.lookup_set_self
#print axioms Witnora.G5IndexedRowValueRefinement.lookup_set_other
#print axioms Witnora.G5IndexedRowValueRefinement.xor_target_has_exact_new_row
#print axioms Witnora.G5IndexedRowValueRefinement.xor_other_slot_unchanged

end Witnora.G5IndexedRowValueRefinement
