import Lean
import Witnora.NumericColorCertificate

/-!
# List-level preservation of accepted numeric edge data

The numeric checker validates every raw edge endpoint before decoding.
This module proves the whole decoded list equals the original ordered
list with each endpoint embedded in Fin (N+1), including duplicates
and original edge ordering.
-/

namespace Witnora.NumericEdgeListBridge

open Witnora.NumericColorCertificate

def boundedPair (N : Nat) (edge : Nat × Nat) :
    Fin (N + 1) × Fin (N + 1) :=
  (⟨edge.1 % (N + 1), Nat.mod_lt _ (Nat.succ_pos N)⟩,
   ⟨edge.2 % (N + 1), Nat.mod_lt _ (Nat.succ_pos N)⟩)

def edgeEndpointValid (N : Nat) (edge : Nat × Nat) : Bool :=
  decide (edge.1 < N + 1) && decide (edge.2 < N + 1)

def edgeBoundsValid (N : Nat) (edges : List (Nat × Nat)) : Bool :=
  edges.all (edgeEndpointValid N)

/-- Valid individual entries decode without changing either endpoint. -/
theorem decodeEdge_eq_boundedPair
    (N : Nat) (edge : Nat × Nat)
    (hValid : edgeEndpointValid N edge = true) :
    decodeEdge N edge = some (boundedPair N edge) := by
  have hSplit :
      decide (edge.1 < N + 1) = true ∧
      decide (edge.2 < N + 1) = true := by
    simpa only [edgeEndpointValid, Bool.and_eq_true] using hValid
  have hu : edge.1 < N + 1 := of_decide_eq_true hSplit.1
  have hv : edge.2 < N + 1 := of_decide_eq_true hSplit.2
  simpa [boundedPair, Nat.mod_eq_of_lt hu, Nat.mod_eq_of_lt hv] using
    decodeEdge_preserves N edge.1 edge.2 hu hv

/-- Exact ordered-list preservation for all in-range numeric edges. -/
theorem decodedEdges_preserve_list (N : Nat)
    (edges : List (Nat × Nat))
    (hValid : edgeBoundsValid N edges = true) :
    decodedEdges N edges = edges.map (boundedPair N) := by
  induction edges with
  | nil => rfl
  | cons edge rest ih =>
      have hHead : edgeEndpointValid N edge = true := by
        exact (List.all_eq_true.mp hValid) edge (by simp)
      have hTail : edgeBoundsValid N rest = true := by
        apply List.all_eq_true.mpr
        intro x hx
        exact (List.all_eq_true.mp hValid) x (by simp [hx])
      have hDecode := decodeEdge_eq_boundedPair N edge hHead
      change (edge :: rest).filterMap (decodeEdge N) =
        (edge :: rest).map (boundedPair N)
      simpa [List.filterMap, hDecode] using ih hTail

end Witnora.NumericEdgeListBridge

#print axioms Witnora.NumericEdgeListBridge.decodeEdge_eq_boundedPair
#print axioms Witnora.NumericEdgeListBridge.decodedEdges_preserve_list
