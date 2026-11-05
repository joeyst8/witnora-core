import Witnora.G5ScheduledModelPreservation
import Witnora.G5DriverXorOrderBridge

/-!
# G5 source-order pivot-variable clearance

The indexed source emitter computes target XOR pivot. We prove this
operation removes the scheduled variable whenever both target and pivot
contain it, and that a full source-order elimination pass clears the
variable from every target. Duplicate attempts are idempotent after
the first successful clearance.

These are the support-normal-form lemmas needed to lift the emitted
scheduler's model equivalence to contradiction-discovery completeness.
-/

namespace Witnora.G5IndexedPivotClearance

open Witnora.G5Trace
open Witnora.G5DriverXorOrderBridge
open Witnora.G5IndexedRowValueRefinement
open Witnora.G5IndexedOperationEmitter

/-- Reversing XOR operands does not affect variable cancellation:
    target-first XOR removes v when both operands contain v. -/
theorem target_first_xor_clears
    (v : Nat) (target pivot : Row)
    (ht : v ∈ target.coefficients)
    (hp : v ∈ pivot.coefficients) :
    v ∉ (xorRow target pivot).coefficients := by
  intro hbad
  have hx := (mem_xorCoefficients
    target.coefficients pivot.coefficients v).mp hbad
  rcases hx with ⟨_, hn⟩ | ⟨_, hn⟩
  · exact hn hp
  · exact hn ht

/-- The source-order elimination function always removes the variable
    from a target, whether or not the target initially contained it. -/
theorem sourceOrderEliminateTarget_clears
    (v : Nat) (pivot target : Row)
    (hp : v ∈ pivot.coefficients) :
    v ∉ (sourceOrderEliminateTarget v pivot target).coefficients := by
  by_cases ht : v ∈ target.coefficients
  · simpa [sourceOrderEliminateTarget, ht] using
      target_first_xor_clears v target pivot ht hp
  · simpa [sourceOrderEliminateTarget, ht]

/-- A full finite source-order Gaussian pivot pass clears v from
    every transformed target row. -/
theorem sourceOrderEliminatePass_clears
    (v : Nat) (pivot : Row) (targets : List Row)
    (hp : v ∈ pivot.coefficients) :
    ∀ row ∈ sourceOrderEliminatePass v pivot targets,
      v ∉ row.coefficients := by
  intro row hr
  obtain ⟨original, _, heq⟩ := List.mem_map.mp
    (show row ∈ targets.map (sourceOrderEliminateTarget v pivot) from hr)
  subst row
  exact sourceOrderEliminateTarget_clears v pivot original hp

/-- After one successful source-order elimination, reprocessing the
    same target is a no-op. This handles duplicated target-slot visits. -/
theorem sourceOrderEliminateTarget_idempotent
    (v : Nat) (pivot target : Row)
    (hp : v ∈ pivot.coefficients) :
    sourceOrderEliminateTarget v pivot
      (sourceOrderEliminateTarget v pivot target) =
        sourceOrderEliminateTarget v pivot target := by
  have hclear :=
    sourceOrderEliminateTarget_clears v pivot target hp
  change (if v ∈ (sourceOrderEliminateTarget v pivot target).coefficients
    then xorRow (sourceOrderEliminateTarget v pivot target) pivot
    else sourceOrderEliminateTarget v pivot target) =
    sourceOrderEliminateTarget v pivot target
  simp [hclear]

/-- The explicit checked DAG append makes a mutable target slot contain
    the exact XOR row, and that row is free of the eliminated variable. -/
theorem verified_indexed_xor_clears_target
    (initial : List Row) (state : SourceState initial)
    (v targetSlot targetRef pivotRef : Nat)
    (targetRow pivotRow : Row)
    (hslot : state.refs[targetSlot]? = some targetRef)
    (htarget : state.dag.rows[targetRef]? = some targetRow)
    (hpivot : state.dag.rows[pivotRef]? = some pivotRow)
    (hvTarget : v ∈ targetRow.coefficients)
    (hvPivot : v ∈ pivotRow.coefficients) :
    ∃ newRow,
      workingRow initial
        (xorUpdatedState initial state targetSlot targetRef pivotRef
          targetRow pivotRow htarget hpivot)
        targetSlot = some newRow ∧
      v ∉ newRow.coefficients := by
  refine ⟨xorRow targetRow pivotRow, ?_, ?_⟩
  · exact xor_target_has_exact_new_row initial state
      targetSlot targetRef pivotRef targetRow pivotRow
      hslot htarget hpivot
  · exact target_first_xor_clears v targetRow pivotRow
      hvTarget hvPivot

#print axioms Witnora.G5IndexedPivotClearance.target_first_xor_clears
#print axioms Witnora.G5IndexedPivotClearance.sourceOrderEliminatePass_clears
#print axioms Witnora.G5IndexedPivotClearance.sourceOrderEliminateTarget_idempotent
#print axioms Witnora.G5IndexedPivotClearance.verified_indexed_xor_clears_target

end Witnora.G5IndexedPivotClearance
