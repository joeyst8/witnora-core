import Witnora.G5Extraction

/-!
# CNF conditioning under a finite separator assignment

A separator is modeled as a partial assignment `Nat → Option Bool`.
The executable reducer removes satisfied clauses and false assigned
literals, preserving unassigned literals. This file proves a semantic
equivalence for every total assignment extending the separator.

The representation bridge from Python's dictionary assignment and Clause
objects to this Lean function remains a separate implementation obligation.
-/

namespace Witnora.Conditioning

open Witnora.Concrete
open Witnora.FiniteXor
open Witnora.G5Extraction

def agreesWith (fixed : Nat → Option Bool) (a : Nat → Bool) : Prop :=
  ∀ v b, fixed v = some b → a v = b

def conditionClause (fixed : Nat → Option Bool) :
    List Literal → Option (List Literal)
  | [] => some []
  | lit :: rest =>
      match fixed lit.1 with
      | none => (conditionClause fixed rest).map (lit :: ·)
      | some b =>
          if (if lit.2 then b else !b) then none
          else conditionClause fixed rest

def conditionCNF (fixed : Nat → Option Bool) (cnf : CNF) : CNF :=
  cnf.filterMap (conditionClause fixed)

def conditionedClauseTrue (a : Nat → Bool) :
    Option (List Literal) → Bool
  | none => true
  | some clause => clause.any (signedLitTrue a)

theorem conditionClause_correct
    (fixed : Nat → Option Bool) (a : Nat → Bool)
    (h : agreesWith fixed a) (clause : List Literal) :
    conditionedClauseTrue a (conditionClause fixed clause) =
      clause.any (signedLitTrue a) := by
  induction clause with
  | nil => rfl
  | cons lit rest ih =>
      unfold conditionClause
      cases hv : fixed lit.1 with
      | none =>
          simp only [hv]
          cases ht : conditionClause fixed rest with
          | none =>
              simp [conditionedClauseTrue, ht, List.any_cons] at ih ⊢
              simp [ih]
          | some tail =>
              simp [conditionedClauseTrue, ht, List.any_cons] at ih ⊢
              simp [ih]
      | some b =>
          have hab : a lit.1 = b := h lit.1 b hv
          cases lit with
          | mk v polarity =>
              cases polarity <;> cases b <;>
                simp [conditionedClauseTrue, signedLitTrue, hv, hab,
                  List.any_cons] <;> exact ih

theorem conditionCNF_bool
    (fixed : Nat → Option Bool) (a : Nat → Bool)
    (h : agreesWith fixed a) (cnf : CNF) :
    (conditionCNF fixed cnf).all (fun clause => clause.any (signedLitTrue a)) =
      cnf.all (fun clause => clause.any (signedLitTrue a)) := by
  induction cnf with
  | nil => rfl
  | cons clause rest ih =>
      have heq := conditionClause_correct fixed a h clause
      simp only [conditionCNF, List.filterMap_cons]
      cases hc : conditionClause fixed clause with
      | none =>
          simp [conditionedClauseTrue, hc] at heq
          simp only [hc, List.all_cons]
          simp [conditionCNF, ih, heq]
      | some reduced =>
          simp [conditionedClauseTrue, hc] at heq
          simp only [hc, List.all_cons]
          simp [conditionCNF, ih, heq]

theorem conditionCNF_correct
    (fixed : Nat → Option Bool) (a : Nat → Bool)
    (h : agreesWith fixed a) (cnf : CNF) :
    CNFHolds (conditionCNF fixed cnf) a ↔ CNFHolds cnf a := by
  unfold CNFHolds
  rw [conditionCNF_bool fixed a h cnf]

#print axioms Witnora.Conditioning.conditionClause_correct
#print axioms Witnora.Conditioning.conditionCNF_correct

end Witnora.Conditioning
