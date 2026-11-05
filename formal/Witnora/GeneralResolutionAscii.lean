import Witnora.GeneralResolutionStream
import Witnora.DIMACSDocument
import Witnora.DIMACSTokens

/-!
# Arbitrary CNF resolution proofs bound to actual ASCII DIMACS documents

This composition is independent of TC-063's separator/affine family.
It checks:
1. the actual supplied ASCII source byte sequence with the Lean DIMACS parser,
2. exact agreement with the proposed signed-zero-delimited clause stream,
3. the streaming indexed resolution refutation from those signed clauses.

No Python-reported SAT status, selected graph or external solver verdict
is trusted. The caller is responsible for supplying the *actual* source
bytes, and the parser supports only its documented ASCII DIMACS subset.
-/

namespace Witnora.GeneralResolutionAscii

open Witnora.GeneralResolutionStream
open Witnora.GeneralResolutionIndexed

def checkAsciiStream
    (sourceBytes : List Nat) (tokens : List Int)
    (raw : List (List Int)) (trace : List Instruction) : Bool :=
  Witnora.DIMACSDocument.checkDocument sourceBytes tokens &&
    Witnora.DIMACSTokens.checkStream tokens raw &&
    checkStream (Witnora.SignedSerialization.decodeCNF raw) trace

/-- An accepted proof is bound to the independently parsed source
    document and universally rules out all assignments to that CNF. -/
theorem checkAsciiStream_sound
    (sourceBytes : List Nat) (tokens : List Int)
    (raw : List (List Int)) (trace : List Instruction)
    (h : checkAsciiStream sourceBytes tokens raw trace = true) :
    Witnora.DIMACSDocument.parseDocument sourceBytes =
      some (Witnora.DIMACSTokens.serialize raw) ∧
    ¬ ∃ a, Witnora.SignedSerialization.signedCNFHolds raw a := by
  have hparts :
      Witnora.DIMACSDocument.checkDocument sourceBytes tokens = true ∧
      Witnora.DIMACSTokens.checkStream tokens raw = true ∧
      checkStream (Witnora.SignedSerialization.decodeCNF raw) trace = true := by
    simpa [checkAsciiStream, Bool.and_eq_true, and_assoc] using h
  have hdoc :=
    Witnora.DIMACSDocument.checkDocument_sound
      sourceBytes tokens hparts.1
  have hstream :=
    (Witnora.DIMACSTokens.checkStream_sound
      tokens raw hparts.2.1).1
  rw [hstream] at hdoc
  exact ⟨hdoc, signedStream_unsat raw trace hparts.2.2⟩

#print axioms Witnora.GeneralResolutionAscii.checkAsciiStream_sound

end Witnora.GeneralResolutionAscii
