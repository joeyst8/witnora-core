import Witnora.ExactSignedXorCNF

/-!
# Checked Python XOR output: exact generated signed-clause meaning

Composes the existing normalization/output checker with the universal
literal-level XOR-CNF equivalence theorem. The checker confirms that
submitted signed integer data equals the expected serialized output.
Semantics here are stated for the normalized *symbolic signed clauses*;
the integer-to-literal semantic bridge is a separate proof obligation.
-/

namespace Witnora.CheckedXorOutput

open Witnora.FiniteXor
open Witnora.Extraction
open Witnora.ExactSignedXorCNF

/-- A verified Python-output certificate simultaneously establishes
    exact serialized integers and the semantic iff of the generated
    signed-literal CNF with the original (unnormalized) XOR equation. -/
theorem checked_python_xor_output_exact
    (raw normalized : List Nat) (rhs : Bool)
    (submitted : List (List Int))
    (hcheck : checkPythonEncodingOutput raw normalized rhs submitted = true)
    (a : Nat → Bool) :
    submitted = serializedSignedClauses normalized rhs ∧
      (generatedSignedHolds normalized rhs a = true ↔
        parityVars raw a = rhs) := by
  have hcert := checkedPythonEncodingOutput_sound
    raw normalized rhs submitted hcheck a
  refine ⟨hcert.2, ?_⟩
  have hiff := generatedSignedHolds_iff normalized rhs a
  simpa only [hcert.1] using hiff

/-- The accepted representation cannot silently change the parity of the
    raw equation for any assignment. -/
theorem checked_python_xor_output_parity
    (raw normalized : List Nat) (rhs : Bool)
    (submitted : List (List Int))
    (hcheck : checkPythonEncodingOutput raw normalized rhs submitted = true)
    (a : Nat → Bool) :
    generatedSignedHolds normalized rhs a = true ↔
      parityVars raw a = rhs :=
  (checked_python_xor_output_exact
    raw normalized rhs submitted hcheck a).2

example :
    checkPythonEncodingOutput [3, 1, 3, 2, 1] [2] true
      (serializedSignedClauses [2] true) = true := by
  decide

#print axioms Witnora.CheckedXorOutput.checked_python_xor_output_exact
#print axioms Witnora.CheckedXorOutput.checked_python_xor_output_parity

end Witnora.CheckedXorOutput
