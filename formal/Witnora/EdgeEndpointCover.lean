import Lean
import Witnora.VertexCoverMinimum

/-!
# Certified enumeration of undirected graph edges

Every undirected edge is listed once, up to endpoint reversal.
Selecting one endpoint per listed edge gives a valid vertex cover.
The subsequent counting bridge will show that the minimum cover
has size no greater than the length of this enumeration.
-/

namespace Witnora.EdgeEndpointCover

open Witnora.VertexCoverMinimum

def SameUndirectedEdge {N : Nat}
    (a b : Fin N × Fin N) : Prop :=
  a = b ∨ a = (b.2, b.1)

structure EdgeEnumeration (N m : Nat)
    (Adj : Fin N → Fin N → Prop) where
  edge : Fin m → Fin N × Fin N
  sound : ∀ i, Adj (edge i).1 (edge i).2
  complete : ∀ u v, Adj u v →
    ∃ i, SameUndirectedEdge (edge i) (u, v)
  unique : ∀ i j, SameUndirectedEdge (edge i) (edge j) → i = j

def FirstEndpoints {N m : Nat} {Adj : Fin N → Fin N → Prop}
    (enumeration : EdgeEnumeration N m Adj) (u : Fin N) : Prop :=
  ∃ i, (enumeration.edge i).1 = u

theorem first_endpoints_cover
    {N m : Nat} (Adj : Fin N → Fin N → Prop)
    (enumeration : EdgeEnumeration N m Adj) :
    IsVertexCover Adj (FirstEndpoints enumeration) := by
  intro u v huv
  obtain ⟨i, hEdge⟩ := enumeration.complete u v huv
  rcases hEdge with hDirect | hReverse
  · left
    exact ⟨i, congrArg Prod.fst hDirect⟩
  · right
    exact ⟨i, congrArg Prod.fst hReverse⟩

theorem first_endpoints_witnessed
    {N m : Nat} (Adj : Fin N → Fin N → Prop)
    (enumeration : EdgeEnumeration N m Adj)
    (u : Fin N) (hu : FirstEndpoints enumeration u) :
    ∃ i : Fin m, (enumeration.edge i).1 = u := hu

end Witnora.EdgeEndpointCover
