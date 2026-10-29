import Witnora.Concrete

/-!
# CNF encoding of one forbidden assignment

The full canonical XOR-to-CNF encoding consists of forbidden assignments:
each assignment with the wrong parity contributes one clause rejecting exactly
that assignment. This file establishes the clause-level equivalence for all
variable IDs and assignments. Composition into an exact XOR-CNF extraction
theorem still requires completeness of the forbidden-assignment family.
-/

namespace Witnora.Extraction

open Witnora.Concrete

def forbidClause (fixed : List (Nat × Bool)) : List Literal :=
  fixed.map (fun p => (p.1, !p.2))

/-- The clause that forbids a fixed assignment is true precisely when at
least one of those variable values differs from the assignment. -/
theorem forbidClause_true (bits : List Bool) (fixed : List (Nat × Bool)) :
    (forbidClause fixed).any (litTrue bits) = !(agrees bits fixed) := by
  induction fixed with
  | nil => rfl
  | cons p tail ih =>
    rcases p with ⟨v, value⟩
    simp only [forbidClause, List.map_cons, List.any_cons,
      agrees, List.all_cons] at ih ⊢
    rw [ih]
    cases hb : readVar bits v <;>
      cases hv : value <;>
      cases ht : tail.all (fun p => readVar bits p.1 == p.2) <;>
      simp [litTrue, hb, hv, ht]

/-- XOR of the values of an arbitrary finite variable support. -/
def parityVars : List Nat → (Nat → Bool) → Bool
  | [], _ => false
  | v :: rest, a => Bool.xor (a v) (parityVars rest a)

/-- Parity depends only on values on the specified finite support. -/
theorem parityVars_congr (vars : List Nat) (a b : Nat → Bool)
    (hagrees : ∀ v, v ∈ vars → a v = b v) :
    parityVars vars a = parityVars vars b := by
  induction vars with
  | nil => rfl
  | cons v rest ih =>
      simp only [parityVars]
      rw [hagrees v (by simp)]
      congr 1
      apply ih
      intro w hw
      exact hagrees w (by simp [hw])

/-- A canonical forbidden-assignment clause is satisfied when at least one
variable in the constraint differs from its forbidden value. -/
def forbiddenHolds (vars : List Nat) (bad actual : Nat → Bool) : Prop :=
  ∃ v, v ∈ vars ∧ actual v ≠ bad v

/-- Semantic form of the *complete* canonical XOR-CNF: one forbidden clause
for every assignment having parity opposite the required right-hand side. -/
def canonicalXorCNFHolds (vars : List Nat) (rhs : Bool)
    (actual : Nat → Bool) : Prop :=
  ∀ bad, parityVars vars bad ≠ rhs → forbiddenHolds vars bad actual

/-- Full semantic XOR-CNF equivalence for every finite list of variables,
every Boolean assignment, and either parity bit. No assignments are
enumerated by this proof. The finite Python encoder still needs its own
completeness/serialization refinement theorem. -/
theorem canonicalXorCNF_iff (vars : List Nat) (rhs : Bool)
    (actual : Nat → Bool) :
    canonicalXorCNFHolds vars rhs actual ↔ parityVars vars actual = rhs := by
  classical
  constructor
  · intro h
    apply Classical.byContradiction
    intro hwrong
    obtain ⟨v, _, hv⟩ := h actual hwrong
    exact hv rfl
  · intro hright bad hwrong
    apply Classical.byContradiction
    intro hnone
    have hagrees : ∀ v, v ∈ vars → actual v = bad v := by
      intro v hv
      apply Classical.byContradiction
      intro hdiff
      exact hnone ⟨v, hv, hdiff⟩
    have hbadRight : parityVars vars bad = rhs :=
      (parityVars_congr vars actual bad hagrees).symm.trans hright
    exact hwrong hbadRight

/-- If a CNF guarantees every canonical forbidden clause for an XOR
equation, it entails that equation. The CNF may contain additional clauses.
This is the soundness condition required by G5 UNSAT proof reconstruction. -/
theorem original_entails_extracted_xor
    (vars : List Nat) (rhs : Bool)
    (originalHolds : (Nat → Bool) → Prop)
    (hcomplete : ∀ a, originalHolds a → canonicalXorCNFHolds vars rhs a)
    (a : Nat → Bool) (hmodel : originalHolds a) :
    parityVars vars a = rhs :=
  (canonicalXorCNF_iff vars rhs a).mp (hcomplete a hmodel)

#print axioms Witnora.Extraction.original_entails_extracted_xor

#print axioms Witnora.Extraction.parityVars_congr
#print axioms Witnora.Extraction.canonicalXorCNF_iff

#print axioms Witnora.Extraction.forbidClause_true

end Witnora.Extraction
