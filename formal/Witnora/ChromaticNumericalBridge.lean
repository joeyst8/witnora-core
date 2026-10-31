import Lean
import Witnora.FiniteCliqueBridge

/-!
# Numeric bridge for the chromatic maximum inequality

The proof below derives chi <= max coverSize omega from actual, verified
finite graph colorings and indexed cliques. It explicitly assumes that
chi and omega respect all such certificates (the extremal-number
interfaces). Concrete minimum/maximum definitions are the remaining task.
-/

namespace Witnora.ChromaticNumericalBridge

open Witnora.FiniteCliqueBridge
open Witnora.GraphCoverColoring
open Witnora.CoverDichotomy

theorem chromatic_le_max_cover_clique_from_certificates
    {V : Type} (Adj : V → V → Prop) (S : V → Prop)
    (n : Nat) (label : V → Fin (n + 2))
    (chi omega : Nat)
    (hSym : ∀ u v, Adj u v → Adj v u)
    (hNoLoops : ∀ u, ¬ Adj u u)
    (hIndependent : ∀ u v, ¬ S u → ¬ S v → ¬ Adj u v)
    (hInjectOnCover :
      ∀ u v, S u → S v → label u = label v → u = v)
    (hSurjectOnCover :
      ∀ i : Fin (n + 2), ∃ u, S u ∧ label u = i)
    (hChromaticUpper :
      ∀ k : Nat, (∃ paint : V → Fin k,
        ∀ u v, Adj u v → paint u ≠ paint v) → chi ≤ k)
    (hCliqueLower :
      ∀ k : Nat, ∀ vertices : Option (Fin k) → V,
        (∀ a b, vertices a = vertices b → a = b) →
        (∀ a b, a ≠ b → Adj (vertices a) (vertices b)) →
        k + 1 ≤ omega) :
    chi ≤ max (n + 2) omega := by
  obtain ⟨paintExtra, hProperExtra⟩ :=
    colorable_with_cover_plus_one Adj S (n + 2) label
      hNoLoops hIndependent hInjectOnCover
  have hExtra : chi ≤ (n + 2) + 1 := by
    apply hChromaticUpper ((n + 2) + 1)
    refine ⟨fun u => optionToFin (n + 1) (paintExtra u), ?_⟩
    intro u v huv heq
    exact hProperExtra u v huv
      (optionToFin_injective (n + 1) (paintExtra u) (paintExtra v) heq)
  rcases cover_color_or_indexed_clique Adj S n label
      hSym hNoLoops hIndependent hInjectOnCover hSurjectOnCover with
    ⟨paint, hProper⟩ | ⟨vertices, hInject, hClique⟩
  · have hSmall : chi ≤ n + 2 :=
      hChromaticUpper (n + 2) ⟨paint, hProper⟩
    exact Nat.le_trans hSmall (Nat.le_max_left (n + 2) omega)
  · have hLarge : (n + 2) + 1 ≤ omega :=
      hCliqueLower (n + 2) vertices hInject hClique
    have hChiOmega : chi ≤ omega := Nat.le_trans hExtra hLarge
    exact Nat.le_trans hChiOmega (Nat.le_max_right (n + 2) omega)

end Witnora.ChromaticNumericalBridge
