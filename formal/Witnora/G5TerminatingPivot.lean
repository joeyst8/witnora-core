import Witnora.G5EliminationInvariant

/-!
# A finite G5 elimination pass on an arbitrary number of target rows

Given a pivot row containing v, eliminate v from every target row by
XORing the pivot exactly when the target contains v. The pass is
computable by a structurally terminating List.map. It preserves all
target equations whenever the pivot holds.

This proves a generalized elimination *pass*. It does not yet choose
independent pivots, establish global normal form, or synthesize the
indexed-DAG certificate for every inconsistent system.
-/

namespace Witnora.G5TerminatingPivot

open Witnora.G5Trace
open Witnora.G5Certificate
open Witnora.G5EliminationInvariant

/-- One deterministic sparse GF(2) pivot update. -/
def eliminateTarget (v : Nat) (pivot target : Row) : Row :=
  if v ∈ target.coefficients then xorRow pivot target else target

/-- One pivot transforms every target exactly once. -/
def eliminatePass (v : Nat) (pivot : Row) (targets : List Row) :
    List Row :=
  targets.map (eliminateTarget v pivot)

theorem eliminatePass_length (v : Nat) (pivot : Row)
    (targets : List Row) :
    (eliminatePass v pivot targets).length = targets.length := by
  simp [eliminatePass]

/-- Every transformed row is logically equivalent to its input in the
    context where the chosen pivot equation holds. -/
theorem eliminateTarget_iff (bound v : Nat) (pivot target : Row)
    (a : Nat → Bool) (hp : RowHolds bound pivot a) :
    RowHolds bound target a ↔
      RowHolds bound (eliminateTarget v pivot target) a := by
  by_cases hv : v ∈ target.coefficients
  · constructor
    · intro ht
      have hx := ((xor_replacement_iff bound pivot target a).mp
        ⟨hp, ht⟩).2
      simpa [eliminateTarget, hv] using hx
    · intro ht
      exact (xor_replacement_iff bound pivot target a).mpr
        ⟨hp, by simpa [eliminateTarget, hv] using ht⟩ |>.2
  · simp [eliminateTarget, hv]

/-- The pivot cannot appear in any output target, provided it occurs
    in the source pivot. -/
theorem eliminateTarget_clears_variable
    (v : Nat) (pivot target : Row)
    (hp : v ∈ pivot.coefficients) :
    v ∉ (eliminateTarget v pivot target).coefficients := by
  by_cases ht : v ∈ target.coefficients
  · change v ∉ (xorRow pivot target).coefficients
    intro hbad
      have hx := (mem_xorCoefficients
        pivot.coefficients target.coefficients v).mp hbad
      rcases hx with ⟨_, hn⟩ | ⟨_, hn⟩
      · exact hn ht
      · exact hn hp
    simpa [eliminateTarget, ht] using hcleared
  · simpa [eliminateTarget, ht]

/-- A pass over any finite list preserves the entire conjunction of
    target constraints, under the retained pivot equation. -/
theorem eliminatePass_equiv (bound v : Nat)
    (pivot : Row) (targets : List Row) (a : Nat → Bool)
    (hp : RowHolds bound pivot a) :
    (∀ row ∈ targets, RowHolds bound row a) ↔
      (∀ row ∈ eliminatePass v pivot targets,
        RowHolds bound row a) := by
  constructor
  · intro hall row hmem
    obtain ⟨original, hsource, heq⟩ :=
      List.mem_map.mp (show row ∈ targets.map (eliminateTarget v pivot) from hmem)
    subst row
    exact (eliminateTarget_iff bound v pivot original a hp).mp
      (hall original hsource)
  · intro hall row hmem
    have hnew : eliminateTarget v pivot row ∈
        eliminatePass v pivot targets := by
      exact List.mem_map.mpr ⟨row, hmem, rfl⟩
    exact (eliminateTarget_iff bound v pivot row a hp).mpr
      (hall (eliminateTarget v pivot row) hnew)

/-- Every target in the output has its selected pivot variable cleared. -/
theorem eliminatePass_clears_variable
    (v : Nat) (pivot : Row) (targets : List Row)
    (hp : v ∈ pivot.coefficients) :
    ∀ row ∈ eliminatePass v pivot targets,
      v ∉ row.coefficients := by
  intro row hr
  obtain ⟨original, _, heq⟩ := List.mem_map.mp
    (show row ∈ targets.map (eliminateTarget v pivot) from hr)
  subst row
  exact eliminateTarget_clears_variable v pivot original hp

#print axioms Witnora.G5TerminatingPivot.eliminateTarget_iff
#print axioms Witnora.G5TerminatingPivot.eliminateTarget_clears_variable
#print axioms Witnora.G5TerminatingPivot.eliminatePass_equiv
#print axioms Witnora.G5TerminatingPivot.eliminatePass_clears_variable

end Witnora.G5TerminatingPivot
