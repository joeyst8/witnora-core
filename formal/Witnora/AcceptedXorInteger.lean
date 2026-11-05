import Witnora.SignedIntSemanticBridge

/-!
# Complete checked integer XOR-CNF semantic equivalence

The checker already enforces positivity of raw IDs and validates normalized
output as a permutation of toggle normalization. This file proves that
these facts imply positivity of all normalized IDs automatically.
Consequently no extra positivity hypothesis is needed in the final
integer-CNF equivalence theorem.
-/

namespace Witnora.AcceptedXorInteger

open Witnora.FiniteXor
open Witnora.Extraction
open Witnora.SignedSerialization
open Witnora.SignedIntSemanticBridge

theorem toggleVar_preserves_positive
    (v : Nat) (xs : List Nat)
    (hv : 0 < v)
    (hxs : ∀ x, x ∈ xs → 0 < x) :
    ∀ x, x ∈ toggleVar v xs → 0 < x := by
  induction xs with
  | nil =>
      intro x hx
      have heq : x = v := by
        simpa [toggleVar] using hx
      rw [heq]
      exact hv
  | cons head tail ih =>
      have htail : ∀ x, x ∈ tail → 0 < x := by
        intro x hx
        exact hxs x (by simp [hx])
      by_cases heq : v = head
      · subst head
        intro x hx
        have hxTail : x ∈ tail := by
          simpa [toggleVar] using hx
        exact htail x hxTail
      · have hbeq : (v == head) = false := decide_eq_false heq
        intro x hx
        have hxParts : x = head ∨ x ∈ toggleVar v tail := by
          simpa [toggleVar, hbeq] using hx
        rcases hxParts with hxHead | hxTail
        · subst x
          exact hxs head (by simp)
        · exact ih htail x hxTail

theorem normalizeByToggle_preserves_positive
    (raw : List Nat)
    (hraw : ∀ v, v ∈ raw → 0 < v) :
    ∀ v, v ∈ normalizeByToggle raw → 0 < v := by
  induction raw with
  | nil =>
      intro v hv
      simp [normalizeByToggle] at hv
  | cons head tail ih =>
      have hhead : 0 < head := hraw head (by simp)
      have htail : ∀ v, v ∈ tail → 0 < v := by
        intro v hv
        exact hraw v (by simp [hv])
      simpa only [normalizeByToggle] using
        toggleVar_preserves_positive head (normalizeByToggle tail)
          hhead (ih htail)

/-- Accepted Python-output checking implies every normalized ID is positive,
    so no zero DIMACS variable can be introduced by normalization. -/
theorem checked_normalized_positive
    (raw normalized : List Nat) (rhs : Bool)
    (submitted : List (List Int))
    (hcheck : checkPythonEncodingOutput raw normalized rhs submitted = true) :
    ∀ v, v ∈ normalized → 0 < v := by
  have hparts :
      raw.all (fun v => decide (0 < v)) = true ∧
      checkNormalizedOutput raw normalized = true := by
    simp only [checkPythonEncodingOutput, Bool.and_eq_true] at hcheck
    exact ⟨hcheck.1.1, hcheck.1.2⟩
  have hraw : ∀ v, v ∈ raw → 0 < v := by
    intro v hv
    exact of_decide_eq_true (List.all_eq_true.mp hparts.1 v hv)
  have hperm : (normalizeByToggle raw).Perm normalized := by
    simpa [checkNormalizedOutput] using hparts.2
  intro v hv
  exact normalizeByToggle_preserves_positive raw hraw v
    (hperm.mem_iff.mpr hv)

/-- Final in-memory semantic bridge: a passing checked Python-output
    certificate implies that the ACTUAL submitted signed-integer CNF
    has exactly the models of the original raw XOR equation.
    No separate positivity or normalization hypothesis is needed. -/
theorem checked_submitted_integerCNF_iff_original_xor
    (raw normalized : List Nat) (rhs : Bool)
    (submitted : List (List Int))
    (hcheck : checkPythonEncodingOutput raw normalized rhs submitted = true)
    (a : Nat → Bool) :
    signedCNFHolds submitted a ↔ parityVars raw a = rhs := by
  exact checked_submitted_signedCNF_iff_raw_xor
    raw normalized rhs submitted hcheck
    (checked_normalized_positive raw normalized rhs submitted hcheck) a

#print axioms Witnora.AcceptedXorInteger.toggleVar_preserves_positive
#print axioms Witnora.AcceptedXorInteger.normalizeByToggle_preserves_positive
#print axioms Witnora.AcceptedXorInteger.checked_normalized_positive
#print axioms Witnora.AcceptedXorInteger.checked_submitted_integerCNF_iff_original_xor

end Witnora.AcceptedXorInteger
