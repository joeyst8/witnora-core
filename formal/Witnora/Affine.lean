import Init

/-!
# GF(2) affine row-operation soundness

An affine equation is modeled as a Boolean-valued left-hand-side function
and a Boolean right-hand side. This model supports arbitrary assignment
domains and does not assume that Witnora's Python extraction or sparse-row
representation realizes these functions correctly.

These theorems justify the algebra used by the G5 Gaussian elimination
steps: swapping equations preserves satisfaction; replacing one equation
with its XOR against another preserves the entire two-equation system;
and a constant contradiction cannot be satisfied.
-/

namespace Witnora.Affine

structure Equation (Assignment : Type) where
  lhs : Assignment → Bool
  rhs : Bool

def Holds {Assignment : Type} (e : Equation Assignment)
    (a : Assignment) : Prop :=
  e.lhs a = e.rhs

def xorEquation {Assignment : Type}
    (e₁ e₂ : Equation Assignment) : Equation Assignment where
  lhs := fun a => Bool.xor (e₁.lhs a) (e₂.lhs a)
  rhs := Bool.xor e₁.rhs e₂.rhs

/-- XORing two equations is valid whenever both original equations hold. -/
theorem xorEquation_sound {Assignment : Type}
    (e₁ e₂ : Equation Assignment) (a : Assignment)
    (h₁ : Holds e₁ a) (h₂ : Holds e₂ a) :
    Holds (xorEquation e₁ e₂) a := by
  simp only [Holds, xorEquation] at *
  rw [h₁, h₂]

/-- An ADD_ROW_XOR operation is reversible because XOR is its own inverse.
Consequently it preserves *exactly* the solution set of the two rows. -/
theorem addRowXor_iff {Assignment : Type}
    (e₁ e₂ : Equation Assignment) (a : Assignment) :
    (Holds e₁ a ∧ Holds e₂ a) ↔
      (Holds e₁ a ∧ Holds (xorEquation e₁ e₂) a) := by
  constructor
  · intro h
    exact ⟨h.1, xorEquation_sound e₁ e₂ a h.1 h.2⟩
  · intro h
    refine ⟨h.1, ?_⟩
    unfold Holds xorEquation at *
    rcases h with ⟨h₁, hx⟩
    cases hleft : e₁.lhs a <;>
      cases hright : e₁.rhs <;>
      cases hother : e₂.lhs a <;>
      cases htarget : e₂.rhs <;>
      simp_all [Bool.xor]

/-- Swapping two rows has no effect on their joint solution set. -/
theorem swapRows_iff {Assignment : Type}
    (e₁ e₂ : Equation Assignment) (a : Assignment) :
    (Holds e₁ a ∧ Holds e₂ a) ↔
      (Holds e₂ a ∧ Holds e₁ a) := by
  exact and_comm

/-- The impossible equation 0 = 1 rejects every assignment. -/
def contradictionRow (Assignment : Type) : Equation Assignment where
  lhs := fun _ => false
  rhs := true

theorem contradictionRow_unsat {Assignment : Type} (a : Assignment) :
    ¬ Holds (contradictionRow Assignment) a := by
  decide

#print axioms Witnora.Affine.xorEquation_sound
#print axioms Witnora.Affine.addRowXor_iff
#print axioms Witnora.Affine.swapRows_iff
#print axioms Witnora.Affine.contradictionRow_unsat

end Witnora.Affine
