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

theorem dedup_nodup {α : Type} [DecidableEq α]
    (xs : List α) : (dedup xs).Nodup := by
  induction xs with
  | nil => exact List.Nodup.nil
  | cons x xs ih =>
      by_cases h : x ∈ xs
      · simpa [dedup, h] using ih
      · have hx : x ∉ dedup xs := by
          intro hx
          exact h ((mem_dedup xs x).mp hx)
        simpa [dedup, h] using (List.Nodup.cons hx ih)

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

def complementary (lit : Literal) : Literal := (lit.1, !lit.2)

def isTautology (clause : List Literal) : Bool :=
  clause.any (fun lit => decide (complementary lit ∈ clause))

theorem complementary_satisfied (lit : Literal) (a : Nat → Bool) :
    signedLitTrue a lit = true ∨
      signedLitTrue a (complementary lit) = true := by
  cases lit with
  | mk v polarity =>
      cases polarity <;> cases a v <;>
        simp [signedLitTrue, complementary]

theorem tautology_is_true (clause : List Literal) (a : Nat → Bool)
    (h : isTautology clause = true) :
    clause.any (signedLitTrue a) = true := by
  obtain ⟨lit, hlit, hcomp⟩ := List.any_eq_true.mp h
  have hc : complementary lit ∈ clause := by
    simpa [isTautology] using hcomp
  rcases complementary_satisfied lit a with hp | hn
  · exact List.any_eq_true.mpr ⟨lit, hlit, hp⟩
  · exact List.any_eq_true.mpr ⟨complementary lit, hc, hn⟩

def dropTautologies (cnf : CNF) : CNF :=
  cnf.filter (fun clause => !isTautology clause)

theorem dropTautologies_bool (cnf : CNF) (a : Nat → Bool) :
    (dropTautologies cnf).all (fun clause => clause.any (signedLitTrue a)) =
      cnf.all (fun clause => clause.any (signedLitTrue a)) := by
  induction cnf with
  | nil => rfl
  | cons clause rest ih =>
      by_cases ht : isTautology clause = true
      · have htrue := tautology_is_true clause a ht
        simp only [dropTautologies, List.filter_cons, ht,
          Bool.not_true, List.all_cons]
        change (dropTautologies rest).all
            (fun clause => clause.any (signedLitTrue a)) =
          (clause.any (signedLitTrue a) &&
            rest.all (fun clause => clause.any (signedLitTrue a)))
        rw [ih, htrue]
        simp
      · have hf : isTautology clause = false := by
          cases hbit : isTautology clause <;> simp_all
        simp only [dropTautologies, List.filter_cons, hf,
          Bool.not_false, List.all_cons]
        change (clause.any (signedLitTrue a) &&
            (dropTautologies rest).all
              (fun clause => clause.any (signedLitTrue a))) =
          (clause.any (signedLitTrue a) &&
            rest.all (fun clause => clause.any (signedLitTrue a)))
        rw [ih]

theorem dropTautologies_correct (cnf : CNF) (a : Nat → Bool) :
    CNFHolds (dropTautologies cnf) a ↔ CNFHolds cnf a := by
  unfold CNFHolds
  rw [dropTautologies_bool cnf a]

def normalize (cnf : CNF) : CNF :=
  dedupClauses (dropTautologies (dedupLiterals cnf))

theorem normalize_correct (cnf : CNF) (a : Nat → Bool) :
    CNFHolds (normalize cnf) a ↔ CNFHolds cnf a := by
  unfold normalize
  rw [dedupClauses_correct, dropTautologies_correct, dedupLiterals_correct]

example : isTautology [(1, true), (2, true), (1, false)] = true := by decide
example : isTautology [(1, true), (2, true)] = false := by decide

#print axioms Witnora.CNFCanonical.tautology_is_true
#print axioms Witnora.CNFCanonical.dropTautologies_correct
#print axioms Witnora.CNFCanonical.normalize_correct

#print axioms Witnora.CNFCanonical.dedup_nodup
#print axioms Witnora.CNFCanonical.mem_dedup
#print axioms Witnora.CNFCanonical.dedupLiterals_correct
#print axioms Witnora.CNFCanonical.dedupClauses_correct

end Witnora.CNFCanonical
