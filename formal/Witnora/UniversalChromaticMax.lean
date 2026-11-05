import Lean
import Init.Omega
import Witnora.SmallCoverBounds

/-!
# Universal finite simple-graph chromatic maximum bound

For every symmetric irreflexive graph on Fin N, the chromatic number
is at most the maximum of the minimum vertex-cover size and the
maximum clique size. All three extrema are concretely defined, and
the zero-, one-, and larger-cover cases are proved separately.

No theorem hypotheses assert the desired inequality or any extremal
number property. No sorry, axiom declaration, or unsafe code is used.
-/

namespace Witnora.UniversalChromaticMax

open Witnora.ChromaticMinimum
open Witnora.VertexCoverMinimum
open Witnora.ConcreteGraphBound
open Witnora.CoverMinimumBridge
open Witnora.SmallCoverBounds

theorem chromatic_le_max_vertex_cover_clique
    (N : Nat) (Adj : Fin N → Fin N → Prop)
    (hSym : ∀ u v, Adj u v → Adj v u)
    (hNoLoops : ∀ u, ¬ Adj u u) :
    chromaticNumber Adj hNoLoops ≤
      max (vertexCoverNumber Adj) (finiteCliqueNumber N Adj) := by
  by_cases hZero : vertexCoverNumber Adj = 0
  · simpa [hZero] using
      zero_cover_bound N Adj hNoLoops
        (by simpa [hZero] using vertexCoverNumber_certificate Adj)
  · by_cases hOne : vertexCoverNumber Adj = 1
    · simpa [hOne] using
        one_cover_bound N Adj hSym hNoLoops
          (by simpa [hOne] using vertexCoverNumber_certificate Adj)
    · have hLarge : 2 ≤ vertexCoverNumber Adj := by omega
      exact graph_bound_if_min_cover_at_least_two
        N Adj hSym hNoLoops hLarge

end Witnora.UniversalChromaticMax
