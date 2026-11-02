import Init

/-!
TC-063 conditional owner soundness, kernel-only core.

This file proves the semantic *routing and conditioning* equivalence
for every finite list of occurrence-indexed clauses. It does not assert
that a given Python graph decomposition meets the owner's structural
obligations, nor does it prove DIMACS normalization or G5 soundness.
-/

namespace Witnora.TC063

universe u

/-- Each pair contains its original one-based occurrence index and clause. -/
abbrev Occurrence (Clause : Type u) := Nat × Clause

/-- Every occurrence in the list satisfies the supplied clause predicate. -/
def SatAll {Clause : Type u}
    (formula : List (Occurrence Clause)) (holds : Clause → Prop) : Prop :=
  ∀ row, row ∈ formula → holds row.2

/-- Route by occurrence ID, retaining repeated clause *values*. -/
def bucket {Clause : Type u}
    (formula : List (Occurrence Clause))
    (owner : Nat → Option Nat) (target : Option Nat) :
    List (Occurrence Clause) :=
  formula.filter (fun row => decide (owner row.1 = target))

theorem mem_bucket_iff {Clause : Type u}
    (formula : List (Occurrence Clause))
    (owner : Nat → Option Nat) (target : Option Nat)
    (row : Occurrence Clause) :
    row ∈ bucket formula owner target ↔
      row ∈ formula ∧ owner row.1 = target := by
  simp [bucket]

/--
If each referenced component number is in range, formula satisfaction
is equivalent to satisfaction of the separator-only bucket and every
component bucket. No graph traversal is trusted in this theorem.
-/
theorem sat_all_buckets_iff {Clause : Type u}
    (formula : List (Occurrence Clause))
    (owner : Nat → Option Nat)
    (holds : Clause → Prop)
    (componentCount : Nat)
    (hBound : ∀ row, row ∈ formula →
      ∀ i, owner row.1 = some i → i < componentCount) :
    SatAll formula holds ↔
      SatAll (bucket formula owner none) holds ∧
      (∀ i, i < componentCount →
        SatAll (bucket formula owner (some i)) holds) := by
  constructor
  · intro h
    constructor
    · intro row hr
      exact h row ((mem_bucket_iff formula owner none row).mp hr).1
    · intro i _ row hr
      exact h row ((mem_bucket_iff formula owner (some i) row).mp hr).1
  · intro h row hr
    cases hOwner : owner row.1 with
    | none =>
        exact h.1 row
          ((mem_bucket_iff formula owner none row).mpr ⟨hr, hOwner⟩)
    | some i =>
        exact h.2 i (hBound row hr i hOwner) row
          ((mem_bucket_iff formula owner (some i) row).mpr ⟨hr, hOwner⟩)

/-- A clause is true when at least one literal is true. -/
def ClauseSat {Lit : Type u}
    (assignment : Lit → Prop) (clause : List Lit) : Prop :=
  ∃ lit, lit ∈ clause ∧ assignment lit

/--
Semantic form of conditioning: a clause is either made true by a
separator literal, or has a true non-separator literal.
-/
def ConditionedSat {Lit : Type u}
    (assignment separatorAssignment : Lit → Prop)
    (inSeparator : Lit → Prop) (clause : List Lit) : Prop :=
  (∃ lit, lit ∈ clause ∧ inSeparator lit ∧ separatorAssignment lit) ∨
  (∃ lit, lit ∈ clause ∧ ¬ inSeparator lit ∧ assignment lit)

/--
Universal clause-conditioning equivalence for any full assignment
agreeing with the separator assignment on separator literals.
-/
theorem clause_conditioned_iff {Lit : Type u}
    (assignment separatorAssignment : Lit → Prop)
    (inSeparator : Lit → Prop)
    (clause : List Lit)
    (agree : ∀ lit, inSeparator lit →
      (assignment lit ↔ separatorAssignment lit)) :
    ClauseSat assignment clause ↔
      ConditionedSat assignment separatorAssignment inSeparator clause := by
  constructor
  · rintro ⟨lit, hMem, hTrue⟩
    by_cases hSep : inSeparator lit
    · exact Or.inl ⟨lit, hMem, hSep, (agree lit hSep).mp hTrue⟩
    · exact Or.inr ⟨lit, hMem, hSep, hTrue⟩
  · intro h
    rcases h with h | h
    · rcases h with ⟨lit, hMem, hSep, hAlpha⟩
      exact ⟨lit, hMem, (agree lit hSep).mpr hAlpha⟩
    · rcases h with ⟨lit, hMem, _, hTrue⟩
      exact ⟨lit, hMem, hTrue⟩

/--
The combined semantic core: source CNF truth is equivalent to truth
of all conditioned, occurrence-indexed buckets. Empty clauses, repeated
clauses, and separator-only clauses are not excluded.
-/
theorem tc063_conditioned_partition_iff {Lit : Type u}
    (formula : List (Occurrence (List Lit)))
    (owner : Nat → Option Nat)
    (componentCount : Nat)
    (assignment separatorAssignment : Lit → Prop)
    (inSeparator : Lit → Prop)
    (agree : ∀ lit, inSeparator lit →
      (assignment lit ↔ separatorAssignment lit))
    (hBound : ∀ row, row ∈ formula →
      ∀ i, owner row.1 = some i → i < componentCount) :
    SatAll formula (ClauseSat assignment) ↔
      SatAll (bucket formula owner none)
        (ConditionedSat assignment separatorAssignment inSeparator) ∧
      (∀ i, i < componentCount →
        SatAll (bucket formula owner (some i))
          (ConditionedSat assignment separatorAssignment inSeparator)) := by
  have hCondition :
      SatAll formula (ClauseSat assignment) ↔
        SatAll formula
          (ConditionedSat assignment separatorAssignment inSeparator) := by
    constructor
    · intro h row hMem
      exact (clause_conditioned_iff
        assignment separatorAssignment inSeparator row.2 agree).mp
          (h row hMem)
    · intro h row hMem
      exact (clause_conditioned_iff
        assignment separatorAssignment inSeparator row.2 agree).mpr
          (h row hMem)
  exact hCondition.trans
    (sat_all_buckets_iff formula owner
      (ConditionedSat assignment separatorAssignment inSeparator)
      componentCount hBound)

end Witnora.TC063
