import Lean
import Witnora.FiniteChromaticBound
import Witnora.CliqueMaximum

/-!
# Finite graph chromatic maximum with defined extremal quantities

Both chromatic number and clique number are now concrete least-choice
definitions. The clique number requires an explicit finite bound
certificate, to be discharged by the pigeonhole/counting theorem.
The cover-size parameter is represented by a label bijection.
-/

namespace Witnora.ExtremalGraphBound

open Witnora.FiniteChromaticBound
open Witnora.ChromaticMinimum
open Witnora.CliqueMaximum

theorem chromatic_le_max_cover_defined_clique
    (N n : Nat) (Adj : Fin N → Fin N → Prop)
    (S : Fin N → Prop) (label : Fin N → Fin (n + 2))
    (hSym : ∀ u v, Adj u v → Adj v u)
    (hNoLoops : ∀ u, ¬ Adj u u)
    (hIndependent : ∀ u v, ¬ S u → ¬ S v → ¬ Adj u v)
    (hInjectOnCover :
      ∀ u v, S u → S v → label u = label v → u = v)
    (hSurjectOnCover :
      ∀ i : Fin (n + 2), ∃ u, S u ∧ label u = i)
    (hCliqueFinite : ∃ bound, CliqueUpperBound Adj bound) :
    chromaticNumber Adj hNoLoops ≤
      max (n + 2) (cliqueNumber Adj hCliqueFinite) := by
  apply finite_chromatic_le_max_cover_clique
    N n Adj S label (cliqueNumber Adj hCliqueFinite)
    hSym hNoLoops hIndependent hInjectOnCover hSurjectOnCover
  intro k vertices hInject hClique
  exact cliqueNumber_bounds_every_clique
    Adj hCliqueFinite k vertices hInject hClique

end Witnora.ExtremalGraphBound
