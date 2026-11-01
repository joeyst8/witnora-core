import Witnora.G5FiniteTraceCorrespondence
import Witnora.G5TerminatingPivot

/-!
# Driver-to-certificate XOR operand order bridge

The Gaussian driver uses xorRow pivot target, while the executable
indexed source emitter uses xorRow target pivot. Sparse list ordering is
not canonical, so these Row values are generally not definitionally equal.

We prove universal equality of the affine equation's right-hand side and
support membership, then model-equivalence for every assignment, and
finally connect the actual driver's eliminateTarget operation to a
source-order row update.
-/

namespace Witnora.G5DriverXorOrderBridge

open Witnora.G5Trace
open Witnora.G5Certificate
open Witnora.G5TerminatingPivot
open Witnora.SparseParity

/-- XOR swaps produce the same RHS for any two sparse rows. -/
theorem xorRow_rhs_comm (pivot target : Row) :
    (xorRow pivot target).rhs = (xorRow target pivot).rhs := by
  simp [xorRow, Bool.xor_comm]

/-- The two operand orders have exactly the same support membership,
    irrespective of the ordering of the resulting coefficient lists. -/
theorem xorRow_support_comm (pivot target : Row) (v : Nat) :
    v ∈ (xorRow pivot target).coefficients ↔
      v ∈ (xorRow target pivot).coefficients := by
  simp only [xorRow, mem_xorCoefficients]
  constructor
  · intro h
    exact h.elim Or.inr Or.inl
  · intro h
    exact h.elim Or.inr Or.inl

/-- The independent sparse-parity evaluator sees the same equation in
    either operand order, for every bound and every Boolean assignment. -/
theorem xorRow_comm_holds (bound : Nat) (pivot target : Row)
    (a : Nat → Bool) :
    RowHolds bound (xorRow pivot target) a ↔
      RowHolds bound (xorRow target pivot) a := by
  simp only [RowHolds, xorRow, sparseParity_xor]
  simp [Bool.xor_comm]

/-- Source-order update: target XOR pivot rather than pivot XOR target. -/
def sourceOrderEliminateTarget (v : Nat) (pivot target : Row) : Row :=
  if v ∈ target.coefficients then xorRow target pivot else target

/-- A single driver update and its source-order indexed representation
    have precisely the same satisfying assignments. -/
theorem eliminateTarget_source_order_equiv
    (bound v : Nat) (pivot target : Row) (a : Nat → Bool) :
    RowHolds bound (eliminateTarget v pivot target) a ↔
      RowHolds bound (sourceOrderEliminateTarget v pivot target) a := by
  by_cases hv : v ∈ target.coefficients
  · simpa [eliminateTarget, sourceOrderEliminateTarget, hv] using
      xorRow_comm_holds bound pivot target a
  · simp [eliminateTarget, sourceOrderEliminateTarget, hv]

/-- The two row outputs can differ syntactically even though their
    affine equations are identical. This prevents an unsound exact-list
    refinement assumption in the driver-to-DAG proof. -/
example :
    xorRow ⟨[1], false⟩ ⟨[2], false⟩ ≠
      xorRow ⟨[2], false⟩ ⟨[1], false⟩ := by decide

/-- A complete driver pass rendered in the target-first operand order
    required by the indexed source emitter. -/
def sourceOrderEliminatePass (v : Nat) (pivot : Row)
    (targets : List Row) : List Row :=
  targets.map (sourceOrderEliminateTarget v pivot)

/-- Every target in a full Gaussian elimination pass retains exactly the
    same solution semantics after changing operand order for the emitter. -/
theorem eliminatePass_source_order_models
    (bound v : Nat) (pivot : Row)
    (targets : List Row) (a : Nat → Bool) :
    (∀ row ∈ eliminatePass v pivot targets, RowHolds bound row a) ↔
    (∀ row ∈ sourceOrderEliminatePass v pivot targets,
      RowHolds bound row a) := by
  constructor
  · intro hall row hmem
    obtain ⟨original, hsource, heq⟩ := List.mem_map.mp
      (show row ∈ targets.map (sourceOrderEliminateTarget v pivot)
        from hmem)
    subst row
    apply (eliminateTarget_source_order_equiv bound v pivot original a).mp
    exact hall (eliminateTarget v pivot original)
      (List.mem_map.mpr ⟨original, hsource, rfl⟩)
  · intro hall row hmem
    obtain ⟨original, hsource, heq⟩ := List.mem_map.mp
      (show row ∈ targets.map (eliminateTarget v pivot) from hmem)
    subst row
    apply (eliminateTarget_source_order_equiv bound v pivot original a).mpr
    exact hall (sourceOrderEliminateTarget v pivot original)
      (List.mem_map.mpr ⟨original, hsource, rfl⟩)

#print axioms Witnora.G5DriverXorOrderBridge.eliminatePass_source_order_models

#print axioms Witnora.G5DriverXorOrderBridge.xorRow_rhs_comm
#print axioms Witnora.G5DriverXorOrderBridge.xorRow_support_comm
#print axioms Witnora.G5DriverXorOrderBridge.xorRow_comm_holds
#print axioms Witnora.G5DriverXorOrderBridge.eliminateTarget_source_order_equiv

end Witnora.G5DriverXorOrderBridge
