import Lean
import Witnora.ExtremalGraphBound
import Witnora.FinitePigeonhole

/-!
# Finite graph chromatic bound with concrete chi and omega

The finite pigeonhole theorem discharges the last independent
clique-size bound assumption. A cover is still given as a bijection
with Fin (n+2); minimizing its size and handling k=0,1 remains.
-/

namespace Witnora.ConcreteGraphBound

open Witnora.ExtremalGraphBound
open Witnora.ChromaticMinimum
open Witnora.CliqueMaximum
open Witnora.FinitePigeonhole

theorem finite_cliques_bounded
    (N : Nat) (Adj : Fin N → Fin N → Prop) :
    ∃ bound, CliqueUpperBound Adj bound := by
  refine ⟨N, ?_⟩
  intro k hClique
  obtain ⟨vertices, hInject, hAdjacent⟩ := hClique
  exact indexed_clique_size_le_vertices N Adj k vertices hInject

noncomputable def finiteCliqueNumber
    (N : Nat) (Adj : Fin N → Fin N → Prop) : Nat :=
  cliqueNumber Adj (finite_cliques_bounded N Adj)

theorem finite_graph_chromatic_max_bound
    (N n : Nat) (Adj : Fin N → Fin N → Prop)
    (S : Fin N → Prop) (label : Fin N → Fin (n + 2))
    (hSym : ∀ u v, Adj u v → Adj v u)
    (hNoLoops : ∀ u, ¬ Adj u u)
    (hIndependent : ∀ u v, ¬ S u → ¬ S v → ¬ Adj u v)
    (hInjectOnCover :
      ∀ u v, S u → S v → label u = label v → u = v)
    (hSurjectOnCover :
      ∀ i : Fin (n + 2), ∃ u, S u ∧ label u = i) :
    chromaticNumber Adj hNoLoops ≤
      max (n + 2) (finiteCliqueNumber N Adj) := by
  exact chromatic_le_max_cover_defined_clique
    N n Adj S label hSym hNoLoops hIndependent
      hInjectOnCover hSurjectOnCover
      (finite_cliques_bounded N Adj)

end Witnora.ConcreteGraphBound
