import Lean
import Witnora.CoverDichotomy

/-!
# Counting bridge for the cover dichotomy

If the cover labels are not merely distinct but exhaust Fin k, the
clique-extension case contains k+1 explicitly indexed vertices.
-/

namespace Witnora.FiniteCliqueBridge

open Witnora.CoverDichotomy

theorem cover_color_or_indexed_clique
    {V : Type} (Adj : V → V → Prop) (S : V → Prop)
    (n : Nat) (label : V → Fin (n + 2))
    (hSym : ∀ u v, Adj u v → Adj v u)
    (hNoLoops : ∀ u, ¬ Adj u u)
    (hIndependent : ∀ u v, ¬ S u → ¬ S v → ¬ Adj u v)
    (hInjectOnCover :
      ∀ u v, S u → S v → label u = label v → u = v)
    (hSurjectOnCover :
      ∀ i : Fin (n + 2), ∃ u, S u ∧ label u = i) :
    (∃ paint : V → Fin (n + 2),
      ∀ u v, Adj u v → paint u ≠ paint v) ∨
    (∃ vertices : Option (Fin (n + 2)) → V,
      (∀ a b, vertices a = vertices b → a = b) ∧
      (∀ a b, a ≠ b → Adj (vertices a) (vertices b))) := by
  classical
  rcases cover_color_or_larger_clique Adj S n label
      hSym hNoLoops hIndependent hInjectOnCover with
    hColor | hExt
  · exact Or.inl hColor
  · right
    obtain ⟨outside, hOutside, hClique⟩ := hExt
    let rep : Fin (n + 2) → V :=
      fun i => Classical.choose (hSurjectOnCover i)
    have hRep : ∀ i, S (rep i) ∧ label (rep i) = i := by
      intro i
      exact Classical.choose_spec (hSurjectOnCover i)
    let vertices : Option (Fin (n + 2)) → V
      | none => outside
      | some i => rep i
    have hInject : ∀ a b, vertices a = vertices b → a = b := by
      intro a b hEq
      cases a with
      | none =>
        cases b with
        | none => rfl
        | some j =>
          have hOutsideEq : outside = rep j := hEq
          have hInside : S outside := by
            rw [hOutsideEq]
            exact (hRep j).1
          exact False.elim (hOutside hInside)
      | some i =>
        cases b with
        | none =>
          have hOutsideEq : rep i = outside := hEq
          have hInside : S outside := by
            rw [← hOutsideEq]
            exact (hRep i).1
          exact False.elim (hOutside hInside)
        | some j =>
          have hRepEq : rep i = rep j := hEq
          have hij : i = j := by
            calc
              i = label (rep i) := (hRep i).2.symm
              _ = label (rep j) := congrArg label hRepEq
              _ = j := (hRep j).2
          exact congrArg Option.some hij
    refine ⟨vertices, hInject, ?_⟩
    intro a b hne
    have ha : S (vertices a) ∨ vertices a = outside := by
      cases a with
      | none => exact Or.inr rfl
      | some i => exact Or.inl (hRep i).1
    have hb : S (vertices b) ∨ vertices b = outside := by
      cases b with
      | none => exact Or.inr rfl
      | some i => exact Or.inl (hRep i).1
    have hDistinct : vertices a ≠ vertices b := by
      intro hEq
      exact hne (hInject a b hEq)
    exact hClique (vertices a) (vertices b) ha hb hDistinct

end Witnora.FiniteCliqueBridge
