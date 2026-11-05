import Witnora.ComponentPartition
import Witnora.SeparatorAssignments
import Witnora.SourceG5
import Witnora.DIMACSDocument
import Witnora.DIMACSTokens
import Witnora.CNFSorted

/-!
# Concrete source-CNF / G14 residual partition / G5 soundness

This route avoids an assumed abstract G14 residual-model transfer:
a successful checked partition of each conditioned original CNF *implies*
that every model of the original formula models every listed residual
component (for assignments extending the selected separator branch).

The remaining external obligation is that the supplied finite branch
assignments cover all total assignments. Certificates need only be supplied
for branches in that list. A finite separator enumeration can discharge
the branch-coverage obligation; Python's component construction does not
become a theorem merely by producing a certificate.
-/

namespace Witnora.G14ConcreteBridge

open Witnora.Concrete
open Witnora.Conditioning
open Witnora.ComponentPartition
open Witnora.SignedSerialization
open Witnora.G5Extraction
open Witnora.SparseBridge

/-- No abstract decomposition or residual-model lift is assumed: partition
    checking and conditioning explicitly establish the model transfer. -/
theorem signed_unsat_of_checked_conditioned_partitions
    {Branch : Type}
    (raw : List (List Int))
    (branches : List Branch)
    (fixed : Branch → Nat → Option Bool)
    (hcover : ∀ a : Nat → Bool,
      ∃ branch ∈ branches, agreesWith (fixed branch) a)
    (components : Branch → List Witnora.Concrete.CNF)
    (hpart : ∀ branch ∈ branches,
      checkPartition
        (conditionCNF (fixed branch) (decodeCNF raw))
        (components branch) = true)
    (selected : Branch → Witnora.Concrete.CNF)
    (hselected : ∀ branch ∈ branches,
      selected branch ∈ components branch)
    (bound : Branch → Nat)
    (rows : Branch → List Witnora.G5Trace.Row)
    (steps : Branch → List Witnora.G5Dag.XorRef)
    (hcert : ∀ branch ∈ branches,
      checkG5Closed (bound branch) (selected branch)
        (rows branch) (steps branch) = true) :
    ¬ ∃ a, signedCNFHolds raw a := by
  intro ⟨a, ha⟩
  obtain ⟨branch, hb, hag⟩ := hcover a
  have horiginal : CNFHolds (decodeCNF raw) a :=
    (signedCNFHolds_iff raw a).mp ha
  have hcomponents :=
    (conditioned_partition_correct (fixed branch) (decodeCNF raw)
      (components branch) (hpart branch hb) a hag).mp horiginal
  have hchosen : CNFHolds (selected branch) a := by
    exact List.all_eq_true.mp hcomponents (selected branch)
      (hselected branch hb)
  have hun := checkG5Closed_unsat (bound branch) (selected branch)
    (rows branch) (steps branch) (hcert branch hb)
  exact hun ⟨a, hchosen⟩


/-- Concrete finite-branch theorem: the separator coverage assumption is
    discharged by the kernel-proved Boolean assignment enumeration. -/
theorem signed_unsat_of_enumerated_partitions
    (raw : List (List Int))
    (separator : List Nat)
    (components : List (Nat × Bool) → List Witnora.Concrete.CNF)
    (hpart : ∀ branch ∈ Witnora.SeparatorAssignments.enumerate separator,
      checkPartition
        (conditionCNF (Witnora.SeparatorAssignments.fixedOf branch)
          (decodeCNF raw))
        (components branch) = true)
    (selected : List (Nat × Bool) → Witnora.Concrete.CNF)
    (hselected : ∀ branch ∈ Witnora.SeparatorAssignments.enumerate separator,
      selected branch ∈ components branch)
    (bound : List (Nat × Bool) → Nat)
    (rows : List (Nat × Bool) → List Witnora.G5Trace.Row)
    (steps : List (Nat × Bool) → List Witnora.G5Dag.XorRef)
    (hcert : ∀ branch ∈ Witnora.SeparatorAssignments.enumerate separator,
      checkG5Closed (bound branch) (selected branch)
        (rows branch) (steps branch) = true) :
    ¬ ∃ a, signedCNFHolds raw a := by
  exact signed_unsat_of_checked_conditioned_partitions
    raw (Witnora.SeparatorAssignments.enumerate separator)
    Witnora.SeparatorAssignments.fixedOf
    (Witnora.SeparatorAssignments.enumerate_covers_assignments separator)
    components hpart selected hselected bound rows steps hcert

#print axioms Witnora.G14ConcreteBridge.signed_unsat_of_enumerated_partitions


/-- Source document -> exact signed clauses -> checked G14 partition ->
    G5 contradiction for each branch -> UNSAT. Every premise is explicit.
    This is a conditional theorem about accepted artifacts, not a proof
    that arbitrary Python runs produce accepted artifacts. -/
theorem checked_ascii_dimacs_g14_unsat
    (source : List Nat) (tokens : List Int) (raw : List (List Int))
    (hdocument : Witnora.DIMACSDocument.checkDocument source tokens = true)
    (hstream : Witnora.DIMACSTokens.checkStream tokens raw = true)
    (separator : List Nat)
    (components : List (Nat × Bool) → List Witnora.Concrete.CNF)
    (hpart : ∀ branch ∈ Witnora.SeparatorAssignments.enumerate separator,
      checkPartition
        (conditionCNF (Witnora.SeparatorAssignments.fixedOf branch)
          (decodeCNF raw))
        (components branch) = true)
    (selected : List (Nat × Bool) → Witnora.Concrete.CNF)
    (hselected : ∀ branch ∈ Witnora.SeparatorAssignments.enumerate separator,
      selected branch ∈ components branch)
    (bound : List (Nat × Bool) → Nat)
    (rows : List (Nat × Bool) → List Witnora.G5Trace.Row)
    (steps : List (Nat × Bool) → List Witnora.G5Dag.XorRef)
    (hcert : ∀ branch ∈ Witnora.SeparatorAssignments.enumerate separator,
      checkG5Closed (bound branch) (selected branch)
        (rows branch) (steps branch) = true) :
    Witnora.DIMACSDocument.parseDocument source =
      some (Witnora.DIMACSTokens.serialize raw) ∧
    ¬ ∃ a, signedCNFHolds raw a := by
  constructor
  · have hd := Witnora.DIMACSDocument.checkDocument_sound source tokens hdocument
    have hs := (Witnora.DIMACSTokens.checkStream_sound tokens raw hstream).1
    simpa [hs] using hd
  · exact signed_unsat_of_enumerated_partitions raw separator components
      hpart selected hselected bound rows steps hcert

#print axioms Witnora.G14ConcreteBridge.checked_ascii_dimacs_g14_unsat


/-- Production-oriented theorem: the source clauses need not be canonical.
    Lean checks their canonicalization before transferring a model into
    the exact checked residual partitions. -/
theorem checked_ascii_dimacs_g14_canonical_unsat
    (source : List Nat) (tokens : List Int)
    (raw canonical : List (List Int))
    (hdocument : Witnora.DIMACSDocument.checkDocument source tokens = true)
    (hstream : Witnora.DIMACSTokens.checkStream tokens raw = true)
    (hcanonical : Witnora.CNFSorted.canonicalize (decodeCNF raw) =
      decodeCNF canonical)
    (separator : List Nat)
    (components : List (Nat × Bool) → List Witnora.Concrete.CNF)
    (hpart : ∀ branch ∈ Witnora.SeparatorAssignments.enumerate separator,
      checkPartition
        (conditionCNF (Witnora.SeparatorAssignments.fixedOf branch)
          (decodeCNF canonical))
        (components branch) = true)
    (selected : List (Nat × Bool) → Witnora.Concrete.CNF)
    (hselected : ∀ branch ∈ Witnora.SeparatorAssignments.enumerate separator,
      selected branch ∈ components branch)
    (bound : List (Nat × Bool) → Nat)
    (rows : List (Nat × Bool) → List Witnora.G5Trace.Row)
    (steps : List (Nat × Bool) → List Witnora.G5Dag.XorRef)
    (hcert : ∀ branch ∈ Witnora.SeparatorAssignments.enumerate separator,
      checkG5Closed (bound branch) (selected branch)
        (rows branch) (steps branch) = true) :
    Witnora.DIMACSDocument.parseDocument source =
      some (Witnora.DIMACSTokens.serialize raw) ∧
    ¬ ∃ a, signedCNFHolds raw a := by
  constructor
  · have hd := Witnora.DIMACSDocument.checkDocument_sound source tokens hdocument
    have hs := (Witnora.DIMACSTokens.checkStream_sound tokens raw hstream).1
    simpa [hs] using hd
  · have hun := signed_unsat_of_enumerated_partitions canonical separator
      components hpart selected hselected bound rows steps hcert
    intro ⟨a, ha⟩
    apply hun
    refine ⟨a, (signedCNFHolds_iff canonical a).mpr ?_⟩
    rw [← hcanonical]
    apply (Witnora.CNFSorted.canonicalize_correct (decodeCNF raw) a).mpr
    exact (signedCNFHolds_iff raw a).mp ha

#print axioms Witnora.G14ConcreteBridge.checked_ascii_dimacs_g14_canonical_unsat

#print axioms Witnora.G14ConcreteBridge.signed_unsat_of_checked_conditioned_partitions

end Witnora.G14ConcreteBridge
