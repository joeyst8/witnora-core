import Witnora.G5IndexedRowValueRefinement

/-!
# Universal G5 indexed working-view simulation

The source interpreter stores references to DAG rows, not a second row table.
A legal XOR changes exactly one observable working slot; a legal swap
interchanges exactly two. We state these facts pointwise for *all* slots,
including absent ones, under a validity invariant for live references.

This is the local semantic simulation lemma needed for a future finite-trace
induction. It does not yet construct Gaussian driver operation traces.
-/

namespace Witnora.G5IndexedViewSimulation

open Witnora.G5Trace
open Witnora.G5IndexedOperationEmitter
open Witnora.G5IndexedRowValueRefinement

/-- A list append does not change a lookup strictly inside the old list. -/
theorem lookup_append_of_lt {α : Type} (xs ys : List α) (i : Nat)
    (hi : i < xs.length) :
    (xs ++ ys)[i]? = xs[i]? := by
  induction xs generalizing i with
  | nil =>
      simp at hi
  | cons x tail ih =>
      cases i with
      | zero => rfl
      | succ j =>
          have hj : j < tail.length := by simpa using hi
          simpa using ih j hj

/-- Any live reference that remains in range retains precisely its value
    when an XOR row is appended. -/
theorem append_preserves_live_lookup
    (initial : List Row) (state : SourceState initial)
    (targetRef sourceRef ref : Nat) (targetRow sourceRow : Row)
    (htr : state.dag.rows[targetRef]? = some targetRow)
    (hsr : state.dag.rows[sourceRef]? = some sourceRow)
    (hvalid : ref < state.dag.rows.length) :
    (state.dag.append initial targetRef sourceRef
      targetRow sourceRow htr hsr).rows[ref]? =
      state.dag.rows[ref]? := by
  exact lookup_append_of_lt state.dag.rows
    [xorRow targetRow sourceRow] ref hvalid

/-- All working slots obey XOR's exact pointwise update law.
    The global validity hypothesis rules out dormant references that could
    become newly addressable just because the DAG grew. -/
theorem xor_all_slots
    (initial : List Row) (state : SourceState initial)
    (targetSlot targetRef sourceRef : Nat)
    (targetRow sourceRow : Row)
    (ht : state.refs[targetSlot]? = some targetRef)
    (htr : state.dag.rows[targetRef]? = some targetRow)
    (hsr : state.dag.rows[sourceRef]? = some sourceRow)
    (hvalid : ∀ slot ref,
      state.refs[slot]? = some ref → ref < state.dag.rows.length)
    (slot : Nat) :
    workingRow initial
      (xorUpdatedState initial state targetSlot targetRef sourceRef
        targetRow sourceRow htr hsr) slot =
    if slot = targetSlot then some (xorRow targetRow sourceRow)
    else workingRow initial state slot := by
  by_cases heq : slot = targetSlot
  · subst slot
    simp [xor_target_has_exact_new_row initial state
      targetSlot targetRef sourceRef targetRow sourceRow ht htr hsr]
  · have hne : targetSlot ≠ slot := Ne.symm heq
    have hset := lookup_set_other state.refs
      targetSlot slot state.dag.rows.length hne
    cases hr : state.refs[slot]? with
    | none =>
        simp [workingRow, xorUpdatedState, hset, hr, heq]
    | some ref =>
        have hv : ref < state.dag.rows.length :=
          hvalid slot ref hr
        have hkeep := append_preserves_live_lookup initial state
          targetRef sourceRef ref targetRow sourceRow htr hsr hv
        simp [workingRow, xorUpdatedState, hset, hr, hkeep, heq]

/-- Swapping two different live indices exchanges their values and leaves
    all other (even absent) slots unchanged. -/
theorem swap_all_slots
    (initial : List Row) (state : SourceState initial)
    (i j leftRef rightRef : Nat)
    (hne : i ≠ j)
    (hi : state.refs[i]? = some leftRef)
    (hj : state.refs[j]? = some rightRef)
    (slot : Nat) :
    workingRow initial
      (swapUpdatedState initial state i j leftRef rightRef) slot =
    if slot = i then workingRow initial state j
    else if slot = j then workingRow initial state i
    else workingRow initial state slot := by
  by_cases hsi : slot = i
  · subst slot
    have hfirst := lookup_set_self state.refs i leftRef rightRef hi
    have hsecond := lookup_set_other (state.refs.set i rightRef)
      j i leftRef (Ne.symm hne)
    simp [workingRow, swapUpdatedState, hfirst, hsecond, hj]
  · by_cases hsj : slot = j
    · subst slot
      have hpre : (state.refs.set i rightRef)[j]? = some rightRef := by
        rw [lookup_set_other state.refs i j rightRef hne]
        exact hj
      have hlast := lookup_set_self (state.refs.set i rightRef)
        j rightRef leftRef hpre
      simp [workingRow, swapUpdatedState, hlast, hi, hsi]
    · have hfirst := lookup_set_other state.refs
        i slot rightRef (Ne.symm hsi)
      have hsecond := lookup_set_other (state.refs.set i rightRef)
        j slot leftRef (Ne.symm hsj)
      simp [workingRow, swapUpdatedState, hfirst, hsecond, hsi, hsj]

#print axioms Witnora.G5IndexedViewSimulation.lookup_append_of_lt
#print axioms Witnora.G5IndexedViewSimulation.xor_all_slots
#print axioms Witnora.G5IndexedViewSimulation.swap_all_slots

end Witnora.G5IndexedViewSimulation
