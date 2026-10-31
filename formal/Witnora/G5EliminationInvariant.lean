import Witnora.G5ContradictionConstructor

/-!
# Reversible G5 Gaussian pivot invariant

A row replacement target := target XOR source preserves the entire set
of satisfying assignments, in both directions. Unlike a one-way soundness
lemma, this is the core exact-invariance statement for Gaussian elimination.
It is proved for arbitrary sparse supports and arbitrary assignments.
A global pivot-scheduling algorithm and completeness of DAG construction
from inconsistent systems remain separate obligations.
-/

namespace Witnora.G5EliminationInvariant

open Witnora.G5Trace
open Witnora.G5Certificate
open Witnora.SparseParity

/-- The row XOR replacement is logically reversible whenever the source
    row is retained: (source AND target) iff (source AND source XOR target). -/
theorem xor_replacement_iff
    (bound : Nat) (source target : Row) (a : Nat → Bool) :
    (RowHolds bound source a ∧ RowHolds bound target a) ↔
      (RowHolds bound source a ∧
        RowHolds bound (xorRow source target) a) := by
  constructor
  · rintro ⟨hs, ht⟩
    exact ⟨hs, xorRow_holds bound source target a hs ht⟩
  · rintro ⟨hs, hx⟩
    refine ⟨hs, ?_⟩
    unfold RowHolds at hs hx ⊢
    change
      sparseParity bound
        (xorCoefficients source.coefficients target.coefficients) a =
        Bool.xor source.rhs target.rhs at hx
    rw [sparseParity_xor, hs] at hx
    cases hr : sparseParity bound target.coefficients a <;>
      cases hsRhs : source.rhs <;>
      cases htRhs : target.rhs <;>
      simp_all [Bool.xor]

/-- Eliminating one row against another leaves two-row SAT unchanged. -/
theorem pair_sat_iff_after_pivot (bound : Nat)
    (source target : Row) :
    (∃ a : Nat → Bool,
      RowHolds bound source a ∧ RowHolds bound target a) ↔
    (∃ a : Nat → Bool,
      RowHolds bound source a ∧
        RowHolds bound (xorRow source target) a) := by
  constructor
  · rintro ⟨a, h⟩
    exact ⟨a, (xor_replacement_iff bound source target a).mp h⟩
  · rintro ⟨a, h⟩
    exact ⟨a, (xor_replacement_iff bound source target a).mpr h⟩

/-- Therefore this pivot also preserves UNSAT, not merely entailment. -/
theorem pair_unsat_iff_after_pivot (bound : Nat)
    (source target : Row) :
    (¬ ∃ a : Nat → Bool,
      RowHolds bound source a ∧ RowHolds bound target a) ↔
    (¬ ∃ a : Nat → Bool,
      RowHolds bound source a ∧
        RowHolds bound (xorRow source target) a) := by
  exact not_congr (pair_sat_iff_after_pivot bound source target)

#print axioms Witnora.G5EliminationInvariant.xor_replacement_iff
#print axioms Witnora.G5EliminationInvariant.pair_sat_iff_after_pivot
#print axioms Witnora.G5EliminationInvariant.pair_unsat_iff_after_pivot

end Witnora.G5EliminationInvariant
