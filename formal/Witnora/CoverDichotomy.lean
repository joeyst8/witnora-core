import Lean
import Witnora.GraphCoverColoring
import Witnora.ColorMerge

/-!
# A structural cover dichotomy

For any graph with a vertex cover injectively labeled by n+2 colors:
either the graph can be colored with n+2 colors, or the cover itself
extends by one outside vertex to form a larger clique.

This is not yet the chromatic-number / vertex-cover-number inequality:
it needs finite cardinality and minimum/maximum definitions.
-/

namespace Witnora.CoverDichotomy

open Witnora.ColorMerge
open Witnora.GraphCoverColoring

def optionToFin (n : Nat) : Option (Fin (n + 1)) → Fin (n + 2)
  | none => ⟨0, by omega⟩
  | some i => ⟨i.val + 1, by have hi := i.isLt; omega⟩

theorem optionToFin_injective (n : Nat)
    (a b : Option (Fin (n + 1)))
    (h : optionToFin n a = optionToFin n b) : a = b := by
  cases a with
  | none =>
    cases b with
    | none => rfl
    | some j =>
      have hv := congrArg Fin.val h
      simp [optionToFin] at hv
  | some i =>
    cases b with
    | none =>
      have hv := congrArg Fin.val h
      simp [optionToFin] at hv
      omega
    | some j =>
      have hv := congrArg Fin.val h
      have hij : i = j := by
        apply Fin.ext
        simp [optionToFin] at hv
      exact congrArg Option.some hij

theorem cover_color_or_larger_clique
    {V : Type} (Adj : V → V → Prop) (S : V → Prop)
    (n : Nat) (label : V → Fin (n + 2))
    (hSym : ∀ u v, Adj u v → Adj v u)
    (hNoLoops : ∀ u, ¬ Adj u u)
    (hIndependent : ∀ u v, ¬ S u → ¬ S v → ¬ Adj u v)
    (hInjectOnCover :
      ∀ u v, S u → S v → label u = label v → u = v) :
    (∃ paint : V → Fin (n + 2),
      ∀ u v, Adj u v → paint u ≠ paint v) ∨
    (∃ outside : V, ¬ S outside ∧
      ∀ u v, (S u ∨ u = outside) → (S v ∨ v = outside) →
        u ≠ v → Adj u v) := by
  classical
  by_cases hCoverClique :
      ∀ u v, S u → S v → u ≠ v → Adj u v
  · exact clique_cover_color_or_extend Adj S (n + 2) label
      hSym hNoLoops hIndependent hInjectOnCover hCoverClique
  · have hPair :
        ∃ x y, S x ∧ S y ∧ x ≠ y ∧ ¬ Adj x y := by
      by_cases hExists :
          ∃ x y, S x ∧ S y ∧ x ≠ y ∧ ¬ Adj x y
      · exact hExists
      · have hAll : ∀ u v, S u → S v → u ≠ v → Adj u v := by
          intro u v hu hv hne
          by_cases hedge : Adj u v
          · exact hedge
          · exact False.elim (hExists ⟨u, v, hu, hv, hne, hedge⟩)
        exact False.elim (hCoverClique hAll)
    obtain ⟨x, y, hx, hy, hxy, hNoPairEdge⟩ := hPair
    obtain ⟨paint, hProper⟩ :=
      colorable_after_merging_arbitrary_nonedge Adj S n label x y
        hSym hNoLoops hIndependent hInjectOnCover
        hx hy hxy hNoPairEdge
    left
    refine ⟨fun u => optionToFin n (paint u), ?_⟩
    intro u v huv heq
    exact hProper u v huv (optionToFin_injective n (paint u) (paint v) heq)

end Witnora.CoverDichotomy
