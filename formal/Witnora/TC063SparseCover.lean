import Witnora.TC063SparseDirectChecker
import Witnora.G14NormalizedPartition

/-!
# Source-bound G14 cover with bound-independent G5 certificates

The prior normalized G14 composition required a numeric bound for every
component's G5Closed checker.  This theorem uses a strictly sparse G5
checker at every branch.  It preserves the same exact source-document,
CNF-normalization and residual-partition premises; the finite maximum
variable ID appears only in the proof of sparse G5 soundness, not in
the executable certificate contract.
-/

namespace Witnora.TC063SparseCover

open Witnora.Concrete
open Witnora.G5Extraction
open Witnora.G14NormalizedPartition
open Witnora.ComponentPartition
open Witnora.Conditioning
open Witnora.TC063SparseDirectChecker

/-- Complete separator enumeration plus normalized residual partitions
    and one accepted sparse source-CNF G5 contradiction per branch
    prove UNSAT of the original signed CNF. -/
theorem signed_unsat_of_sparse_normalized_cover
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
    (rows : List (Nat × Bool) → List Witnora.G5Trace.Row)
    (steps : List (Nat × Bool) → List Witnora.G5Dag.XorRef)
    (hcert : ∀ branch ∈ Witnora.SeparatorAssignments.enumerate separator,
      checkSparseG5 (selected branch)
        (rows branch) (steps branch) = true) :
    ¬ ∃ a, Witnora.SignedSerialization.signedCNFHolds raw a := by
  intro ⟨a, ha⟩
  obtain ⟨branch, hb, hag⟩ :=
    Witnora.SeparatorAssignments.enumerate_covers_assignments separator a
  have hsource :
      CNFHolds (Witnora.SignedSerialization.decodeCNF raw) a :=
    (Witnora.SignedSerialization.signedCNFHolds_iff raw a).mp ha
  have hcomponents :=
    (conditioned_normalized_partition_models_iff
      (Witnora.SeparatorAssignments.fixedOf branch)
      (Witnora.SignedSerialization.decodeCNF raw)
      (components branch) (hpart branch hb) a hag).mp hsource
  have hchosen : CNFHolds (selected branch) a :=
    List.all_eq_true.mp hcomponents (selected branch)
      (hselected branch hb)
  exact (checkSparseG5_unsat
    (selected branch) (rows branch) (steps branch)
    (hcert branch hb)) ⟨a, hchosen⟩

/-- End-to-end source-byte theorem with exact DIMACS source/stream checks,
    normalized source equivalence, full G14 partition coverage and only
    bound-independent sparse per-branch G5 certificate checks. -/
theorem checked_ascii_dimacs_g14_canonical_sparse_unsat
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
    (rows : List (Nat × Bool) → List Witnora.G5Trace.Row)
    (steps : List (Nat × Bool) → List Witnora.G5Dag.XorRef)
    (hcert : ∀ branch ∈ Witnora.SeparatorAssignments.enumerate separator,
      checkSparseG5 (selected branch)
        (rows branch) (steps branch) = true) :
    Witnora.DIMACSDocument.parseDocument source =
      some (Witnora.DIMACSTokens.serialize raw) ∧
    ¬ ∃ a, Witnora.SignedSerialization.signedCNFHolds raw a := by
  constructor
  · have hd :=
      Witnora.DIMACSDocument.checkDocument_sound source tokens hdocument
    have hs := (Witnora.DIMACSTokens.checkStream_sound tokens raw hstream).1
    simpa [hs] using hd
  · have hun := signed_unsat_of_sparse_normalized_cover
      canonical separator components hpart selected hselected
      rows steps hcert
    intro ⟨a, ha⟩
    apply hun
    refine ⟨a,
      (Witnora.SignedSerialization.signedCNFHolds_iff canonical a).mpr ?_⟩
    rw [← hcanonical]
    apply (Witnora.CNFSorted.canonicalize_correct
      (Witnora.SignedSerialization.decodeCNF raw) a).mpr
    exact (Witnora.SignedSerialization.signedCNFHolds_iff raw a).mp ha

#print axioms Witnora.TC063SparseCover.signed_unsat_of_sparse_normalized_cover
#print axioms Witnora.TC063SparseCover.checked_ascii_dimacs_g14_canonical_sparse_unsat

end Witnora.TC063SparseCover
