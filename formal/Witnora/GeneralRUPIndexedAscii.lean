import Witnora.GeneralRUPIndexed
import Witnora.DIMACSDocument
import Witnora.DIMACSTokens

/-!
# Original ASCII DIMACS bytes → indexed-reason RUP UNSAT theorem

Each source token and clause is checked against the exact supported DIMACS
source byte document; each unit and final conflict cites an existing clause
row ID. Solver output and Python witness elaboration are untrusted.
-/

namespace Witnora.GeneralRUPIndexedAscii

open Witnora.GeneralRUPIndexed

def checkAsciiIndexedRup
    (source : List Nat) (tokens : List Int)
    (raw : List (List Int)) (trace : List IndexedRupStep) : Bool :=
  Witnora.DIMACSDocument.checkDocument source tokens &&
    Witnora.DIMACSTokens.checkStream tokens raw &&
    checkIndexedRup (Witnora.SignedSerialization.decodeCNF raw) trace

theorem checkAsciiIndexedRup_sound
    (source : List Nat) (tokens : List Int)
    (raw : List (List Int)) (trace : List IndexedRupStep)
    (h : checkAsciiIndexedRup source tokens raw trace = true) :
    Witnora.DIMACSDocument.parseDocument source =
      some (Witnora.DIMACSTokens.serialize raw) ∧
    ¬ ∃ a, Witnora.SignedSerialization.signedCNFHolds raw a := by
  have hparts :
      Witnora.DIMACSDocument.checkDocument source tokens = true ∧
      Witnora.DIMACSTokens.checkStream tokens raw = true ∧
      checkIndexedRup (Witnora.SignedSerialization.decodeCNF raw)
        trace = true := by
    simpa [checkAsciiIndexedRup, Bool.and_eq_true, and_assoc] using h
  have hdocument :=
    Witnora.DIMACSDocument.checkDocument_sound source tokens hparts.1
  have hclauses :=
    (Witnora.DIMACSTokens.checkStream_sound tokens raw hparts.2.1).1
  rw [hclauses] at hdocument
  exact ⟨hdocument, signedIndexedRup_unsat raw trace hparts.2.2⟩

#print axioms Witnora.GeneralRUPIndexedAscii.checkAsciiIndexedRup_sound

end Witnora.GeneralRUPIndexedAscii
