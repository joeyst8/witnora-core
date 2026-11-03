import Witnora.G5IndexedBridge
import Witnora.TC063SparseDirectChecker

/-!
# Typed numeric-wire decoding of Python G5 source operations

The Python certificate's two operation shapes can be represented using
a small numeric tag and two nonnegative indices.  Tag 0 means SWAP_ROWS;
tag 1 means ADD_ROW_XOR.  Every other tag is rejected.

This decoder is checked by Lean, not by a certificate-provided parser or
source fragment.  The Python gate can submit only numeric literal triples.

This proves properties of the *typed wire representation* and its
corresponding Lean operations; it does not claim CPython/JSON correctness.
-/

namespace Witnora.TC063PythonOperationCodec

open Witnora.G5IndexedBridge
open Witnora.G5Dag

abbrev WireOperation := Nat × Nat × Nat

def encodeOne : Operation → WireOperation
  | .swapRows a b => (0, a, b)
  | .addRowXor target source => (1, target, source)

def decodeOne : WireOperation → Option Operation
  | (0, a, b) => some (.swapRows a b)
  | (1, a, b) => some (.addRowXor a b)
  | _ => none

def decodeAll : List WireOperation → Option (List Operation)
  | [] => some []
  | value :: rest => do
      let operation ← decodeOne value
      let remainder ← decodeAll rest
      return operation :: remainder

def compileWire (n : Nat) (wire : List WireOperation) :
    Option (List XorRef) :=
  (decodeAll wire).bind (compile n)

theorem decodeOne_encodeOne (op : Operation) :
    decodeOne (encodeOne op) = some op := by
  cases op <;> rfl

theorem decodeAll_encode (ops : List Operation) :
    decodeAll (ops.map encodeOne) = some ops := by
  induction ops with
  | nil => rfl
  | cons op rest ih =>
      cases op <;> simp [decodeAll, encodeOne, decodeOne, ih]

theorem compileWire_encode
    (n : Nat) (ops : List Operation) :
    compileWire n (ops.map encodeOne) = compile n ops := by
  simp [compileWire, decodeAll_encode]

/-- Acceptance of a numeric wire trace always corresponds to one
    well-typed decoded operation list accepted by the verified compiler. -/
theorem compileWire_sound
    (n : Nat) (wire : List WireOperation) (steps : List XorRef)
    (h : compileWire n wire = some steps) :
    ∃ operations : List Operation,
      decodeAll wire = some operations ∧
      compile n operations = some steps := by
  cases hd : decodeAll wire with
  | none =>
      simp [compileWire, hd] at h
  | some operations =>
      refine ⟨operations, by simp [hd], ?_⟩
      simpa [compileWire, hd] using h

example : decodeAll [(0, 0, 1), (1, 0, 1)] =
    some [.swapRows 0 1, .addRowXor 0 1] := by decide
example : decodeAll [(2, 0, 1)] = none := by decide
example : compileWire 2 [(0, 0, 1), (1, 0, 1)] =
    some [(1, 0)] := by decide
example : compileWire 2 [(1, 0, 0)] = none := by decide

#print axioms Witnora.TC063PythonOperationCodec.decodeOne_encodeOne
#print axioms Witnora.TC063PythonOperationCodec.decodeAll_encode
#print axioms Witnora.TC063PythonOperationCodec.compileWire_encode
#print axioms Witnora.TC063PythonOperationCodec.compileWire_sound


/-- Certificate-only G5 gate from typed numeric operation triples:
    ill-formed tags or invalid references fail closed before the
    source-bound sparse contradiction checker is reached. -/
def checkWireSparseG5
    (cnf : Witnora.Concrete.CNF)
    (rows : List Witnora.G5Trace.Row)
    (wire : List WireOperation) : Bool :=
  match compileWire rows.length wire with
  | none => false
  | some steps =>
      Witnora.TC063SparseDirectChecker.checkSparseG5 cnf rows steps

/-- If the executable numeric-wire gate accepts, the original CNF is
    UNSAT for every assignment; no trust in Python's claimed status. -/
theorem checkWireSparseG5_unsat
    (cnf : Witnora.Concrete.CNF)
    (rows : List Witnora.G5Trace.Row)
    (wire : List WireOperation)
    (h : checkWireSparseG5 cnf rows wire = true) :
    ¬ ∃ a : Nat → Bool, Witnora.G5Extraction.CNFHolds cnf a := by
  cases hc : compileWire rows.length wire with
  | none =>
      simp [checkWireSparseG5, hc] at h
  | some steps =>
      have hCheck :
          Witnora.TC063SparseDirectChecker.checkSparseG5
            cnf rows steps = true := by
        simpa [checkWireSparseG5, hc] using h
      exact Witnora.TC063SparseDirectChecker.checkSparseG5_unsat
        cnf rows steps hCheck

example :
    checkWireSparseG5
      [[(1048576, true)], [(1048576, false)]]
      [⟨[1048576], true⟩, ⟨[1048576], false⟩]
      [(1, 0, 1)] = true := by decide

example :
    checkWireSparseG5
      [[(1, true)], [(1, false)]]
      [⟨[1], true⟩, ⟨[1], false⟩]
      [(99, 0, 1)] = false := by decide

#print axioms Witnora.TC063PythonOperationCodec.checkWireSparseG5_unsat

end Witnora.TC063PythonOperationCodec
