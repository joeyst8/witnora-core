import Witnora.SparseBridge
import Witnora.SignedSerialization

/-!
# Source-subset G5 UNSAT bridge

An exact affine CNF extracted from the original source need not cover every
original clause when non-affine clauses are present. Soundness requires two
independent checks:
  1. Every extracted clause occurs in the entire source CNF.
  2. The extracted CNF has a kernel-checked G5 contradiction certificate.

This theorem is universal for arbitrary CNFs, not limited to our fixtures.
It proves only the semantic implication; the concrete extraction and DIMACS
normalization must still be checked at the source boundary.
-/

namespace Witnora.SourceSubsetG5

open Witnora.Concrete
open Witnora.G5Trace
open Witnora.G5Dag
open Witnora.G5Extraction

def checkSourceSubsetG5 (bound : Nat) (source subset : CNF)
    (rows : List Row) (steps : List XorRef) : Bool :=
  subset.all (fun clause => decide (clause ∈ source)) &&
    Witnora.SparseBridge.checkG5Closed bound subset rows steps

theorem checkSourceSubsetG5_unsat
    (bound : Nat) (source subset : CNF)
    (rows : List Row) (steps : List XorRef)
    (h : checkSourceSubsetG5 bound source subset rows steps = true) :
    ¬ ∃ a, CNFHolds source a := by
  have hs : subset.all (fun clause => decide (clause ∈ source)) = true :=
    (Bool.and_eq_true.mp h).1
  have hc : Witnora.SparseBridge.checkG5Closed bound subset rows steps = true :=
    (Bool.and_eq_true.mp h).2
  have hi : ∀ clause, clause ∈ subset → clause ∈ source := by
    intro clause hmem
    have hm := List.all_eq_true.mp hs clause hmem
    simpa only [decide_eq_true_eq] using hm
  have hunsat := Witnora.SparseBridge.checkG5Closed_unsat
    bound subset rows steps hc
  intro ⟨a, hsource⟩
  apply hunsat
  refine ⟨a, ?_⟩
  unfold CNFHolds at hsource ⊢
  apply List.all_eq_true.mpr
  intro clause hmem
  exact List.all_eq_true.mp hsource clause (hi clause hmem)

example :
    checkSourceSubsetG5 3
      [[(1, true)], [(1, false)], [(2, true)]]
      [[(1, true)], [(1, false)]]
      [⟨[1], true⟩, ⟨[1], false⟩]
      [(0, 1)] = true := by decide

example :
    checkSourceSubsetG5 3
      [[(1, true)], [(2, true)]]
      [[(1, true)], [(1, false)]]
      [⟨[1], true⟩, ⟨[1], false⟩]
      [(0, 1)] = false := by decide

#print axioms Witnora.SourceSubsetG5.checkSourceSubsetG5_unsat

end Witnora.SourceSubsetG5
