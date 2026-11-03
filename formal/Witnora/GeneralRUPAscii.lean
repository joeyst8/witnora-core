import Witnora.GeneralRUP
import Witnora.DIMACSDocument
import Witnora.DIMACSTokens

/-!
# Arbitrary-CNF RUP refutations bound to their original ASCII DIMACS bytes

The external solver only proposes RUP additions and their unit witnesses.
Lean independently parses the exact source document, checks that its
signed clauses match the source, validates all RUP steps and the final
empty clause, and proves UNSAT for every assignment. No separator or
affine promise is required.
-/

namespace Witnora.GeneralRUPAscii

open Witnora.GeneralRUP

def checkAsciiRup
    (source : List Nat) (tokens : List Int)
    (raw : List (List Int)) (trace : List RupStep) : Bool :=
  Witnora.DIMACSDocument.checkDocument source tokens &&
    Witnora.DIMACSTokens.checkStream tokens raw &&
    checkRup (Witnora.SignedSerialization.decodeCNF raw) trace

theorem checkAsciiRup_sound
    (source : List Nat) (tokens : List Int)
    (raw : List (List Int)) (trace : List RupStep)
    (h : checkAsciiRup source tokens raw trace = true) :
    Witnora.DIMACSDocument.parseDocument source =
      some (Witnora.DIMACSTokens.serialize raw) ∧
    ¬ ∃ a, Witnora.SignedSerialization.signedCNFHolds raw a := by
  have hparts :
      Witnora.DIMACSDocument.checkDocument source tokens = true ∧
      Witnora.DIMACSTokens.checkStream tokens raw = true ∧
      checkRup (Witnora.SignedSerialization.decodeCNF raw) trace = true := by
    simpa [checkAsciiRup, Bool.and_eq_true, and_assoc] using h
  have hdocument :=
    Witnora.DIMACSDocument.checkDocument_sound source tokens hparts.1
  have hclauses :=
    (Witnora.DIMACSTokens.checkStream_sound
      tokens raw hparts.2.1).1
  rw [hclauses] at hdocument
  exact ⟨hdocument, signedRup_unsat raw trace hparts.2.2⟩

#print axioms Witnora.GeneralRUPAscii.checkAsciiRup_sound

end Witnora.GeneralRUPAscii
