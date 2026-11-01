import Witnora.G5TerminatingPivot

/-!
# G5 residual normal form: eliminated variables stay eliminated

Establishes that the sparse XOR elimination driver cannot reintroduce a
variable absent from its input rows. This is the induction invariant needed
to prove all scheduled variables are absent from the final residual rows.

Full UNSAT-to-contradiction completeness additionally requires model
construction (back-substitution) when all residual rows are consistent.
-/

namespace Witnora.G5ResidualNormalForm

open Witnora.G5Trace
open Witnora.G5TerminatingPivot

def AbsentFrom (v : Nat) (rows : List Row) : Prop :=
  ∀ row ∈ rows, v ∉ row.coefficients

/-- XOR cannot introduce a variable absent from both operands. -/
theorem xorRow_preserves_absence (w : Nat) (left right : Row)
    (hl : w ∉ left.coefficients) (hr : w ∉ right.coefficients) :
    w ∉ (xorRow left right).coefficients := by
  intro h
  have hx := (mem_xorCoefficients
    left.coefficients right.coefficients w).mp h
  rcases hx with ⟨hleft, _⟩ | ⟨hright, _⟩
  · exact hl hleft
  · exact hr hright

theorem eliminateTarget_preserves_absence
    (pivotVariable w : Nat) (pivot target : Row)
    (hp : w ∉ pivot.coefficients)
    (ht : w ∉ target.coefficients) :
    w ∉ (eliminateTarget pivotVariable pivot target).coefficients := by
  by_cases hv : pivotVariable ∈ target.coefficients
  · simpa [eliminateTarget, hv] using
      xorRow_preserves_absence w pivot target hp ht
  · simpa [eliminateTarget, hv] using ht

/-- One entire pivot pass preserves absence of any unrelated variable
    already absent from both pivot and target rows. -/
theorem eliminatePass_preserves_absence (v w : Nat)
    (pivot : Row) (targets : List Row)
    (hp : w ∉ pivot.coefficients)
    (ht : AbsentFrom w targets) :
    AbsentFrom w (eliminatePass v pivot targets) := by
  intro row hr
  obtain ⟨old, hmem, heq⟩ := List.mem_map.mp
    (show row ∈ targets.map (eliminateTarget v pivot) from hr)
  subst row
  exact eliminateTarget_preserves_absence v w pivot old hp (ht old hmem)

/-- If a pivot was extracted, the chosen row and every remaining row
    inherit any variable absence shared by the original list. -/
theorem extracted_pivot_preserves_absence (v w : Nat)
    (rows : List Row) (pivot : Row) (remaining : List Row)
    (he : extractPivot v rows = some (pivot, remaining))
    (ha : AbsentFrom w rows) :
    w ∉ pivot.coefficients ∧ AbsentFrom w remaining := by
  have hp := extractPivot_perm v rows pivot remaining he
  have hpair : AbsentFrom w (pivot :: remaining) := by
    intro row hr
    exact ha row (hp.mem_iff.mpr hr)
  constructor
  · exact hpair pivot (by simp)
  · intro row hr
    exact hpair row (by simp [hr])

/-- The complete terminating elimination driver never reintroduces an
    absent variable in either retained pivots or residual rows. -/
theorem eliminateVariables_preserves_absence
    (vars : List Nat) (rows : List Row) (w : Nat)
    (ha : AbsentFrom w rows) :
    AbsentFrom w ((eliminateVariables vars rows).1 ++
      (eliminateVariables vars rows).2) := by
  induction vars generalizing rows with
  | nil =>
      simpa [eliminateVariables] using ha
  | cons v rest ih =>
      cases he : extractPivot v rows with
      | none =>
          simpa [eliminateVariables, he] using ih rows ha
      | some result =>
          cases result with
          | mk pivot others =>
              obtain ⟨hp, ho⟩ :=
                extracted_pivot_preserves_absence v w rows pivot others he ha
              have hpass : AbsentFrom w (eliminatePass v pivot others) :=
                eliminatePass_preserves_absence v w pivot others hp ho
              have htail := ih (eliminatePass v pivot others) hpass
              cases hr : eliminateVariables rest (eliminatePass v pivot others) with
              | mk pivots residual =>
                  have hnext : AbsentFrom w (pivots ++ residual) := by
                    simpa [hr] using htail
                  intro row hmem
                  have hm : row ∈ pivot :: (pivots ++ residual) := by
                    simpa [eliminateVariables, he, hr] using hmem
                  rcases List.mem_cons.mp hm with heq | hrest
                  · subst row
                    exact hp
                  · exact hnext row hrest

#print axioms Witnora.G5ResidualNormalForm.xorRow_preserves_absence
#print axioms Witnora.G5ResidualNormalForm.eliminateVariables_preserves_absence

end Witnora.G5ResidualNormalForm
