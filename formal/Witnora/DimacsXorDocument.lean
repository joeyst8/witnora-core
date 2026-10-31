import Witnora.DIMACSDocument
import Witnora.AcceptedXorInteger

/-!
# DIMACS source-byte to original XOR equation

This composes the existing executable whole-document ASCII DIMACS parser,
the exact zero-delimited clause-stream checker, and the universal accepted
integer XOR-CNF theorem. No already-parsed token list is trusted.
-/

namespace Witnora.DimacsXorDocument

open Witnora.DIMACSDocument
open Witnora.DIMACSTokens
open Witnora.FiniteXor
open Witnora.SignedSerialization
open Witnora.Extraction
open Witnora.AcceptedXorInteger

/-- Accept iff the actual supplied ASCII source parses to exactly the
    zero-delimited submitted clauses and those clauses are a checked
    encoding of the original raw XOR equation. -/
def checkXorDocument
    (source : List Nat) (raw normalized : List Nat) (rhs : Bool)
    (submitted : List (List Int)) : Bool :=
  match parseDocument source with
  | none => false
  | some tokens =>
      checkStream tokens submitted &&
        checkPythonEncodingOutput raw normalized rhs submitted

theorem checked_xor_document_tokens
    (source : List Nat) (raw normalized : List Nat) (rhs : Bool)
    (submitted : List (List Int))
    (h : checkXorDocument source raw normalized rhs submitted = true) :
    parseDocument source = some (serialize submitted) := by
  cases hparse : parseDocument source with
  | none =>
      simp [checkXorDocument, hparse] at h
  | some tokens =>
      have hparts :
          checkStream tokens submitted = true ∧
            checkPythonEncodingOutput raw normalized rhs submitted = true := by
        simpa only [checkXorDocument, hparse, Bool.and_eq_true] using h
      have hstream := (checkStream_sound tokens submitted hparts.1).1
      simpa [hparse] using congrArg some hstream

/-- Successful verification of the literal input bytes proves that the
    resulting submitted integer CNF has precisely the models of the
    original raw XOR equation, for every Boolean assignment. -/
theorem checked_xor_document_iff_original
    (source : List Nat) (raw normalized : List Nat) (rhs : Bool)
    (submitted : List (List Int))
    (h : checkXorDocument source raw normalized rhs submitted = true)
    (a : Nat → Bool) :
    signedCNFHolds submitted a ↔ parityVars raw a = rhs := by
  cases hparse : parseDocument source with
  | none =>
      simp [checkXorDocument, hparse] at h
  | some tokens =>
      have hparts :
          checkStream tokens submitted = true ∧
            checkPythonEncodingOutput raw normalized rhs submitted = true := by
        simpa only [checkXorDocument, hparse, Bool.and_eq_true] using h
      exact checked_submitted_integerCNF_iff_original_xor
        raw normalized rhs submitted hparts.2 a

/-- Example input: 'p cnf 1 1' then the one positive unit clause '1 0'. -/
def positiveUnitDocument : List Nat :=
  [112, 32, 99, 110, 102, 32, 49, 32, 49, 10,
   49, 32, 48, 10]

theorem positive_unit_document_accepted :
    checkXorDocument positiveUnitDocument [1] [1] true [[1]] = true := by
  decide

theorem positive_unit_document_exact_tokens :
    parseDocument positiveUnitDocument = some [1, 0] := by
  decide

theorem positive_unit_document_iff :
    ∀ a : Nat → Bool,
      signedCNFHolds [[1]] a ↔ parityVars [1] a = true := by
  intro a
  exact checked_xor_document_iff_original
    positiveUnitDocument [1] [1] true [[1]]
    positive_unit_document_accepted a

theorem rejects_modified_source_literal :
    checkXorDocument
      [112, 32, 99, 110, 102, 32, 49, 32, 49, 10,
       45, 49, 32, 48, 10]
      [1] [1] true [[1]] = false := by
  decide

theorem rejects_extra_clause :
    checkXorDocument
      [112, 32, 99, 110, 102, 32, 49, 32, 50, 10,
       49, 32, 48, 10, 49, 32, 48, 10]
      [1] [1] true [[1]] = false := by
  decide

theorem rejects_non_ascii :
    checkXorDocument (positiveUnitDocument ++ [255])
      [1] [1] true [[1]] = false := by
  decide

#print axioms Witnora.DimacsXorDocument.checked_xor_document_tokens
#print axioms Witnora.DimacsXorDocument.checked_xor_document_iff_original
#print axioms Witnora.DimacsXorDocument.positive_unit_document_iff

end Witnora.DimacsXorDocument
