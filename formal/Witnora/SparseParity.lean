import Witnora.G5Trace

/-!
# Sparse GF(2) row parity semantics

The finite support is represented by a List Nat, and the assignment is a
function Nat → Bool. The evaluator enumerates variable IDs below a bound;
it does *not* enumerate assignments. The theorem is uniform in that bound,
the rows, and the assignment.
-/

namespace Witnora.SparseParity

open Witnora.G5Trace

def xorFold : Nat → (Nat → Bool) → Bool
  | 0, _ => false
  | n + 1, f => Bool.xor (xorFold n f) (f n)

theorem xorFold_distrib (n : Nat) (f g : Nat → Bool) :
    xorFold n (fun v => Bool.xor (f v) (g v)) =
      Bool.xor (xorFold n f) (xorFold n g) := by
  induction n with
  | zero => rfl
  | succ n ih =>
    simp only [xorFold, ih]
    cases hf : xorFold n f <;>
      cases hg : xorFold n g <;>
      cases hfn : f n <;>
      cases hgn : g n <;>
      decide

def sparseParity (bound : Nat) (coefficients : List Nat)
    (assignment : Nat → Bool) : Bool :=
  xorFold bound (fun v => (decide (v ∈ coefficients)) && assignment v)

/-- One coefficient is present in the GF(2) sum exactly when it occurs in
one of the two coefficient supports but not the other. -/
theorem xor_member_bit (left right : List Nat) (v : Nat) :
    decide (v ∈ xorCoefficients left right) =
      Bool.xor (decide (v ∈ left)) (decide (v ∈ right)) := by
  have hm := mem_xorCoefficients left right v
  cases hl : decide (v ∈ left) <;>
    cases hr : decide (v ∈ right) <;>
    simp_all [Bool.xor]

/-- Sparse-row XOR has exactly the parity semantics of Boolean equation XOR.
This holds for every assignment and bound, without enumerating assignments. -/
theorem sparseParity_xor (bound : Nat)
    (left right : List Nat) (assignment : Nat → Bool) :
    sparseParity bound (xorCoefficients left right) assignment =
      Bool.xor (sparseParity bound left assignment)
        (sparseParity bound right assignment) := by
  unfold sparseParity
  rw [← xorFold_distrib]
  congr 1
  funext v
  rw [xor_member_bit]
  cases hl : decide (v ∈ left) <;>
    cases hr : decide (v ∈ right) <;>
    cases ha : assignment v <;>
    decide

/-- Interpret an executable sparse row as the abstract equation used by the
unbounded reconstruction theorem. -/
def interpret (bound : Nat) (row : Row) : Witnora.Affine.Equation (Nat → Bool) where
  lhs := sparseParity bound row.coefficients
  rhs := row.rhs

/-- The concrete XOR row constructor and the abstract XOR equation have the
same left- and right-hand sides for every assignment. -/
theorem xorRow_interpret (bound : Nat) (left right : Row)
    (assignment : Nat → Bool) :
    (interpret bound (xorRow left right)).lhs assignment =
      (Witnora.Affine.xorEquation (interpret bound left)
        (interpret bound right)).lhs assignment ∧
    (interpret bound (xorRow left right)).rhs =
      (Witnora.Affine.xorEquation (interpret bound left)
        (interpret bound right)).rhs := by
  constructor
  · exact sparseParity_xor bound left.coefficients right.coefficients assignment
  · rfl

#print axioms Witnora.SparseParity.xorRow_interpret

#print axioms Witnora.SparseParity.xorFold_distrib
#print axioms Witnora.SparseParity.xor_member_bit
#print axioms Witnora.SparseParity.sparseParity_xor

end Witnora.SparseParity
