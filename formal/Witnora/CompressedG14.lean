import Witnora.ParityResidual
import Witnora.G14ConcreteBridge
import Witnora.SignedSerialization

/-!
# Root-offset compression composed with complete G14 branch coverage

Every input used by the G14 checker is an explicit premise. The G14
partition/selected-component/G5 checks must hold for the exact rewritten
signed CNF, and root paths must be valid in the original source CNF.
-/

namespace Witnora.CompressedG14

open Witnora.Concrete
open Witnora.G5Extraction
open Witnora.ParityCompression
open Witnora.ParityResidual
open Witnora.SignedSerialization

theorem residual_g14_implies_original_unsat
    (cnf : CNF) (rootOf : Nat → Nat) (offset : Nat → Bool)
    (paths : Nat → List (Nat × Bool))
    (hpaths : ValidSourcePaths cnf rootOf offset paths)
    (residualRaw : List (List Int))
    (hrewrite : substituteCNF rootOf offset cnf = decodeCNF residualRaw)
    (canonical : List (List Int))
    (hcanonical : Witnora.CNFSorted.canonicalize (decodeCNF residualRaw) =
      decodeCNF canonical)
    (separator : List Nat)
    (components : List (Nat × Bool) → List CNF)
    (hpart : ∀ branch ∈ Witnora.SeparatorAssignments.enumerate separator,
      Witnora.ComponentPartition.checkPartition
        (Witnora.Conditioning.conditionCNF
          (Witnora.SeparatorAssignments.fixedOf branch)
          (decodeCNF canonical))
        (components branch) = true)
    (selected : List (Nat × Bool) → CNF)
    (hselected : ∀ branch ∈ Witnora.SeparatorAssignments.enumerate separator,
      selected branch ∈ components branch)
    (bound : List (Nat × Bool) → Nat)
    (rows : List (Nat × Bool) → List Witnora.G5Trace.Row)
    (steps : List (Nat × Bool) → List Witnora.G5Dag.XorRef)
    (hcert : ∀ branch ∈ Witnora.SeparatorAssignments.enumerate separator,
      Witnora.SparseBridge.checkG5Closed
        (bound branch) (selected branch) (rows branch) (steps branch) = true) :
    ¬ ∃ a, CNFHolds cnf a := by
  intro ha
  obtain ⟨roots, hr⟩ :=
    (source_iff_rewritten_residual cnf rootOf offset paths hpaths).mp ha
  rw [hrewrite] at hr
  have hraw : signedCNFHolds residualRaw roots :=
    (signedCNFHolds_iff residualRaw roots).mpr hr
  have hcan : signedCNFHolds canonical roots := by
    apply (signedCNFHolds_iff canonical roots).mpr
    rw [← hcanonical]
    apply (Witnora.CNFSorted.canonicalize_correct (decodeCNF residualRaw) roots).mpr
    exact (signedCNFHolds_iff residualRaw roots).mp hraw
  exact (Witnora.G14ConcreteBridge.signed_unsat_of_enumerated_partitions
    canonical separator components hpart selected hselected bound rows steps)
      ⟨roots, hcan⟩

#print axioms Witnora.CompressedG14.residual_g14_implies_original_unsat

end Witnora.CompressedG14
