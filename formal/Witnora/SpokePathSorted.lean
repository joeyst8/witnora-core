import Witnora.SpokePathIndexed

/-!
# Sorted-vector certificate for indexed spoke paths

Both the deduplicated source-derived join list and the reported list are
sorted using the same total lexicographic ordering and compared once.
Membership preservation is kernel-proved, so acceptance cannot fabricate
or omit any path. The old independent exact-set checker remains available.
-/

namespace Witnora.SpokePathSorted

open Witnora.BinaryXorDiscovery
open Witnora.SpokePathDiscovery
open Witnora.SpokePathIndexed

def bit (b : Bool) : Nat := if b then 1 else 0

def pathLe (a b : Path) : Bool :=
  decide (a.x < b.x ∨
    (a.x = b.x ∧ (a.z < b.z ∨
      (a.z = b.z ∧ (a.middle < b.middle ∨
        (a.middle = b.middle ∧ (bit a.left < bit b.left ∨
          (bit a.left = bit b.left ∧ bit a.right ≤ bit b.right))))))))

/-- Structurally recursive insertion avoids well-founded merge-sort
    reductions getting stuck in closed kernel computations. -/
def insertSorted (p : Path) : List Path → List Path
  | [] => [p]
  | q :: qs =>
      if pathLe p q then p :: q :: qs
      else q :: insertSorted p qs

def normalize : List Path → List Path
  | [] => []
  | p :: ps => insertSorted p (normalize ps)

theorem mem_insertSorted (p q : Path) (xs : List Path) :
    p ∈ insertSorted q xs ↔ p = q ∨ p ∈ xs := by
  induction xs with
  | nil => simp [insertSorted]
  | cons x xs ih =>
      cases hqx : pathLe q x <;>
        simp [insertSorted, hqx, ih, or_assoc, or_left_comm, or_comm]

theorem mem_normalize (p : Path) (xs : List Path) :
    p ∈ normalize xs ↔ p ∈ xs := by
  induction xs with
  | nil => simp [normalize]
  | cons x xs ih =>
      simp [normalize, mem_insertSorted, ih, or_assoc, or_left_comm, or_comm]

def checkSorted (edges : List Equation) (reported : List Path) : Bool :=
  decide (normalize (uniqueJoins edges) = normalize reported) &&
  decide reported.Nodup

theorem checkSorted_mem_iff
    (edges : List Equation) (reported : List Path)
    (h : checkSorted edges reported = true) (p : Path) :
    p ∈ reported ↔ p ∈ uniqueJoins edges := by
  have heq : normalize (uniqueJoins edges) = normalize reported := by
    have hh : decide (normalize (uniqueJoins edges) = normalize reported) = true ∧
        decide reported.Nodup = true := by
      simpa only [checkSorted, Bool.and_eq_true] using h
    simpa using hh.1
  constructor
  · intro hp
    have hm : p ∈ normalize reported :=
      (mem_normalize p reported).mpr hp
    rw [← heq] at hm
    exact (mem_normalize p (uniqueJoins edges)).mp hm
  · intro hp
    have hm : p ∈ normalize (uniqueJoins edges) :=
      (mem_normalize p (uniqueJoins edges)).mpr hp
    rw [heq] at hm
    exact (mem_normalize p reported).mp hm

/-- The fast sorted checker implies the original complete indexed check. -/
theorem checkSorted_implies_exact
    (edges : List Equation) (reported : List Path)
    (h : checkSorted edges reported = true) :
    checkExact edges reported = true := by
  have hnodup : reported.Nodup := by
    have hh : decide (normalize (uniqueJoins edges) = normalize reported) = true ∧
        decide reported.Nodup = true := by
      simpa only [checkSorted, Bool.and_eq_true] using h
    simpa using hh.2
  simp only [checkExact, Bool.and_eq_true]
  constructor
  · constructor
    · apply List.all_eq_true.mpr
      intro p hp
      have hm := (checkSorted_mem_iff edges reported h p).mp hp
      simpa using hm
    · apply List.all_eq_true.mpr
      intro p hp
      have hm := (checkSorted_mem_iff edges reported h p).mpr hp
      simpa using hm
  · simpa using hnodup

example :
    checkSorted
      [⟨1, 2, false⟩, ⟨2, 3, true⟩]
      [⟨1, 3, 2, false, true⟩] = true := by decide

example :
    checkSorted [⟨1, 2, false⟩, ⟨2, 3, true⟩] [] = false := by decide

example :
    checkSorted
      [⟨1, 2, false⟩, ⟨2, 3, true⟩]
      [⟨1, 3, 2, true, true⟩] = false := by decide

#print axioms Witnora.SpokePathSorted.checkSorted_implies_exact

end Witnora.SpokePathSorted
