import Witnora.ParityResidual
import Witnora.SourceG5

/-!
# Complete compression -> residual G5 -> original UNSAT composition

The source-path correspondence is a separately checked obligation. The
residual G5 DAG must be accepted on the exact rewritten signed clauses.
Neither Python's report nor a SAT oracle substitutes for those checks.
-/

namespace Witnora.CompressedG5

open Witnora.Concrete
open Witnora.G5Extraction
open Witnora.G5Trace
open Witnora.G5Dag
open Witnora.ParityCompression
open Witnora.ParityResidual
open Witnora.SignedSerialization
open Witnora.SourceG5

theorem residual_g5_implies_original_unsat
    (cnf : CNF) (rootOf : Nat → Nat) (offset : Nat → Bool)
    (paths : Nat → List (Nat × Bool))
    (hpaths : ValidSourcePaths cnf rootOf offset paths)
    (residualRaw : List (List Int))
    (hrewrite : substituteCNF rootOf offset cnf = decodeCNF residualRaw)
    (bound : Nat) (rows : List Row) (steps : List XorRef)
    (hg5 : checkRawG5 bound residualRaw rows steps = true) :
    ¬ ∃ a, CNFHolds cnf a := by
  intro ha
  obtain ⟨rootValues, hresidual⟩ :=
    (source_iff_rewritten_residual cnf rootOf offset paths hpaths).mp ha
  rw [hrewrite] at hresidual
  have hraw : signedCNFHolds residualRaw rootValues :=
    (signedCNFHolds_iff residualRaw rootValues).mpr hresidual
  exact (checkRawG5_unsat bound residualRaw rows steps hg5)
    ⟨rootValues, hraw⟩

#print axioms Witnora.CompressedG5.residual_g5_implies_original_unsat

end Witnora.CompressedG5
