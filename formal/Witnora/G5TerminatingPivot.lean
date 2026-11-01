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
  · have hcleared : v ∉ (xorRow pivot target).coefficients := by
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

/-- Select the first row containing v, retaining all other rows in their
    original relative order. Structural recursion on the row list
    guarantees this search terminates. -/
def extractPivot (v : Nat) : List Row → Option (Row × List Row)
  | [] => none
  | row :: rest =>
      if v ∈ row.coefficients then
        some (row, rest)
      else
        (extractPivot v rest).map (fun result => (result.1, row :: result.2))

/-- A complete finite pass driver. It never tries to re-eliminate into a
    previously retained pivot. The recursive argument is the shrinking
    variable list, giving a direct termination proof by construction. -/
def eliminateVariables : List Nat → List Row → List Row × List Row
  | [], rows => ([], rows)
  | v :: remainingVars, rows =>
      match extractPivot v rows with
      | none => eliminateVariables remainingVars rows
      | some (pivot, otherRows) =>
          let (pivots, residual) :=
            eliminateVariables remainingVars
              (eliminatePass v pivot otherRows)
          (pivot :: pivots, residual)

/-- The empty schedule terminates immediately and changes no row. -/
theorem eliminateVariables_empty (rows : List Row) :
    eliminateVariables [] rows = ([], rows) := rfl

/-- A three-row contradiction is revealed by two successive pivot passes.
    This is an executable regression, not the universal completeness proof. -/
example :
    (eliminateVariables [1, 2]
      [⟨[1, 2], false⟩, ⟨[1], false⟩, ⟨[2], true⟩]).2 =
      [⟨[], true⟩] := by decide

/-- A consistent system leaves an equation rather than fabricating a
    contradiction. -/
example :
    (eliminateVariables [1, 2]
      [⟨[1, 2], false⟩, ⟨[1], false⟩]).2 = [] := by decide

/-- A successful pivot extraction retains exactly the same rows,
    changing only their order. -/
theorem extractPivot_perm
    (v : Nat) (rows : List Row) (pivot : Row) (others : List Row)
    (h : extractPivot v rows = some (pivot, others)) :
    rows.Perm (pivot :: others) := by
  induction rows generalizing pivot others with
  | nil =>
      simp [extractPivot] at h
  | cons head tail ih =>
      by_cases hv : v ∈ head.coefficients
      · simp [extractPivot, hv] at h
        rcases h with ⟨heq1, heq2⟩
        subst pivot
        subst others
        rfl
      · cases hp : extractPivot v tail with
        | none =>
            simp [extractPivot, hv, hp] at h
        | some result =>
            cases result with
            | mk p remaining =>
                simp [extractPivot, hv, hp] at h
                rcases h with ⟨heq1, heq2⟩
                subst pivot
                subst others
                exact (List.Perm.cons head (ih p remaining hp)).trans
                  (List.Perm.swap head p remaining).symm

/-- One extracted pivot plus its elimination pass is *exactly*
    model-equivalent to the original entire row list. -/
theorem extract_and_eliminate_iff
    (bound v : Nat) (rows : List Row)
    (pivot : Row) (others : List Row) (a : Nat → Bool)
    (h : extractPivot v rows = some (pivot, others)) :
    (∀ row ∈ rows, RowHolds bound row a) ↔
      (RowHolds bound pivot a ∧
        ∀ row ∈ eliminatePass v pivot others, RowHolds bound row a) := by
  have hperm := extractPivot_perm v rows pivot others h
  constructor
  · intro hall
    have hmodel : ∀ row ∈ pivot :: others, RowHolds bound row a := by
      intro row hr
      exact hall row (hperm.mem_iff.mpr hr)
    have hp : RowHolds bound pivot a := hmodel pivot (by simp)
    refine ⟨hp, ?_⟩
    apply (eliminatePass_equiv bound v pivot others a hp).mp
    intro row hr
    exact hmodel row (by simp [hr])
  · rintro ⟨hp, htail⟩
    have horig := (eliminatePass_equiv bound v pivot others a hp).mpr htail
    intro row hr
    have hr' : row ∈ pivot :: others := hperm.mem_iff.mp hr
    rcases List.mem_cons.mp hr' with heq | hmem
    · subst row
      exact hp
    · exact horig row hmem

#print axioms Witnora.G5TerminatingPivot.extractPivot_perm
#print axioms Witnora.G5TerminatingPivot.extract_and_eliminate_iff

/-- Every finite elimination schedule preserves *all* models of the input
    row system, represented by its retained pivots and residual rows.
    The recursive driver performs only verified elementary row updates. -/
theorem eliminateVariables_models_iff
    (bound : Nat) (vars : List Nat) (rows : List Row) (a : Nat → Bool) :
    (∀ row ∈ rows, RowHolds bound row a) ↔
      (∀ row ∈ (eliminateVariables vars rows).1 ++
          (eliminateVariables vars rows).2,
        RowHolds bound row a) := by
  induction vars generalizing rows with
  | nil =>
      simp [eliminateVariables]
  | cons v remaining ih =>
      cases hp : extractPivot v rows with
      | none =>
          simpa [eliminateVariables, hp] using ih rows
      | some result =>
          cases result with
          | mk pivot others =>
              cases hr : eliminateVariables remaining
                  (eliminatePass v pivot others) with
              | mk pivots residual =>
                  have hstep := extract_and_eliminate_iff
                    bound v rows pivot others a hp
                  have htail :
                      (∀ row ∈ eliminatePass v pivot others,
                        RowHolds bound row a) ↔
                      (∀ row ∈ pivots ++ residual,
                        RowHolds bound row a) := by
                    simpa [hr] using
                      (ih (eliminatePass v pivot others))
                  have hjoined :
                      (RowHolds bound pivot a ∧
                        ∀ row ∈ pivots ++ residual,
                          RowHolds bound row a) ↔
                      (∀ row ∈ (pivot :: pivots) ++ residual,
                        RowHolds bound row a) := by
                    simp [List.mem_append, List.mem_cons, or_imp, forall_and]
                  calc
                    (∀ row ∈ rows, RowHolds bound row a) ↔
                        (RowHolds bound pivot a ∧
                          ∀ row ∈ eliminatePass v pivot others,
                            RowHolds bound row a) := hstep
                    _ ↔ (RowHolds bound pivot a ∧
                        ∀ row ∈ pivots ++ residual,
                          RowHolds bound row a) := by
                      constructor
                      · rintro ⟨hpivot, ht⟩
                        exact ⟨hpivot, htail.mp ht⟩
                      · rintro ⟨hpivot, ht⟩
                        exact ⟨hpivot, htail.mpr ht⟩
                    _ ↔ (∀ row ∈ (eliminateVariables
                        (v :: remaining) rows).1 ++
                        (eliminateVariables (v :: remaining) rows).2,
                          RowHolds bound row a) := by
                      simpa [eliminateVariables, hp, hr] using hjoined

/-- The algorithm consequently preserves satisfiability and
    unsatisfiability, for every input row set and finite pivot schedule. -/
theorem eliminateVariables_sat_iff
    (bound : Nat) (vars : List Nat) (rows : List Row) :
    (∃ a : Nat → Bool,
      ∀ row ∈ rows, RowHolds bound row a) ↔
    (∃ a : Nat → Bool,
      ∀ row ∈ (eliminateVariables vars rows).1 ++
        (eliminateVariables vars rows).2, RowHolds bound row a) := by
  constructor
  · rintro ⟨a, h⟩
    exact ⟨a, (eliminateVariables_models_iff bound vars rows a).mp h⟩
  · rintro ⟨a, h⟩
    exact ⟨a, (eliminateVariables_models_iff bound vars rows a).mpr h⟩

#print axioms Witnora.G5TerminatingPivot.eliminateVariables_models_iff
#print axioms Witnora.G5TerminatingPivot.eliminateVariables_sat_iff

end Witnora.G5TerminatingPivot
