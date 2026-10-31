import Lean
import Witnora.UniversalChromaticMax
import Witnora.ChromaticMaxConsequences
import Witnora.FinitePigeonhole

/-!
# A universally verified maximum equality for finite simple graphs

First show omega <= chi by coloring every indexed clique with distinct
colors, applying the finite pigeonhole theorem. Then combine that with
the universal chromatic maximum bound.
-/

namespace Witnora.GraphMaxEquality

open Witnora.ChromaticMinimum
open Witnora.CliqueMaximum
open Witnora.ConcreteGraphBound
open Witnora.FinitePigeonhole
open Witnora.UniversalChromaticMax

theorem clique_number_le_chromatic_number
    (N : Nat) (Adj : Fin N → Fin N → Prop)
    (hNoLoops : ∀ u, ¬ Adj u u) :
    finiteCliqueNumber N Adj ≤ chromaticNumber Adj hNoLoops := by
  let chi := chromaticNumber Adj hNoLoops
  obtain ⟨color, hProper⟩ := chromaticNumber_colorable Adj hNoLoops
  have hUpper : CliqueUpperBound Adj chi := by
    intro k hClique
    obtain ⟨vertices, hInject, hAdj⟩ := hClique
    let f : Fin (k + 1) → Fin chi :=
      fun i => color (vertices (finToOption k i))
    have hf : ∀ a b, f a = f b → a = b := by
      intro a b heq
      have hOpt : finToOption k a = finToOption k b := by
        by_cases hSame : finToOption k a = finToOption k b
        · exact hSame
        · have hDifferent :
              color (vertices (finToOption k a)) ≠
              color (vertices (finToOption k b)) :=
            hProper _ _ (hAdj _ _ hSame)
          exact False.elim (hDifferent heq)
      exact finToOption_injective k a b hOpt
    exact fin_injective_card_le (k + 1) chi f hf
  exact cliqueNumber_le_any_upper_bound Adj
    (finite_cliques_bounded N Adj) chi hUpper

theorem max_cover_clique_eq_max_cover_chromatic
    (N : Nat) (Adj : Fin N → Fin N → Prop)
    (hSym : ∀ u v, Adj u v → Adj v u)
    (hNoLoops : ∀ u, ¬ Adj u u) :
    max (Witnora.VertexCoverMinimum.vertexCoverNumber Adj)
        (finiteCliqueNumber N Adj) =
    max (Witnora.VertexCoverMinimum.vertexCoverNumber Adj)
        (chromaticNumber Adj hNoLoops) := by
  exact Witnora.ChromaticMaxConsequences.max_cover_chromatic
    (Witnora.VertexCoverMinimum.vertexCoverNumber Adj)
    (finiteCliqueNumber N Adj)
    (chromaticNumber Adj hNoLoops)
    (clique_number_le_chromatic_number N Adj hNoLoops)
    (chromatic_le_max_vertex_cover_clique N Adj hSym hNoLoops)

end Witnora.GraphMaxEquality

#print axioms Witnora.GraphMaxEquality.max_cover_clique_eq_max_cover_chromatic
