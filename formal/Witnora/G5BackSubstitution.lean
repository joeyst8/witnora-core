import Witnora.G5ResidualNormalForm

/-!
# Back-substitution foundation: toggling a pivot variable

A sparse parity equation containing v and measured with a bound above v
changes truth value when only a(v) is flipped. Every equation not
containing v is unaffected. These universal lemmas are the foundation
for constructing models by reverse traversal of Gaussian pivot rows.
-/

namespace Witnora.G5BackSubstitution

open Witnora.G5Trace
open Witnora.G5Certificate
open Witnora.SparseParity

/-- A single-bit assignment modification. -/
def flipAt (v : Nat) (a : Nat → Bool) : Nat → Bool :=
  fun w => if w = v then !a w else a w

theorem flipAt_other (v w : Nat) (a : Nat → Bool)
    (h : w ≠ v) : flipAt v a w = a w := by
  simp [flipAt, h]

theorem flipAt_self (v : Nat) (a : Nat → Bool) :
    flipAt v a v = !a v := by
  simp [flipAt]

/-- Finite XOR folding respects pointwise equality below its bound. -/
theorem xorFold_ext (n : Nat) (f g : Nat → Bool)
    (h : ∀ w, w < n → f w = g w) :
    xorFold n f = xorFold n g := by
  induction n with
  | zero => rfl
  | succ k ih =>
      have hp : ∀ w, w < k → f w = g w := by
        intro w hw
        exact h w (Nat.lt_trans hw (Nat.lt_succ_self k))
      rw [xorFold, xorFold, ih hp, h k (Nat.lt_succ_self k)]

/-- Flipping one indexed input below the bound complements the XOR fold. -/
theorem xorFold_flip_index
    (n v : Nat) (f : Nat → Bool) (hv : v < n) :
    xorFold n (fun w => if w = v then !f w else f w) =
      !(xorFold n f) := by
  induction n with
  | zero =>
      exact False.elim (Nat.not_lt_zero v hv)
  | succ k ih =>
      by_cases he : v = k
      · subst v
        have hprefix : xorFold k
            (fun w => if w = k then !f w else f w) =
            xorFold k f := by
          apply xorFold_ext k
          intro w hw
          have hn : w ≠ k := Nat.ne_of_lt hw
          simp [hn]
        simp only [xorFold, hprefix, if_pos rfl]
        cases hp : xorFold k f <;> cases hb : f k <;> decide
      · have hlt : v < k := by
          exact (Nat.lt_succ_iff_lt_or_eq.mp hv).resolve_right he
        have hk : k ≠ v := Ne.symm he
        simp only [xorFold, if_neg hk]
        rw [ih hlt]
        cases hp : xorFold k f <;> cases hb : f k <;> decide

/-- A sparse equation is insensitive to changes outside its support. -/
theorem sparseParity_congr_on_support
    (bound : Nat) (coeff : List Nat) (a b : Nat → Bool)
    (hag : ∀ v ∈ coeff, a v = b v) :
    sparseParity bound coeff a = sparseParity bound coeff b := by
  unfold sparseParity
  apply xorFold_ext bound
  intro w _
  by_cases hw : w ∈ coeff
  · simp [hw, hag w hw]
  · simp [hw]

/-- Flipping a present pivot variable below the sparse evaluation bound
    toggles the entire row parity. -/
theorem sparseParity_flip_present
    (bound v : Nat) (coeff : List Nat) (a : Nat → Bool)
    (hv : v < bound) (hmem : v ∈ coeff) :
    sparseParity bound coeff (flipAt v a) =
      !(sparseParity bound coeff a) := by
  unfold sparseParity
  have hfun : (fun w => (decide (w ∈ coeff)) && flipAt v a w) =
      (fun w => if w = v then !((decide (w ∈ coeff)) && a w)
        else (decide (w ∈ coeff)) && a w) := by
    funext w
    by_cases he : w = v
    · subst w
      simp [flipAt, hmem]
    · simp [flipAt, he]
  rw [hfun]
  exact xorFold_flip_index bound v
    (fun w => (decide (w ∈ coeff)) && a w) hv

/-- A row with an in-range pivot variable can always be made true by
    assigning that one variable appropriately. -/
theorem solve_one_pivot
    (bound v : Nat) (row : Row) (a : Nat → Bool)
    (hv : v < bound) (hmem : v ∈ row.coefficients) :
    ∃ b : Nat → Bool,
      (∀ w, w ≠ v → b w = a w) ∧ RowHolds bound row b := by
  by_cases h : RowHolds bound row a
  · exact ⟨a, by intros; rfl, h⟩
  · refine ⟨flipAt v a, ?_, ?_⟩
    · intro w hw
      exact flipAt_other v w a hw
    · unfold RowHolds at h ⊢
      rw [sparseParity_flip_present bound v row.coefficients a hv hmem]
      cases hp : sparseParity bound row.coefficients a <;>
        cases hr : row.rhs <;> simp_all

#print axioms Witnora.G5BackSubstitution.xorFold_flip_index
#print axioms Witnora.G5BackSubstitution.sparseParity_flip_present
#print axioms Witnora.G5BackSubstitution.solve_one_pivot

end Witnora.G5BackSubstitution
