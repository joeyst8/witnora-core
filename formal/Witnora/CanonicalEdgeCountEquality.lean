import Lean
import Witnora.CanonicalEdgeEnumeration
import Witnora.EdgeCountEquality

/-!
# Unconditional edge-count chromatic maximum equality

The graph's edge count is the size of the internally constructed
undirected-edge enumeration. No edge list is supplied as a hypothesis.
The canonical edge predicate is u < v and adjacency; indexing that
finite set currently uses classical choice, not a deterministic program.
-/

namespace Witnora.CanonicalEdgeCountEquality

open Witnora.CanonicalEdgeEnumeration
open Witnora.EdgeCountEquality
open Witnora.ConcreteGraphBound
open Witnora.ChromaticMinimum

noncomputable def canonicalEdgeCount
    (N : Nat) (Adj : Fin N → Fin N → Prop)
    (hSym : ∀ u v, Adj u v → Adj v u)
    (hNoLoops : ∀ u, ¬ Adj u u) : Nat :=
  (canonical_edge_enumeration N Adj hSym hNoLoops).1

theorem max_canonical_edges_clique_eq_chromatic
    (N : Nat) (Adj : Fin N → Fin N → Prop)
    (hSym : ∀ u v, Adj u v → Adj v u)
    (hNoLoops : ∀ u, ¬ Adj u u) :
    max (canonicalEdgeCount N Adj hSym hNoLoops)
        (finiteCliqueNumber N Adj) =
    max (canonicalEdgeCount N Adj hSym hNoLoops)
        (chromaticNumber Adj hNoLoops) := by
  exact max_edges_clique_eq_max_edges_chromatic
    Adj hSym hNoLoops
    (canonical_edge_enumeration N Adj hSym hNoLoops).2

end Witnora.CanonicalEdgeCountEquality

#print axioms Witnora.CanonicalEdgeCountEquality.max_canonical_edges_clique_eq_chromatic
