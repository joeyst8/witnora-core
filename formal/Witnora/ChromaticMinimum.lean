import Lean
import Init.Omega

/-!
# Concrete chromatic number for finite loopless graphs

The chromatic number is defined as the least natural palette size
admitting a proper coloring of Fin N. No extremal-number hypothesis
is supplied as an axiom.
-/

namespace Witnora.ChromaticMinimum

def Colorable {N : Nat} (Adj : Fin N → Fin N → Prop)
    (k : Nat) : Prop :=
  ∃ paint : Fin N → Fin k,
    ∀ u v, Adj u v → paint u ≠ paint v

theorem least_nat_witness (P : Nat → Prop) (h : ∃ k, P k) :
    ∃ k, P k ∧ ∀ m, P m → k ≤ m := by
  have hInd : ∀ w, P w → ∃ k, P k ∧ ∀ m, P m → k ≤ m := by
    intro w
    induction w using Nat.strong_induction_on with
    | h w ih =>
      intro hw
      by_cases hSmaller : ∃ m, m < w ∧ P m
      · obtain ⟨m, hmw, hPm⟩ := hSmaller
        exact ih m hmw hPm
      · refine ⟨w, hw, ?_⟩
        intro m hm
        by_cases hmw : m < w
        · exact False.elim (hSmaller ⟨m, hmw, hm⟩)
        · omega
  obtain ⟨w, hw⟩ := h
  exact hInd w hw

theorem finite_colorable {N : Nat}
    (Adj : Fin N → Fin N → Prop)
    (hNoLoops : ∀ u, ¬ Adj u u) :
    ∃ k, Colorable Adj k := by
  refine ⟨N, ?_⟩
  refine ⟨fun u => u, ?_⟩
  intro u v huv heq
  subst v
  exact hNoLoops u huv

noncomputable def chromaticNumber {N : Nat}
    (Adj : Fin N → Fin N → Prop)
    (hNoLoops : ∀ u, ¬ Adj u u) : Nat :=
  Classical.choose
    (least_nat_witness (Colorable Adj) (finite_colorable Adj hNoLoops))

theorem chromaticNumber_minimal {N : Nat}
    (Adj : Fin N → Fin N → Prop)
    (hNoLoops : ∀ u, ¬ Adj u u)
    (k : Nat) (hColor : Colorable Adj k) :
    chromaticNumber Adj hNoLoops ≤ k := by
  exact (Classical.choose_spec
    (least_nat_witness (Colorable Adj)
      (finite_colorable Adj hNoLoops))).2 k hColor

theorem chromaticNumber_colorable {N : Nat}
    (Adj : Fin N → Fin N → Prop)
    (hNoLoops : ∀ u, ¬ Adj u u) :
    Colorable Adj (chromaticNumber Adj hNoLoops) := by
  exact (Classical.choose_spec
    (least_nat_witness (Colorable Adj)
      (finite_colorable Adj hNoLoops))).1

end Witnora.ChromaticMinimum
