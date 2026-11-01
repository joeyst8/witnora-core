import Witnora.ComponentPartition
import Witnora.CNFSorted
import Witnora.SeparatorAssignments

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

#print axioms Witnora.G14NormalizedPartition.conditioned_normalized_partition_models_iff

end Witnora.G14NormalizedPartition
