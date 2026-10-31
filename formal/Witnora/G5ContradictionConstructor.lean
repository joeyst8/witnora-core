import Witnora.G5Dag
import Witnora.TC063ModelGluing

/-!
# Constructive G5 contradiction certificates: exact base cases

This proves that a contradictory input row needs no DAG operations, and
that two equations on identical supports with opposite RHS bits admit a
one-operation accepted DAG certificate. These are building blocks toward
a general Gaussian-elimination-to-DAG completeness proof, not that full
completeness theorem.
-/

namespace Witnora.G5ContradictionConstructor

open Witnora.G5Trace
open Witnora.G5Dag

/-- Filtering a list by the predicate 'not a member of itself' is empty. -/
theorem filter_not_mem_self (xs : List Nat) :
    xs.filter (fun v => decide (v ∉ xs)) = [] := by
  have aux : ∀ (ys : List Nat), (∀ v ∈ ys, v ∈ xs) →
      ys.filter (fun v => decide (v ∉ xs)) = [] := by
    intro ys
    induction ys with
    | nil =>
        intro _
        rfl
    | cons v rest ih =>
        intro hsub
        have hv : v ∈ xs := hsub v (by simp)
        have ht : ∀ w ∈ rest, w ∈ xs := by
          intro w hw
          exact hsub w (by simp [hw])
        have hrest := ih ht
        simp [List.filter_cons, hv, hrest]
  exact aux xs (by intro v hv; exact hv)

/-- XORing a row's support with itself cancels every variable. -/
theorem xorCoefficients_self (xs : List Nat) :
    xorCoefficients xs xs = [] := by
  simp [xorCoefficients, filter_not_mem_self]

/-- An already present contradiction is an accepted zero-operation DAG. -/
theorem existing_contradiction_certified (rows : List Row)
    (h : ∃ row ∈ rows, row.coefficients = [] ∧ row.rhs = true) :
    checkDagContradiction rows [] = true := by
  unfold checkDagContradiction
  simp only [replayDag]
  apply List.any_eq_true.mpr
  obtain ⟨row, hrow, hc, hr⟩ := h
  refine ⟨row, hrow, ?_⟩
  simp [hc, hr]

/-- For every variable list and opposite RHS bits, one DAG XOR operation
    constructs the explicit inconsistent equation 0 = 1. -/
theorem opposite_rows_certified (xs : List Nat)
    (p q : Bool) (hneq : p ≠ q) :
    checkDagContradiction
      [⟨xs, p⟩, ⟨xs, q⟩] [(0, 1)] = true := by
  cases p <;> cases q <;>
    simp_all [checkDagContradiction, replayDag, xorRow,
      xorCoefficients_self]

/-- The certificate constructor for a pair of opposite rows is fixed,
    independent of width. -/
def oppositePairSteps : List XorRef := [(0, 1)]

theorem oppositePairSteps_complete (xs : List Nat)
    (p q : Bool) (hneq : p ≠ q) :
    checkDagContradiction
      [⟨xs, p⟩, ⟨xs, q⟩] oppositePairSteps = true :=
  opposite_rows_certified xs p q hneq

#print axioms Witnora.G5ContradictionConstructor.xorCoefficients_self
#print axioms Witnora.G5ContradictionConstructor.existing_contradiction_certified
#print axioms Witnora.G5ContradictionConstructor.opposite_rows_certified
#print axioms Witnora.G5ContradictionConstructor.oppositePairSteps_complete

end Witnora.G5ContradictionConstructor
