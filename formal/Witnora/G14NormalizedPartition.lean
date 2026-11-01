import Witnora.ComponentPartition
import Witnora.CNFSorted
import Witnora.SeparatorAssignments
import Witnora.G14ConcreteBridge

/-!
# Sound G14 partition checking after canonical CNF normalization

Python CNFFormula deduplicates clauses after conditioning. Lean's raw
conditionCNF intentionally preserves duplicate clauses, so an exact
multiset check on the unnormalized residual can reject correct Python
output. Canonicalization removes this representation mismatch while
preserving model semantics. A partition must still contain every
canonical residual clause exactly once.
-/

namespace Witnora.G14NormalizedPartition

open Witnora.Concrete
open Witnora.FiniteXor
open Witnora.G5Extraction
open Witnora.Conditioning
open Witnora.ComponentPartition

def checkNormalizedPartition (residual : CNF)
    (components : List CNF) : Bool :=
  checkPartition (Witnora.CNFSorted.canonicalize residual) components

theorem normalized_partition_models_iff
    (residual : CNF) (components : List CNF)
    (h : checkNormalizedPartition residual components = true)
    (a : Nat → Bool) :
    CNFHolds residual a ↔
      components.all (fun c =>
        c.all (fun clause => clause.any (signedLitTrue a))) = true := by
  have hpart :
      checkPartition (Witnora.CNFSorted.canonicalize residual)
        components = true := h
  exact (Witnora.CNFSorted.canonicalize_correct residual a).symm.trans
    (checkPartition_sound
      (Witnora.CNFSorted.canonicalize residual)
      components hpart a)

/-- A Python-normalized, complete residual partition still preserves
    all and only the original CNF models extending the chosen branch. -/
theorem conditioned_normalized_partition_models_iff
    (fixed : Nat → Option Bool) (original : CNF)
    (components : List CNF)
    (h : checkNormalizedPartition (conditionCNF fixed original)
      components = true)
    (a : Nat → Bool) (hag : agreesWith fixed a) :
    CNFHolds original a ↔
      components.all (fun c =>
        c.all (fun clause => clause.any (signedLitTrue a))) = true := by
  exact (conditionCNF_correct fixed a hag original).symm.trans
    (normalized_partition_models_iff
      (conditionCNF fixed original) components h a)

/-- Raw conditioning generates duplicate [] clauses here. Python
    normalizes them to a single []; the sound normalized checker accepts. -/
example :
    checkNormalizedPartition
      (conditionCNF
        (Witnora.SeparatorAssignments.fixedOf [(1, false), (2, false)])
        [[(1, true)], [(2, true)]])
      [[[]]] = true := by decide

/-- Deleting even that one canonical contradiction is rejected. -/
example :
    checkNormalizedPartition
      (conditionCNF
        (Witnora.SeparatorAssignments.fixedOf [(1, false), (2, false)])
        [[(1, true)], [(2, true)]])
      [[]] = false := by decide

 
/-- Complete normalized G14 UNSAT cover. The separator enumeration,
    normalization semantics, and each branch's selected G5 contradiction
    are all checked, with no Python correctness assumption. -/
theorem signed_unsat_of_normalized_enumerated_partitions
    (raw : List (List Int))
    (separator : List Nat)
    (components : List (Nat × Bool) → List CNF)
    (hpart : ∀ branch ∈ Witnora.SeparatorAssignments.enumerate separator,
      checkNormalizedPartition
        (conditionCNF (Witnora.SeparatorAssignments.fixedOf branch)
          (Witnora.SignedSerialization.decodeCNF raw))
        (components branch) = true)
    (selected : List (Nat × Bool) → CNF)
    (hselected : ∀ branch ∈ Witnora.SeparatorAssignments.enumerate separator,
      selected branch ∈ components branch)
    (bound : List (Nat × Bool) → Nat)
    (rows : List (Nat × Bool) → List Witnora.G5Trace.Row)
    (steps : List (Nat × Bool) → List Witnora.G5Dag.XorRef)
    (hcert : ∀ branch ∈ Witnora.SeparatorAssignments.enumerate separator,
      Witnora.SparseBridge.checkG5Closed
        (bound branch) (selected branch)
        (rows branch) (steps branch) = true) :
    ¬ ∃ a, Witnora.SignedSerialization.signedCNFHolds raw a := by
  intro ⟨a, ha⟩
  obtain ⟨branch, hb, hag⟩ :=
    Witnora.SeparatorAssignments.enumerate_covers_assignments separator a
  have hsource : CNFHolds
      (Witnora.SignedSerialization.decodeCNF raw) a :=
    (Witnora.SignedSerialization.signedCNFHolds_iff raw a).mp ha
  have hcomponents :=
    (conditioned_normalized_partition_models_iff
      (Witnora.SeparatorAssignments.fixedOf branch)
      (Witnora.SignedSerialization.decodeCNF raw)
      (components branch) (hpart branch hb) a hag).mp hsource
  have hchosen : CNFHolds (selected branch) a := by
    exact List.all_eq_true.mp hcomponents (selected branch)
      (hselected branch hb)
  exact (Witnora.SparseBridge.checkG5Closed_unsat
    (bound branch) (selected branch) (rows branch) (steps branch)
    (hcert branch hb)) ⟨a, hchosen⟩

/-- Production end-to-end theorem allowing Python's canonical residual
    clause deduplication, but still requiring exact checked source bytes,
    canonical source equivalence, complete branch coverage, and accepted
    G5 certificates for the selected component of every branch. -/
theorem checked_ascii_dimacs_g14_canonical_normalized_unsat
    (source : List Nat) (tokens : List Int)
    (raw canonical : List (List Int))
    (hdocument : Witnora.DIMACSDocument.checkDocument source tokens = true)
    (hstream : Witnora.DIMACSTokens.checkStream tokens raw = true)
    (hcanonical : Witnora.CNFSorted.canonicalize
        (Witnora.SignedSerialization.decodeCNF raw) =
      Witnora.SignedSerialization.decodeCNF canonical)
    (separator : List Nat)
    (components : List (Nat × Bool) → List CNF)
    (hpart : ∀ branch ∈ Witnora.SeparatorAssignments.enumerate separator,
      checkNormalizedPartition
        (conditionCNF (Witnora.SeparatorAssignments.fixedOf branch)
          (Witnora.SignedSerialization.decodeCNF canonical))
        (components branch) = true)
    (selected : List (Nat × Bool) → CNF)
    (hselected : ∀ branch ∈ Witnora.SeparatorAssignments.enumerate separator,
      selected branch ∈ components branch)
    (bound : List (Nat × Bool) → Nat)
    (rows : List (Nat × Bool) → List Witnora.G5Trace.Row)
    (steps : List (Nat × Bool) → List Witnora.G5Dag.XorRef)
    (hcert : ∀ branch ∈ Witnora.SeparatorAssignments.enumerate separator,
      Witnora.SparseBridge.checkG5Closed
        (bound branch) (selected branch)
        (rows branch) (steps branch) = true) :
    Witnora.DIMACSDocument.parseDocument source =
      some (Witnora.DIMACSTokens.serialize raw) ∧
    ¬ ∃ a, Witnora.SignedSerialization.signedCNFHolds raw a := by
  constructor
  · have hd :=
      Witnora.DIMACSDocument.checkDocument_sound source tokens hdocument
    have hs :=
      (Witnora.DIMACSTokens.checkStream_sound tokens raw hstream).1
    simpa [hs] using hd
  · have hun := signed_unsat_of_normalized_enumerated_partitions
      canonical separator components hpart selected hselected
      bound rows steps hcert
    intro ⟨a, ha⟩
    apply hun
    refine ⟨a,
      (Witnora.SignedSerialization.signedCNFHolds_iff canonical a).mpr ?_⟩
    rw [← hcanonical]
    apply (Witnora.CNFSorted.canonicalize_correct
      (Witnora.SignedSerialization.decodeCNF raw) a).mpr
    exact (Witnora.SignedSerialization.signedCNFHolds_iff raw a).mp ha

#print axioms Witnora.G14NormalizedPartition.checked_ascii_dimacs_g14_canonical_normalized_unsat

#print axioms Witnora.G14NormalizedPartition.conditioned_normalized_partition_models_iff

end Witnora.G14NormalizedPartition
