import Witnora.G14DFSOwnerLabels

/-!
# G14 DFS-derived normalized residual model bridge

The verified outer scan provides real residual components and edge-consistent
numeric labels.  We derive a *total* clause-routing construction from those
labels.  An explicit overflow bucket catches empty or otherwise nonstandard
residual clauses rather than silently dropping them.  This construction
satisfies the existing normalized partition checker for every input CNF and
separator assignment.

The construction is a mathematical Lean model.  Equality with the concrete
Python component sorting and dictionary construction remains to be proved.
-/

namespace Witnora.G14DFSModelBridge

open Witnora.Concrete
open Witnora.FiniteXor
open Witnora.G5Extraction
open Witnora.Conditioning
open Witnora.G14DFSOwnerLabels
open Witnora.G14ComponentRouting
open Witnora.G14NormalizedPartition

/-- Missing vertices receive precisely the one-past-end sentinel index.
    Even without coverage assumptions this index never exceeds the length. -/
theorem componentIndex_le_length
    (components : List (List Nat)) (v : Nat) :
    componentIndex components v ≤ components.length := by
  induction components with
  | nil => simp [componentIndex]
  | cons component rest ih =>
      by_cases hv : v ∈ component
      · simp [componentIndex, hv]
      · simpa [componentIndex, hv] using Nat.succ_le_succ ih

/-- A nonempty residual clause is routed by its first variable. Empty
    residual clauses go to the one-past-end bucket to preserve UNSAT. -/
def residualClauseOwner (components : List (List Nat)) :
    List Literal → Nat
  | [] => components.length
  | lit :: _ => componentIndex components lit.1

/-- All genuine component indices plus a final contradiction/overflow
    bucket, so no clause is silently discarded even on unusual input. -/
def componentIds (components : List (List Nat)) : List Nat :=
  List.range (components.length + 1)

theorem residualClauseOwner_covered
    (components : List (List Nat)) (clauses : CNF) :
    OwnersCovered (residualClauseOwner components)
      (componentIds components) clauses := by
  intro clause _
  have hBound :
      residualClauseOwner components clause < components.length + 1 := by
    cases clause with
    | nil =>
        simp [residualClauseOwner]
    | cons lit tail =>
        simpa [residualClauseOwner] using
          Nat.lt_succ_of_le (componentIndex_le_length components lit.1)
  change residualClauseOwner components clause ∈
    List.range (components.length + 1)
  exact List.mem_range.mpr hBound

/-- A fully specified, certificate-checkable G14 normalized partition
    obtained from the verified DFS component list, with a final bucket
    for clauses that do not have an ordinary component owner. -/
def dfsRoutedComponents (source : CNF) (separator : List Nat)
    (fixed : Nat → Option Bool) : List CNF :=
  let components := rawResidualComponents source separator
  routeClauses (residualClauseOwner components) (componentIds components)
    (Witnora.CNFSorted.canonicalize (conditionCNF fixed source))

theorem dfs_routed_partition_check_passes
    (source : CNF) (separator : List Nat)
    (fixed : Nat → Option Bool) :
    checkNormalizedPartition (conditionCNF fixed source)
      (dfsRoutedComponents source separator fixed) = true := by
  unfold dfsRoutedComponents checkNormalizedPartition
  exact routed_partition_check_passes
    (residualClauseOwner (rawResidualComponents source separator))
    (componentIds (rawResidualComponents source separator))
    (Witnora.CNFSorted.canonicalize (conditionCNF fixed source))
    (residualClauseOwner_covered
      (rawResidualComponents source separator)
      (Witnora.CNFSorted.canonicalize (conditionCNF fixed source)))

/-- Exact model correspondence between the original source and all
    automatically routed residual buckets, for each total assignment
    agreeing with the separator branch. No external partition hypothesis. -/
theorem dfs_routed_source_models_iff
    (source : CNF) (separator : List Nat)
    (fixed : Nat → Option Bool) (a : Nat → Bool)
    (hagrees : agreesWith fixed a) :
    CNFHolds source a ↔
      (dfsRoutedComponents source separator fixed).all
        (fun c => c.all (fun clause => clause.any (signedLitTrue a))) =
          true := by
  exact conditioned_normalized_partition_models_iff
    fixed source (dfsRoutedComponents source separator fixed)
    (dfs_routed_partition_check_passes source separator fixed)
    a hagrees

/-- Given one verified G5 contradiction in a selected bucket of each
    separator branch, global unsatisfiability follows.  The previous
    external per-branch residual-partition premise is now discharged
    by construction; selected-bucket membership and G5 witnesses remain. -/
theorem signed_unsat_of_dfs_routed_g5_certificates
    (raw : List (List Int)) (separator : List Nat)
    (selected : List (Nat × Bool) → CNF)
    (hselected : ∀ branch ∈ Witnora.SeparatorAssignments.enumerate separator,
      selected branch ∈ dfsRoutedComponents
        (Witnora.SignedSerialization.decodeCNF raw)
        separator (Witnora.SeparatorAssignments.fixedOf branch))
    (bound : List (Nat × Bool) → Nat)
    (rows : List (Nat × Bool) → List Witnora.G5Trace.Row)
    (steps : List (Nat × Bool) → List Witnora.G5Dag.XorRef)
    (hcert : ∀ branch ∈ Witnora.SeparatorAssignments.enumerate separator,
      Witnora.SparseBridge.checkG5Closed
        (bound branch) (selected branch)
        (rows branch) (steps branch) = true) :
    ¬ ∃ a, Witnora.SignedSerialization.signedCNFHolds raw a := by
  exact signed_unsat_of_normalized_enumerated_partitions
    raw separator
    (fun branch => dfsRoutedComponents
      (Witnora.SignedSerialization.decodeCNF raw)
      separator (Witnora.SeparatorAssignments.fixedOf branch))
    (by
      intro branch _
      exact dfs_routed_partition_check_passes
        (Witnora.SignedSerialization.decodeCNF raw)
        separator (Witnora.SeparatorAssignments.fixedOf branch))
    selected hselected bound rows steps hcert

#print axioms Witnora.G14DFSModelBridge.dfs_routed_partition_check_passes
#print axioms Witnora.G14DFSModelBridge.dfs_routed_source_models_iff
#print axioms Witnora.G14DFSModelBridge.signed_unsat_of_dfs_routed_g5_certificates

end Witnora.G14DFSModelBridge
