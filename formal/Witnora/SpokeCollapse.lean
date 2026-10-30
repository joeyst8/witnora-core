import Witnora.G5Dag

/-!
# Candidate structural operator: parity-syndrome spoke collapse

Every spoke x XOR y_i = left, y_i XOR z = right imposes the
same endpoint equation x XOR z = left XOR right. Two spokes with
different endpoint syndromes are inconsistent, regardless of how
many other spokes the input contains.

This is an infinite-family theorem and a benchmarkable candidate,
not a claim that parity elimination is mathematically novel.
-/

namespace Witnora.SpokeCollapse

structure Spoke where
  middle : Nat
  left : Bool
  right : Bool
  deriving DecidableEq, Repr

def syndrome (s : Spoke) : Bool := s.left != s.right

def SpokeHolds (x z : Bool) (middleValue : Nat → Bool) (s : Spoke) : Prop :=
  (x != middleValue s.middle) = s.left ∧
  (middleValue s.middle != z) = s.right

def SystemHolds (spokes : List Spoke) (x z : Bool)
    (middleValue : Nat → Bool) : Prop :=
  ∀ s ∈ spokes, SpokeHolds x z middleValue s

/-- Eliminate one intermediate variable; the endpoint syndrome is invariant. -/
theorem spoke_endpoint (x z y left right : Bool)
    (hleft : (x != y) = left)
    (hright : (y != z) = right) :
    (x != z) = (left != right) := by
  cases x <;> cases z <;> cases y <;>
    cases left <;> cases right <;> simp_all

/-- Any satisfying assignment to the whole family respects every
    independently inferred endpoint syndrome. -/
theorem all_endpoint_syndromes
    (spokes : List Spoke) (x z : Bool) (ys : Nat → Bool)
    (h : SystemHolds spokes x z ys)
    (s : Spoke) (hs : s ∈ spokes) :
    (x != z) = syndrome s := by
  obtain ⟨hl, hr⟩ := h s hs
  exact spoke_endpoint x z (ys s.middle) s.left s.right hl hr

/-- Two conflicting syndromes prove UNSAT for an arbitrarily long list. -/
theorem conflicting_syndromes_unsat
    (spokes : List Spoke) (s t : Spoke)
    (hs : s ∈ spokes) (ht : t ∈ spokes)
    (hconflict : (syndrome s != syndrome t) = true) :
    ¬ ∃ x z ys, SystemHolds spokes x z ys := by
  rintro ⟨x, z, ys, hmodels⟩
  have h1 := all_endpoint_syndromes spokes x z ys hmodels s hs
  have h2 := all_endpoint_syndromes spokes x z ys hmodels t ht
  have heq : syndrome s = syndrome t := h1.symm.trans h2
  simp [heq] at hconflict

example :
    ¬ ∃ x z ys, SystemHolds
      [⟨1, false, false⟩, ⟨2, true, false⟩] x z ys := by
  apply conflicting_syndromes_unsat
    [⟨1, false, false⟩, ⟨2, true, false⟩]
    ⟨1, false, false⟩ ⟨2, true, false⟩
  · simp
  · simp
  · decide

#print axioms Witnora.SpokeCollapse.conflicting_syndromes_unsat

end Witnora.SpokeCollapse
