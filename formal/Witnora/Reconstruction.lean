import Witnora.Affine

/-!
# Unbounded abstract G5 proof reconstruction

This theorem does not enumerate assignments. It proves that any sequence of
locally justified row swaps and XOR additions preserves every solution, and
that a final 0=1 row proves UNSAT. It assumes an exact CNF-to-equation
extraction relation. A separate implementation-refinement proof is required
to turn Python's indexed sparse traces into these `Step` constructors.
-/

namespace Witnora.Reconstruction

open Witnora.Affine

variable {A : Type}

def Satisfies (rows : List (Equation A)) (a : A) : Prop :=
  ∀ row, row ∈ rows → Holds row a

theorem sat_cons (head : Equation A) (tail : List (Equation A)) (a : A) :
    Satisfies (head :: tail) a ↔ Holds head a ∧ Satisfies tail a := by
  constructor
  · intro h
    constructor
    · exact h head (by simp)
    · intro e he
      exact h e (by simp [he])
  · intro h e he
    rcases List.mem_cons.mp he with heq | htail
    · simpa [heq] using h.1
    · exact h.2 e htail

/-- Local transformations. A general indexed Python operation can be
decomposed into adjacent swaps and context lifts when indices are valid. -/
inductive Step : List (Equation A) → List (Equation A) → Prop where
  | swap (x y : Equation A) (rest : List (Equation A)) :
      Step (x :: y :: rest) (y :: x :: rest)
  | addXor (x y : Equation A) (rest : List (Equation A)) :
      Step (x :: y :: rest) (x :: xorEquation x y :: rest)
  | keep (x : Equation A) {before after : List (Equation A)}
      (h : Step before after) :
      Step (x :: before) (x :: after)

theorem step_sound {before after : List (Equation A)}
    (h : Step before after) (a : A) :
    Satisfies before a ↔ Satisfies after a := by
  induction h with
  | swap x y rest =>
      simp only [sat_cons]
      exact ⟨fun h => ⟨h.2.1, h.1, h.2.2⟩,
             fun h => ⟨h.2.1, h.1, h.2.2⟩⟩
  | addXor x y rest =>
      simp only [sat_cons]
      constructor
      · intro h
        exact ⟨h.1, (addRowXor_iff x y a).mp ⟨h.1, h.2.1⟩ |>.2, h.2.2⟩
      · intro h
        exact ⟨h.1, (addRowXor_iff x y a).mpr ⟨h.1, h.2.1⟩ |>.2, h.2.2⟩
  | keep x h ih =>
      simpa only [sat_cons] using and_congr_right (fun _ => ih)

/-- Lift a verified operation across an arbitrary list front. This allows
adjacent indexed operations at any position, not just row zero. -/
theorem step_under_front (front : List (Equation A))
    {before after : List (Equation A)} (h : Step before after) :
    Step (front ++ before) (front ++ after) := by
  induction front with
  | nil => simpa using h
  | cons x xs ih =>
      simpa using Step.keep x ih

theorem adjacent_swap_sound (front suffix : List (Equation A))
    (x y : Equation A) (assignment : A) :
    Satisfies (front ++ x :: y :: suffix) assignment ↔
      Satisfies (front ++ y :: x :: suffix) assignment := by
  exact step_sound (step_under_front front (Step.swap x y suffix)) assignment

theorem adjacent_xor_sound (front suffix : List (Equation A))
    (x y : Equation A) (assignment : A) :
    Satisfies (front ++ x :: y :: suffix) assignment ↔
      Satisfies (front ++ x :: xorEquation x y :: suffix) assignment := by
  exact step_sound (step_under_front front (Step.addXor x y suffix)) assignment

/-- A finite sequence of certified local steps. -/
inductive Steps : List (Equation A) → List (Equation A) → Prop where
  | refl (rows : List (Equation A)) : Steps rows rows
  | next {r₁ r₂ r₃ : List (Equation A)}
      (h : Step r₁ r₂) (rest : Steps r₂ r₃) : Steps r₁ r₃

theorem steps_sound {before after : List (Equation A)}
    (h : Steps before after) (a : A) :
    Satisfies before a ↔ Satisfies after a := by
  induction h with
  | refl _ => rfl
  | next h rest ih => exact (step_sound h a).trans ih

def ExactExtraction (cnfTrue : A → Prop) (rows : List (Equation A)) : Prop :=
  ∀ a, cnfTrue a ↔ Satisfies rows a

/-- If the extracted equations are equivalent to the CNF and the trace
ends with a contradiction, the original CNF is UNSAT. No search over all
assignments is performed. -/
theorem reconstructed_unsat
    (cnfTrue : A → Prop)
    (initial finalRows : List (Equation A))
    (hexact : ExactExtraction cnfTrue initial)
    (htrace : Steps initial finalRows)
    (hcontradiction : contradictionRow A ∈ finalRows) :
    ¬ ∃ a, cnfTrue a := by
  rintro ⟨a, hmodel⟩
  have hin : Satisfies initial a := (hexact a).mp hmodel
  have hout : Satisfies finalRows a := (steps_sound htrace a).mp hin
  exact contradictionRow_unsat a (hout (contradictionRow A) hcontradiction)

#print axioms Witnora.Reconstruction.reconstructed_unsat
#print axioms Witnora.Reconstruction.steps_sound
#print axioms Witnora.Reconstruction.adjacent_swap_sound
#print axioms Witnora.Reconstruction.adjacent_xor_sound

end Witnora.Reconstruction
