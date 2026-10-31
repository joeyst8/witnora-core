import Lean
import Witnora.EdgeEndpointCover
import Witnora.FiniteImageCardinality
import Witnora.GraphMaxEquality
import Witnora.ChromaticMaxConsequences

/-!
# Vertex-cover bound by certified undirected edge count

For any complete, sound, unique enumeration of m undirected edges,
the minimum vertex cover has size <= m. Combine with the universal
chromatic theorem to obtain the second maximum equality.
-/

namespace Witnora.EdgeCountEquality

open Witnora.EdgeEndpointCover
open Witnora.FiniteImageCardinality
open Witnora.VertexCoverMinimum
open Witnora.ConcreteGraphBound
open Witnora.ChromaticMinimum
open Witnora.UniversalChromaticMax
open Witnora.GraphMaxEquality

theorem minimum_cover_le_edge_slots
    {N m : Nat} (Adj : Fin N → Fin N → Prop)
    (enumeration : EdgeEnumeration N m Adj) :
    vertexCoverNumber Adj ≤ m := by
  let S := FirstEndpoints enumeration
  obtain ⟨label, hLabelInject⟩ :=
    first_endpoints_inject_into_edge_slots Adj enumeration
  obtain ⟨k, hkm, rank, hRankInject, hRankSurject⟩ :=
    compress_injective_labels m label hLabelInject
  have hExact : CoverCertificate Adj k :=
    ⟨S, rank, first_endpoints_cover Adj enumeration,
      hRankInject, hRankSurject⟩
  exact Nat.le_trans
    (vertexCoverNumber_minimal Adj k hExact) hkm

theorem max_edges_clique_eq_max_edges_chromatic
    {N m : Nat} (Adj : Fin N → Fin N → Prop)
    (hSym : ∀ u v, Adj u v → Adj v u)
    (hNoLoops : ∀ u, ¬ Adj u u)
    (enumeration : EdgeEnumeration N m Adj) :
    max m (finiteCliqueNumber N Adj) =
      max m (chromaticNumber Adj hNoLoops) := by
  exact Witnora.ChromaticMaxConsequences.max_edges_chromatic
    m (vertexCoverNumber Adj) (finiteCliqueNumber N Adj)
      (chromaticNumber Adj hNoLoops)
      (minimum_cover_le_edge_slots Adj enumeration)
      (clique_number_le_chromatic_number N Adj hNoLoops)
      (chromatic_le_max_vertex_cover_clique N Adj hSym hNoLoops)

end Witnora.EdgeCountEquality

#print axioms Witnora.EdgeCountEquality.max_edges_clique_eq_max_edges_chromatic
