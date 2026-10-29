import Witnora.CNFCanonical
import Witnora.SignedSerialization

/-!
A deterministic executable sorting model for Python's canonical signed clauses.
Membership lemmas are independent of comparator consistency; lexicographic
ordering and source-level Python refinement are separate obligations.
-/

namespace Witnora.CNFSorted

open Witnora.Concrete
open Witnora.G5Extraction
open Witnora.FiniteXor
open Witnora.CNFCanonical

def insertBy {α : Type} (le : α → α → Bool) (x : α) : List α → List α
  | [] => [x]
  | y :: ys =>
      if le x y then x :: y :: ys else y :: insertBy le x ys

def sortBy {α : Type} (le : α → α → Bool) : List α → List α
  | [] => []
  | x :: xs => insertBy le x (sortBy le xs)

theorem mem_insertBy {α : Type} (le : α → α → Bool)
    (x z : α) (xs : List α) :
    z ∈ insertBy le x xs ↔ z = x ∨ z ∈ xs := by
  induction xs with
  | nil => simp [insertBy]
  | cons y ys ih =>
      by_cases h : le x y = true
      · simp [insertBy, h, or_assoc]
      · have hf : le x y = false := by
          cases hv : le x y <;> simp_all
        simp [insertBy, hf, ih, or_left_comm, or_assoc]

theorem mem_sortBy {α : Type} (le : α → α → Bool)
    (xs : List α) (z : α) :
    z ∈ sortBy le xs ↔ z ∈ xs := by
  induction xs with
  | nil => simp [sortBy]
  | cons x rest ih =>
      simp [sortBy, mem_insertBy, ih, eq_comm]

theorem any_sortBy_iff {α : Type} (le : α → α → Bool)
    (xs : List α) (p : α → Bool) :
    (sortBy le xs).any p = true ↔ xs.any p = true := by
  constructor
  · intro h
    obtain ⟨x, hx, hp⟩ := List.any_eq_true.mp h
    exact List.any_eq_true.mpr ⟨x, (mem_sortBy le xs x).mp hx, hp⟩
  · intro h
    obtain ⟨x, hx, hp⟩ := List.any_eq_true.mp h
    exact List.any_eq_true.mpr ⟨x, (mem_sortBy le xs x).mpr hx, hp⟩

theorem all_sortBy_iff {α : Type} (le : α → α → Bool)
    (xs : List α) (p : α → Bool) :
    (sortBy le xs).all p = true ↔ xs.all p = true := by
  constructor
  · intro h
    apply List.all_eq_true.mpr
    intro x hx
    exact List.all_eq_true.mp h x ((mem_sortBy le xs x).mpr hx)
  · intro h
    apply List.all_eq_true.mpr
    intro x hx
    exact List.all_eq_true.mp h x ((mem_sortBy le xs x).mp hx)

def literalLE (x y : Literal) : Bool :=
  decide (Witnora.SignedSerialization.encode x ≤
    Witnora.SignedSerialization.encode y)

def sortLiterals (clause : List Literal) : List Literal :=
  sortBy literalLE clause

def sortClauses (cnf : CNF) : CNF :=
  sortBy (fun x y => lexLE (x.map Witnora.SignedSerialization.encode)
    (y.map Witnora.SignedSerialization.encode)) cnf
where
  lexLE : List Int → List Int → Bool
    | [], _ => true
    | _ :: _, [] => false
    | x :: xs, y :: ys =>
        if x < y then true else if x == y then lexLE xs ys else false

theorem sortLiterals_correct (clause : List Literal) (a : Nat → Bool) :
    (sortLiterals clause).any (signedLitTrue a) =
      clause.any (signedLitTrue a) := by
  apply Bool.eq_iff_iff.mpr
  exact any_sortBy_iff literalLE clause (signedLitTrue a)

theorem sortClauses_correct (cnf : CNF) (a : Nat → Bool) :
    CNFHolds (sortClauses cnf) a ↔ CNFHolds cnf a := by
  unfold CNFHolds sortClauses
  exact all_sortBy_iff _ cnf (fun clause => clause.any (signedLitTrue a))

def canonicalize (cnf : CNF) : CNF :=
  sortClauses
    (dedupClauses
      (dropTautologies
        (cnf.map (fun clause => sortLiterals (dedup clause)))))

theorem canonicalize_correct (cnf : CNF) (a : Nat → Bool) :
    CNFHolds (canonicalize cnf) a ↔ CNFHolds cnf a := by
  unfold canonicalize
  rw [sortClauses_correct, dedupClauses_correct, dropTautologies_correct]
  unfold CNFHolds
  simp only [List.all_map]
  constructor
  · intro h
    apply List.all_eq_true.mpr
    intro clause hc
    have hd := (any_dedup_iff clause (signedLitTrue a)).mp
    have hs := sortLiterals_correct (dedup clause) a
    exact hd (by
      rw [← hs]
      exact List.all_eq_true.mp h clause hc)
  · intro h
    apply List.all_eq_true.mpr
    intro clause hc
    have hd := (any_dedup_iff clause (signedLitTrue a)).mpr
      (List.all_eq_true.mp h clause hc)
    change (sortLiterals (dedup clause)).any (signedLitTrue a) = true
    rw [sortLiterals_correct]
    exact hd

#print axioms Witnora.CNFSorted.mem_sortBy
#print axioms Witnora.CNFSorted.sortLiterals_correct
#print axioms Witnora.CNFSorted.canonicalize_correct

end Witnora.CNFSorted
