import Lean
import Witnora.ChromaticMinimum
import Witnora.ChromaticNumericalBridge

/-!
# Finite chromatic maximum bridge

This instantiates the certificate-based chromatic theorem with a
concretely defined least chromatic number for vertices Fin N. The
clique-number maximum property is still an explicit hypothesis.
-/

namespace Witnora.FiniteChromaticBound

open Witnora.ChromaticMinimum
open Witnora.ChromaticNumericalBridge

theorem finite_chromatic_le_max_cover_clique
    (N n : Nat) (Adj : Fin N → Fin N → Prop)
    (S : Fin N → Prop) (label : Fin N → Fin (n + 2))
    (omega : Nat)
    (hSym : ∀ u v, Adj u v → Adj v u)
    (hNoLoops : ∀ u, ¬ Adj u u)
    (hIndependent : ∀ u v, ¬ S u → ¬ S v → ¬ Adj u v)
    (hInjectOnCover :
      ∀ u v, S u → S v → label u = label v → u = v)
    (hSurjectOnCover :
      ∀ i : Fin (n + 2), ∃ u, S u ∧ label u = i)
    (hCliqueLower :
      ∀ k : Nat, ∀ vertices : Option (Fin k) → Fin N,
        (∀ a b, vertices a = vertices b → a = b) →
        (∀ a b, a ≠ b → Adj (vertices a) (vertices b)) →
        k + 1 ≤ omega) :
    chromaticNumber Adj hNoLoops ≤ max (n + 2) omega := by
  apply chromatic_le_max_cover_clique_from_certificates
    Adj S n label (chromaticNumber Adj hNoLoops) omega
    hSym hNoLoops hIndependent hInjectOnCover hSurjectOnCover
  · intro k hk
    exact chromaticNumber_minimal Adj hNoLoops k hk
  · exact hCliqueLower

end Witnora.FiniteChromaticBound
