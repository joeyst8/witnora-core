import Witnora.SparseBridge
import Witnora.SignedSerialization
import Witnora.DIMACSDocument
import Witnora.DIMACSTokens
import Witnora.CNFSorted

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
  have hsplit := h
  simp [checkSourceSubsetG5] at hsplit
  have hi : ∀ clause, clause ∈ subset → clause ∈ source :=
    hsplit.1
  have hc : Witnora.SparseBridge.checkG5Closed bound subset rows steps = true :=
    hsplit.2
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

/-- Exact original ASCII DIMACS source -> canonical CNF -> contained G5
    contradiction, all checked by one Lean proof. -/
theorem checked_ascii_dimacs_source_subset_g5_unsat
    (sourceBytes : List Nat) (tokens : List Int)
    (raw canonical : List (List Int))
    (hdocument : Witnora.DIMACSDocument.checkDocument sourceBytes tokens = true)
    (hstream : Witnora.DIMACSTokens.checkStream tokens raw = true)
    (hcanonical : Witnora.CNFSorted.canonicalize
        (Witnora.SignedSerialization.decodeCNF raw) =
      Witnora.SignedSerialization.decodeCNF canonical)
    (bound : Nat) (subset : CNF) (rows : List Row) (steps : List XorRef)
    (hsubset : checkSourceSubsetG5 bound
        (Witnora.SignedSerialization.decodeCNF canonical)
        subset rows steps = true) :
    Witnora.DIMACSDocument.parseDocument sourceBytes =
      some (Witnora.DIMACSTokens.serialize raw) ∧
    ¬ ∃ a, Witnora.SignedSerialization.signedCNFHolds raw a := by
  constructor
  · have hd :=
      Witnora.DIMACSDocument.checkDocument_sound sourceBytes tokens hdocument
    have hs :=
      (Witnora.DIMACSTokens.checkStream_sound tokens raw hstream).1
    simpa [hs] using hd
  · have hun := checkSourceSubsetG5_unsat bound
      (Witnora.SignedSerialization.decodeCNF canonical)
      subset rows steps hsubset
    intro ⟨a, ha⟩
    apply hun
    refine ⟨a, ?_⟩
    rw [← hcanonical]
    apply (Witnora.CNFSorted.canonicalize_correct
      (Witnora.SignedSerialization.decodeCNF raw) a).mpr
    exact (Witnora.SignedSerialization.signedCNFHolds_iff raw a).mp ha

#print axioms Witnora.SourceSubsetG5.checked_ascii_dimacs_source_subset_g5_unsat

#print axioms Witnora.SourceSubsetG5.checkSourceSubsetG5_unsat

end Witnora.SourceSubsetG5
