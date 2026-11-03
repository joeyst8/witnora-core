import Witnora.ClauseViolationParity

/-!
# GF(2) parity-row XOR preserves every violation-vector solution

A mask is a Boolean list of the same length as the violation vector.
The concrete rowParity operation is linear in the mask. Hence an
elementary replacement row_a := row_a XOR row_b, with row_b retained,
preserves the exact solution set for EVERY vector.

The Python sparse-basis checker validates finite XOR-reconstruction
witnesses. This Lean theorem validates the universal row operation;
it does not itself prove that every Python witness is correctly decoded.
-/

namespace Witnora.GF2RowParity

open Witnora.ClauseViolationParity

def xorMask : List Bool → List Bool → List Bool
  | x :: xs, y :: ys => (x != y) :: xorMask xs ys
  | _, _ => []

/-- Inner parity of a pointwise XOR mask equals XOR of two inner parities. -/
theorem rowParity_xorMask (v a b : List Bool)
    (ha : v.length = a.length)
    (hb : v.length = b.length) :
    rowParity v (xorMask a b) =
      (rowParity v a != rowParity v b) := by
  induction v generalizing a b with
  | nil =>
      cases a with
      | nil =>
          cases b with
          | nil => rfl
          | cons _ _ => simp at hb
      | cons _ _ => simp at ha
  | cons bit rest ih =>
      cases a with
      | nil => simp at ha
      | cons x xs =>
          cases b with
          | nil => simp at hb
          | cons y ys =>
              have hxs : rest.length = xs.length := by
                simpa using ha
              have hys : rest.length = ys.length := by
                simpa using hb
              simp only [xorMask, rowParity]
              rw [ih xs ys hxs hys]
              cases bit <;> cases x <;> cases y <;>
                cases (rowParity rest xs) <;>
                cases (rowParity rest ys) <;> decide

/-- Replacing one equation with its XOR against a retained equation is
    reversible and preserves all solution assignments. -/
theorem rowReplacement_equiv (v a b : List Bool)
    (ha : v.length = a.length)
    (hb : v.length = b.length) :
    (rowParity v a = false ∧ rowParity v b = false) ↔
      (rowParity v (xorMask a b) = false ∧
       rowParity v b = false) := by
  rw [rowParity_xorMask v a b ha hb]
  cases hfirst : rowParity v a <;>
    cases hsecond : rowParity v b <;>
    simp [hfirst, hsecond]

example : xorMask [true, false, true] [true, true, false] =
    [false, true, true] := by decide

#print axioms Witnora.GF2RowParity.rowParity_xorMask
#print axioms Witnora.GF2RowParity.rowReplacement_equiv

end Witnora.GF2RowParity
