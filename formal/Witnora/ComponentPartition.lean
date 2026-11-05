import Witnora.Conditioning

/-!
# Exact residual-clause partition

A certificate can present residual components in arbitrary order. Rather
than trusting a claimed component count, the checker verifies the multiset
of all residual clauses (including duplicates and empty clauses) agrees
with the flattened component clauses.

The theorem relates this check to the satisfaction of the original CNF
after the certified separator assignment. The Python serialization and
component-construction refinement is still a separate proof obligation.
-/

namespace Witnora.ComponentPartition

open Witnora.Concrete
open Witnora.FiniteXor
open Witnora.G5Extraction
open Witnora.Conditioning

def checkPartition (residual : CNF) (components : List CNF) : Bool :=
  decide (List.Perm residual components.flatten)

theorem all_perm {α : Type} (p : α → Bool)
    {xs ys : List α} (h : List.Perm xs ys) :
    xs.all p = ys.all p := by
  induction h with
  | nil => rfl
  | cons _ _ ih => simp [List.all_cons, ih]
  | swap x y l =>
      simp [List.all_cons, Bool.and_comm, Bool.and_left_comm, Bool.and_assoc]
  | trans _ _ ih₁ ih₂ => exact ih₁.trans ih₂

theorem all_flatten {α : Type}
    (groups : List (List α)) (p : α → Bool) :
    groups.flatten.all p = groups.all (fun g => g.all p) := by
  induction groups with
  | nil => rfl
  | cons group rest ih =>
      simp [List.flatten, List.all_append, List.all_cons, ih]

theorem checkPartition_sound
    (residual : CNF) (components : List CNF)
    (h : checkPartition residual components = true)
    (a : Nat → Bool) :
    CNFHolds residual a ↔
      components.all (fun c => c.all (fun clause => clause.any (signedLitTrue a))) = true := by
  have hp : List.Perm residual components.flatten := by
    simpa [checkPartition] using h
  unfold CNFHolds
  rw [all_perm (fun clause => clause.any (signedLitTrue a)) hp]
  rw [all_flatten]

/-- Exact residual partition plus conditioning yields original-CNF semantics.
The assignment must extend the certified partial separator assignment. -/
theorem conditioned_partition_correct
    (fixed : Nat → Option Bool) (original : CNF)
    (components : List CNF)
    (hpart : checkPartition (conditionCNF fixed original) components = true)
    (a : Nat → Bool) (hag : agreesWith fixed a) :
    CNFHolds original a ↔
      components.all (fun c => c.all (fun clause => clause.any (signedLitTrue a))) = true := by
  rw [← conditionCNF_correct fixed a hag original]
  exact checkPartition_sound (conditionCNF fixed original) components hpart a

example :
    checkPartition [[(1, true)], [(2, false)]]
      [[[ (2, false) ]], [[(1, true)]]] = true := by decide

example :
    checkPartition [[(1, true)], [(2, false)]]
      [[[ (1, true) ]]] = false := by decide

example :
    checkPartition [[(1, true)], [(2, false)]]
      [[[ (1, true) ]], [[(2, false)], [(2, false)]]] = false := by decide

#print axioms Witnora.ComponentPartition.checkPartition_sound
#print axioms Witnora.ComponentPartition.conditioned_partition_correct

end Witnora.ComponentPartition
