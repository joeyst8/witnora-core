import Witnora.G5Extraction

/-!
# Semantic safety of removing repeated literals and repeated CNF clauses

This is a foundational part of CNF canonicalization. Tautological-clause
elimination and deterministic sorting are separate subsequent obligations.
-/

namespace Witnora.CNFCanonical

open Witnora.Concrete
open Witnora.FiniteXor
open Witnora.G5Extraction

theorem any_eraseDups_iff {α : Type} [DecidableEq α]
    (xs : List α) (p : α → Bool) :
    (xs.eraseDups.any p = true) ↔ (xs.any p = true) := by
  constructor
  · intro h
    obtain ⟨x, hx, hp⟩ := List.any_eq_true.mp h
    apply List.any_eq_true.mpr
    exact ⟨x, by simpa only [List.mem_eraseDups] using hx, hp⟩
  · intro h
    obtain ⟨x, hx, hp⟩ := List.any_eq_true.mp h
    apply List.any_eq_true.mpr
    exact ⟨x, by simpa only [List.mem_eraseDups] using hx, hp⟩

theorem all_eraseDups_iff {α : Type} [DecidableEq α]
    (xs : List α) (p : α → Bool) :
    (xs.eraseDups.all p = true) ↔ (xs.all p = true) := by
  constructor
  · intro h
    apply List.all_eq_true.mpr
    intro x hx
    exact List.all_eq_true.mp h x (by simpa only [List.mem_eraseDups] using hx)
  · intro h
    apply List.all_eq_true.mpr
    intro x hx
    exact List.all_eq_true.mp h x (by simpa only [List.mem_eraseDups] using hx)

def dedupLiterals (cnf : CNF) : CNF :=
  cnf.map List.eraseDups

def dedupClauses (cnf : CNF) : CNF :=
  cnf.eraseDups

theorem dedupLiterals_correct (cnf : CNF) (a : Nat → Bool) :
    CNFHolds (dedupLiterals cnf) a ↔ CNFHolds cnf a := by
  unfold CNFHolds dedupLiterals
  simp only [List.all_map]
  constructor
  · intro h
    apply List.all_eq_true.mpr
    intro clause hc
    exact (any_eraseDups_iff clause (signedLitTrue a)).mp
      (List.all_eq_true.mp h clause hc)
  · intro h
    apply List.all_eq_true.mpr
    intro clause hc
    exact (any_eraseDups_iff clause (signedLitTrue a)).mpr
      (List.all_eq_true.mp h clause hc)

theorem dedupClauses_correct (cnf : CNF) (a : Nat → Bool) :
    CNFHolds (dedupClauses cnf) a ↔ CNFHolds cnf a := by
  change (cnf.eraseDups.all (fun clause => clause.any (signedLitTrue a)) = true) ↔
    (cnf.all (fun clause => clause.any (signedLitTrue a)) = true)
  exact all_eraseDups_iff cnf (fun clause => clause.any (signedLitTrue a))

#print axioms Witnora.CNFCanonical.dedupLiterals_correct
#print axioms Witnora.CNFCanonical.dedupClauses_correct

end Witnora.CNFCanonical
