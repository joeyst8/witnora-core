import Witnora.ClauseViolationParity

/-!
# Exact auxiliary clause-violation bridge

Each source assignment determines a UNIQUE vector of clause-violation
bits. Demanding that this vector be identically zero is equivalent to
satisfying the original CNF. Arbitrary parity checks may additionally
hold; they cannot exclude a source model once all violations are zero.

This validates the semantic tensor-bridge decomposition only. It does
NOT imply an efficient tensor contraction or interpolation procedure.
-/

namespace Witnora.AuxViolationBridge

open Witnora.ClauseViolationParity
open Witnora.SignedSerialization

/-- Parity rows on the *auxiliary bits*, not on source-variable scopes. -/
def auxRowsHold (rows : List (List Bool)) (v : List Bool) : Bool :=
  rows.all (fun row => !(rowParity v row))

/-- Local clause factors link aux bits to actual violation bits; unary
    zero selectors make the bridge exact, while parity rows are redundant
    at the constant coefficient. -/
def auxExact (cnf : List (List Int)) (rows : List (List Bool))
    (a : Nat → Bool) (v : List Bool) : Prop :=
  v = violationVector cnf a ∧
  v.all (fun b => !b) = true ∧ auxRowsHold rows v = true

/-- Each SAT assignment extends to exactly one valid zero-violation
    auxiliary assignment, and no non-SAT assignment extends to one. -/
theorem source_model_iff_unique_exact_aux
    (cnf : List (List Int)) (rows : List (List Bool))
    (a : Nat → Bool) :
    signedCNFHolds cnf a ↔ ∃! v : List Bool, auxExact cnf rows a v := by
  constructor
  · intro hsource
    refine ⟨violationVector cnf a, ?_, ?_⟩
    · refine ⟨rfl, source_model_has_no_violations cnf a hsource, ?_⟩
      simpa [auxRowsHold, accepts] using source_model_passes cnf rows a hsource
    · intro other hother
      exact hother.1
  · rintro ⟨v, ⟨rfl, hzero, _⟩, _⟩
    simpa [violationVector, signedCNFHolds, List.all_map] using hzero

/-- Relaxing away v=0 gives precisely the parity sketch acceptance,
    which is NOT in general equivalent to source SAT. -/
def auxRelaxed (cnf : List (List Int)) (rows : List (List Bool))
    (a : Nat → Bool) (v : List Bool) : Prop :=
  v = violationVector cnf a ∧ auxRowsHold rows v = true

theorem relaxed_aux_iff_parity_acceptance
    (cnf : List (List Int)) (rows : List (List Bool))
    (a : Nat → Bool) :
    (∃ v, auxRelaxed cnf rows a v) ↔ accepts cnf rows a = true := by
  constructor
  · rintro ⟨v, rfl, hrows⟩
    simpa [auxRowsHold, accepts] using hrows
  · intro h
    exact ⟨violationVector cnf a, rfl, by
      simpa [auxRowsHold, accepts] using h⟩

#print axioms Witnora.AuxViolationBridge.source_model_iff_unique_exact_aux
#print axioms Witnora.AuxViolationBridge.relaxed_aux_iff_parity_acceptance

end Witnora.AuxViolationBridge
