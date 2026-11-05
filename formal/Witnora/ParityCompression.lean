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
  have hx : ((rootValue (rootOf e.u) != offset e.u) !=
      (rootValue (rootOf e.u) != offset e.v)) =
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


/-- A supplied source-backed path from each component root to each variable. -/
def ValidSourcePaths (cnf : Witnora.Concrete.CNF)
    (rootOf : Nat → Nat) (offset : Nat → Bool)
    (paths : Nat → List (Nat × Bool)) : Prop :=
  ∀ v,
    CycleParity.checkSteps cnf (rootOf v) (paths v) = true ∧
    CycleParity.lastVertex (rootOf v) (paths v) = v ∧
    CycleParity.rhsParity (paths v) = offset v

/-- Any source model agrees with its reconstruction from root values. -/
theorem source_model_reconstructs
    (cnf : Witnora.Concrete.CNF)
    (rootOf : Nat → Nat) (offset : Nat → Bool)
    (paths : Nat → List (Nat × Bool))
    (hpaths : ValidSourcePaths cnf rootOf offset paths)
    (a : Nat → Bool) (ha : G5Extraction.CNFHolds cnf a)
    (v : Nat) :
    a v = reconstruct rootOf offset a v := by
  obtain ⟨hcheck, hend, hparity⟩ := hpaths v
  have hw := CycleParity.checkSteps_sound cnf a ha
    (rootOf v) (paths v) hcheck
  have hp := CycleParity.walk_endpoint a (rootOf v) (paths v) hw
  rw [hend, hparity] at hp
  unfold reconstruct
  cases hr : a (rootOf v) <;>
    cases hv : a v <;>
    cases ho : offset v <;> simp_all

/-- Source satisfiability is equivalent to satisfiability after semantic
root substitution, assuming checked root-to-vertex source paths. -/
theorem source_iff_root_residual
    (cnf : Witnora.Concrete.CNF)
    (rootOf : Nat → Nat) (offset : Nat → Bool)
    (paths : Nat → List (Nat × Bool))
    (hpaths : ValidSourcePaths cnf rootOf offset paths) :
    (∃ a, G5Extraction.CNFHolds cnf a) ↔
    (∃ roots, G5Extraction.CNFHolds cnf
      (reconstruct rootOf offset roots)) := by
  constructor
  · rintro ⟨a, ha⟩
    refine ⟨a, ?_⟩
    have heq : reconstruct rootOf offset a = a := by
      funext v
      exact (source_model_reconstructs cnf rootOf offset paths
        hpaths a ha v).symm
    simpa [heq] using ha
  · rintro ⟨roots, hroots⟩
    exact ⟨reconstruct rootOf offset roots, hroots⟩

#print axioms Witnora.ParityCompression.reconstruct_preserves_edges
#print axioms Witnora.ParityCompression.source_iff_root_residual

end Witnora.ParityCompression
