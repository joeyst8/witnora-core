import Witnora.TC063ClausePermutation
import Witnora.TC063CanonicalNormalizationReduction

/-!
# TC-063 unconditional canonical-witness completeness

A CertifiedAffine component carries a Boolean-accepted semantic-affine
row witness. The universal arbitrary-row permutation bridge and finite
canonical-support construction turn that witness into accepted sparse
canonical rows. This removes the formerly explicit normalization premise
from the family-level UNSAT iff checked-cover theorem.

The theorem is about the exactly defined CertifiedAffine/Family predicates.
It does not claim polynomial-time certificate discovery, CPython refinement,
or completeness for arbitrary CNF formulas.
-/

namespace Witnora.TC063CanonicalComplete

open Witnora.Concrete
open Witnora.ExactAffineMembership
open Witnora.TC063ClausePermutation

/-- Every certified-affine component admits a *production accepted*
    canonical-support witness. No additional normalization premise. -/
theorem canonical_witness_complete
    (r : Nat) :
    Witnora.TC063CanonicalNormalizationReduction.CanonicalWitnessComplete r := by
  intro component hcert
  obtain ⟨rows, hexact⟩ := hcert
  obtain ⟨bound, hbounded⟩ := finite_rows_bound_exists rows
  have hrows : rows.all (rowSupported r) = true := by
    have hs := hexact
    unfold checkSemanticExactAffine at hs
    simp at hs
    exact List.all_eq_true.mpr hs.1.1
  have hperm : ∀ row ∈ rows,
      row.rhs = (canonicalizeRow bound row).rhs ∧
      row.coefficients.Perm (canonicalizeRow bound row).coefficients := by
    intro row hr
    have hrow : rowSupported r row = true :=
      List.all_eq_true.mp hrows row hr
    have hnodup : row.coefficients.Nodup := by
      have hsupported := hrow
      simp [rowSupported] at hsupported
      exact hsupported.1.2
    refine ⟨rfl, ?_⟩
    change row.coefficients.Perm
      (Witnora.SparseBridge.canonicalSupport bound row.coefficients)
    exact (canonicalSupport_perm_of_covered bound row.coefficients
      hnodup (hbounded row hr)).symm
  refine ⟨bound, rows.map (canonicalizeRow bound), ?_, ?_⟩
  · have hbridge := checkSemanticExactAffine_map_perm
      r component rows (canonicalizeRow bound) hperm
    rw [← hbridge]
    exact hexact
  · exact checkCanonicalRows_canonicalized bound rows

/-- Unconditional, mathematical TC-063 family theorem:
    a certified SAF family instance is UNSAT iff it admits a checked
    bounded G14/G5 cover. Certificate discovery cost is not asserted. -/
theorem tc063_family_unsat_iff_checked_cover
    (c r : Nat) (raw : List (List Int))
    (hmember : Witnora.SemanticSAF.Family c r raw) :
    (¬ ∃ a, Witnora.SignedSerialization.signedCNFHolds raw a) ↔
      ∃ cert : Witnora.TC063Direct.CoverData,
        cert.accepts c raw = true := by
  exact
    Witnora.TC063CanonicalNormalizationReduction.tc063_family_unsat_iff_checked_cover_of_normalization
      c r (canonical_witness_complete r) raw hmember

#print axioms Witnora.TC063CanonicalComplete.canonical_witness_complete
#print axioms Witnora.TC063CanonicalComplete.tc063_family_unsat_iff_checked_cover

end Witnora.TC063CanonicalComplete
