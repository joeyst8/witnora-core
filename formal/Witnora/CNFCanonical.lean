import Witnora.G5Extraction

/-!
# Canonicalization: removing duplicate literals and clauses

A small executable duplicate-removal function is proved to preserve list
membership, and therefore both clause disjunction and CNF conjunction.
Tautology elimination and deterministic sorting are separate obligations.
-/

namespace Witnora.CNFCanonical

open Witnora.Concrete
open Witnora.FiniteXor
open Witnora.G5Extraction

def dedup {α : Type} [DecidableEq α] : List α → List α
  | [] => []
  | x :: xs => if x ∈ xs then dedup xs else x :: dedup xs

theorem mem_dedup {α : Type} [DecidableEq α]
    (xs : List α) (x : α) : x ∈ dedup xs ↔ x ∈ xs := by
  induction xs with
  | nil => simp [dedup]
  | cons y ys ih =>
      by_cases h : y ∈ ys
      · simp [dedup, h, ih, h]
        intro hxy
        subst x
        exact h
      · simp [dedup, h, ih]

theorem any_dedup_iff {α : Type} [DecidableEq α]
    (xs : List α) (p : α → Bool) :
    (dedup xs).any p = true ↔ xs.any p = true := by
  constructor
  · intro h
    obtain ⟨x, hx, hp⟩ := List.any_eq_true.mp h
    exact List.any_eq_true.mpr ⟨x, (mem_dedup xs x).mp hx, hp⟩
  · intro h
    obtain ⟨x, hx, hp⟩ := List.any_eq_true.mp h
    exact List.any_eq_true.mpr ⟨x, (mem_dedup xs x).mpr hx, hp⟩

theorem all_dedup_iff {α : Type} [DecidableEq α]
    (xs : List α) (p : α → Bool) :
    (dedup xs).all p = true ↔ xs.all p = true := by
  constructor
  · intro h
    apply List.all_eq_true.mpr
    intro x hx
    exact List.all_eq_true.mp h x ((mem_dedup xs x).mpr hx)
  · intro h
    apply List.all_eq_true.mpr
    intro x hx
    exact List.all_eq_true.mp h x ((mem_dedup xs x).mp hx)

def dedupLiterals (cnf : CNF) : CNF :=
  cnf.map dedup

def dedupClauses (cnf : CNF) : CNF :=
  dedup cnf

theorem dedupLiterals_correct (cnf : CNF) (a : Nat → Bool) :
    CNFHolds (dedupLiterals cnf) a ↔ CNFHolds cnf a := by
  unfold CNFHolds dedupLiterals
  simp only [List.all_map]
  constructor
  · intro h
    apply List.all_eq_true.mpr
    intro clause hc
    exact (any_dedup_iff clause (signedLitTrue a)).mp
      (by simpa only [Function.comp_apply] using List.all_eq_true.mp h clause hc)
  · intro h
    apply List.all_eq_true.mpr
    intro clause hc
    exact (any_dedup_iff clause (signedLitTrue a)).mpr
      (List.all_eq_true.mp h clause hc)

theorem dedupClauses_correct (cnf : CNF) (a : Nat → Bool) :
    CNFHolds (dedupClauses cnf) a ↔ CNFHolds cnf a := by
  change (dedup cnf).all (fun clause => clause.any (signedLitTrue a)) = true ↔
    cnf.all (fun clause => clause.any (signedLitTrue a)) = true
  exact all_dedup_iff cnf (fun clause => clause.any (signedLitTrue a))

#print axioms Witnora.CNFCanonical.mem_dedup
#print axioms Witnora.CNFCanonical.dedupLiterals_correct
#print axioms Witnora.CNFCanonical.dedupClauses_correct

end Witnora.CNFCanonical
