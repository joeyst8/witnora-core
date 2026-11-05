import Witnora.G5Trace

/-!
# G5 elimination cross-merge signal: proved local meaning

The experimental pairwise heuristic counts pairs of variables that occur
on opposite exclusive sides of one row-XOR operation. This module proves
that both coefficients necessarily survive into the derived row.

This is a local algebraic fact, NOT a claim that the pair forms a primal
graph separator or improves asymptotic SAT complexity.
-/

namespace Witnora.TC063EliminationPairSignal

open Witnora.G5Trace

/-- Two coefficients surviving together after an XOR when each is present
    exclusively on the opposite side of that row operation. -/
theorem opposite_sides_survive
    (target source : List Nat) (u v : Nat)
    (huTarget : u ∈ target) (huNotSource : u ∉ source)
    (hvSource : v ∈ source) (hvNotTarget : v ∉ target) :
    u ∈ xorCoefficients target source ∧
    v ∈ xorCoefficients target source := by
  constructor
  · exact (mem_xorCoefficients target source u).mpr
      (Or.inl ⟨huTarget, huNotSource⟩)
  · exact (mem_xorCoefficients target source v).mpr
      (Or.inr ⟨hvSource, hvNotTarget⟩)

/-- Exclusive-source/target membership guarantees distinct variables. -/
theorem opposite_sides_distinct
    (target source : List Nat) (u v : Nat)
    (huTarget : u ∈ target) (huNotSource : u ∉ source)
    (hvSource : v ∈ source) :
    u ≠ v := by
  intro h
  subst v
  exact huNotSource hvSource

example :
    1 ∈ xorCoefficients [1, 3] [2, 3] ∧
    2 ∈ xorCoefficients [1, 3] [2, 3] := by decide

#print axioms Witnora.TC063EliminationPairSignal.opposite_sides_survive
#print axioms Witnora.TC063EliminationPairSignal.opposite_sides_distinct

end Witnora.TC063EliminationPairSignal
