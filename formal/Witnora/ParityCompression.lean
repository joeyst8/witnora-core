import Witnora.CycleParity

/-!
# Parity-connected component compression

Given a root label and relative parity offset for each vertex, a model of
one Boolean root value per component reconstructs a valuation for every
vertex. The theorem is uniform in the graph size and proves every edge
whose endpoints share a root and whose offsets match its parity.

This is an established GF(2) component substitution, not a novel method.
It covers the extracted binary-XOR equations, not arbitrary CNF clauses.
-/

namespace Witnora.ParityCompression

structure Edge where
  u : Nat
  v : Nat
  rhs : Bool
  deriving Repr, DecidableEq

def reconstruct (rootOf : Nat → Nat) (offset : Nat → Bool)
    (rootValue : Nat → Bool) (v : Nat) : Bool :=
  rootValue (rootOf v) != offset v

def EdgeHolds (a : Nat → Bool) (e : Edge) : Prop :=
  (a e.u != a e.v) = e.rhs

def EdgesHold (a : Nat → Bool) (edges : List Edge) : Prop :=
  ∀ e ∈ edges, EdgeHolds a e

def ValidOffsets (rootOf : Nat → Nat) (offset : Nat → Bool)
    (edges : List Edge) : Prop :=
  ∀ e ∈ edges,
    rootOf e.u = rootOf e.v ∧ (offset e.u != offset e.v) = e.rhs

theorem reconstruct_edge (rootOf : Nat → Nat) (offset : Nat → Bool)
    (rootValue : Nat → Bool) (e : Edge)
    (hsame : rootOf e.u = rootOf e.v)
    (hparity : (offset e.u != offset e.v) = e.rhs) :
    EdgeHolds (reconstruct rootOf offset rootValue) e := by
  unfold EdgeHolds reconstruct
  rw [← hsame]
  have hx : (rootValue (rootOf e.u) != offset e.u) !=
      (rootValue (rootOf e.u) != offset e.v) =
      (offset e.u != offset e.v) := by
    cases rootValue (rootOf e.u) <;>
      cases offset e.u <;> cases offset e.v <;> decide
  exact hx.trans hparity

/-- One root choice per component satisfies *all* certified binary XOR edges. -/
theorem reconstruct_preserves_edges
    (rootOf : Nat → Nat) (offset : Nat → Bool)
    (edges : List Edge) (hvalid : ValidOffsets rootOf offset edges)
    (rootValue : Nat → Bool) :
    EdgesHold (reconstruct rootOf offset rootValue) edges := by
  intro e he
  exact reconstruct_edge rootOf offset rootValue e (hvalid e he).1 (hvalid e he).2

#print axioms Witnora.ParityCompression.reconstruct_preserves_edges

end Witnora.ParityCompression
