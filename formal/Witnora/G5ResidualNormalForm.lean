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

/-- If no pivot is found, no input row mentions the searched variable. -/
theorem extractPivot_none_absent
    (v : Nat) (rows : List Row)
    (h : extractPivot v rows = none) :
    AbsentFrom v rows := by
  induction rows with
  | nil =>
      intro row hr
      simp at hr
  | cons head rest ih =>
      by_cases hv : v ∈ head.coefficients
      · simp [extractPivot, hv] at h
      · have htail : extractPivot v rest = none := by
          simpa [extractPivot, hv] using h
        intro row hr
        rcases List.mem_cons.mp hr with heq | hrest
        · subst row
          exact hv
        · exact ih htail row hrest

/-- Every successfully extracted pivot contains the requested variable. -/
theorem extractPivot_some_contains
    (v : Nat) (rows : List Row) (pivot : Row)
    (other : List Row)
    (h : extractPivot v rows = some (pivot, other)) :
    v ∈ pivot.coefficients := by
  induction rows generalizing pivot other with
  | nil =>
      simp [extractPivot] at h
  | cons head rest ih =>
      by_cases hv : v ∈ head.coefficients
      · simp [extractPivot, hv] at h
        exact h.1 ▸ hv
      · cases he : extractPivot v rest with
        | none =>
            simp [extractPivot, hv, he] at h
        | some result =>
            cases result with
            | mk p tail =>
                simp [extractPivot, hv, he] at h
                have hp : p = pivot := h.1
                exact hp ▸ ih p tail he

/-- The final residual system omits *every* variable in the schedule,
    regardless of whether that schedule contains all input variables. -/
theorem eliminateVariables_residual_clears_schedule
    (vars : List Nat) (rows : List Row) :
    ∀ v ∈ vars, AbsentFrom v (eliminateVariables vars rows).2 := by
  induction vars generalizing rows with
  | nil =>
      intro v hv
      simp at hv
  | cons first remaining ih =>
      intro v hv
      cases he : extractPivot first rows with
      | none =>
          have hresult : AbsentFrom v
              (eliminateVariables remaining rows).2 := by
            rcases List.mem_cons.mp hv with hfirst | hrest
            · subst v
              have hbefore := extractPivot_none_absent first rows he
              have hafter := eliminateVariables_preserves_absence
                remaining rows first hbefore
              intro row hr
              exact hafter row (List.mem_append.mpr (Or.inr hr))
            · exact ih rows v hrest
          simpa [eliminateVariables, he] using hresult
      | some result =>
          cases result with
          | mk pivot other =>
              have hp : first ∈ pivot.coefficients :=
                extractPivot_some_contains first rows pivot other he
              have hcleared : AbsentFrom first
                  (eliminatePass first pivot other) := by
                intro row hr
                exact eliminatePass_clears_variable first pivot other hp row hr
              have hresult : AbsentFrom v
                  (eliminateVariables remaining
                    (eliminatePass first pivot other)).2 := by
                rcases List.mem_cons.mp hv with hfirst | hrest
                · subst v
                  have hafter := eliminateVariables_preserves_absence
                    remaining (eliminatePass first pivot other)
                    first hcleared
                  intro row hr
                  exact hafter row (List.mem_append.mpr (Or.inr hr))
                · exact ih (eliminatePass first pivot other) v hrest
              simpa [eliminateVariables, he] using hresult

#print axioms Witnora.G5ResidualNormalForm.extractPivot_none_absent
#print axioms Witnora.G5ResidualNormalForm.extractPivot_some_contains
#print axioms Witnora.G5ResidualNormalForm.eliminateVariables_residual_clears_schedule

end Witnora.G5ResidualNormalForm
