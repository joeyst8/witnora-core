import Lean
import Init.Omega
import Witnora.GraphMaxEquality

/-!
# Explicit optimal-coloring certificate for finite simple graphs

A proper k-coloring is an upper-bound witness. An explicitly injected
k-vertex clique is a matching lower-bound witness. Together they certify
that the concretely defined chromatic number equals k.

This is a reusable verifier theorem, not a claim of graph-theoretic novelty.
No sorry, axiom, or unsafe declarations are introduced.
-/

namespace Witnora.ColoringOptimalityCertificate

open Witnora.ChromaticMinimum
open Witnora.CliqueMaximum
open Witnora.ConcreteGraphBound
open Witnora.GraphMaxEquality

/-- Every explicit proper coloring certifies an upper bound on chi. -/
theorem explicit_coloring_upper_bound
    (N k : Nat) (Adj : Fin N → Fin N → Prop)
    (hNoLoops : ∀ u, ¬ Adj u u)
    (paint : Fin N → Fin k)
    (hProper : ∀ u v, Adj u v → paint u ≠ paint v) :
    chromaticNumber Adj hNoLoops ≤ k := by
  exact chromaticNumber_minimal Adj hNoLoops k ⟨paint, hProper⟩

/-- A concretely listed, injective clique certifies a lower bound on chi. -/
theorem explicit_clique_lower_bound
    (N k : Nat) (Adj : Fin N → Fin N → Prop)
    (hNoLoops : ∀ u, ¬ Adj u u)
    (vertices : Option (Fin k) → Fin N)
    (hInject : ∀ a b, vertices a = vertices b → a = b)
    (hClique : ∀ a b, a ≠ b → Adj (vertices a) (vertices b)) :
    k + 1 ≤ chromaticNumber Adj hNoLoops := by
  have hLower : k + 1 ≤ finiteCliqueNumber N Adj :=
    cliqueNumber_bounds_every_clique Adj
      (finite_cliques_bounded N Adj) k vertices hInject hClique
  have hCliqueLe : finiteCliqueNumber N Adj ≤
      chromaticNumber Adj hNoLoops :=
    clique_number_le_chromatic_number N Adj hNoLoops
  omega

/-- Matching explicit upper/lower witnesses certify exact optimality. -/
theorem exact_chromatic_of_matching_witnesses
    (N k : Nat) (Adj : Fin N → Fin N → Prop)
    (hNoLoops : ∀ u, ¬ Adj u u)
    (paint : Fin N → Fin (k + 1))
    (hProper : ∀ u v, Adj u v → paint u ≠ paint v)
    (vertices : Option (Fin k) → Fin N)
    (hInject : ∀ a b, vertices a = vertices b → a = b)
    (hClique : ∀ a b, a ≠ b → Adj (vertices a) (vertices b)) :
    chromaticNumber Adj hNoLoops = k + 1 := by
  have hUpper : chromaticNumber Adj hNoLoops ≤ k + 1 :=
    explicit_coloring_upper_bound N (k + 1) Adj hNoLoops paint hProper
  have hLower : k + 1 ≤ chromaticNumber Adj hNoLoops :=
    explicit_clique_lower_bound N k Adj hNoLoops vertices hInject hClique
  omega

/-- The empty-palette case, where no indexed nonempty clique is needed. -/
theorem exact_zero_of_empty_palette
    (N : Nat) (Adj : Fin N → Fin N → Prop)
    (hNoLoops : ∀ u, ¬ Adj u u)
    (paint : Fin N → Fin 0)
    (hProper : ∀ u v, Adj u v → paint u ≠ paint v) :
    chromaticNumber Adj hNoLoops = 0 := by
  have hUpper : chromaticNumber Adj hNoLoops ≤ 0 :=
    explicit_coloring_upper_bound N 0 Adj hNoLoops paint hProper
  omega

end Witnora.ColoringOptimalityCertificate

#print axioms Witnora.ColoringOptimalityCertificate.explicit_coloring_upper_bound
#print axioms Witnora.ColoringOptimalityCertificate.explicit_clique_lower_bound
#print axioms Witnora.ColoringOptimalityCertificate.exact_chromatic_of_matching_witnesses
#print axioms Witnora.ColoringOptimalityCertificate.exact_zero_of_empty_palette
