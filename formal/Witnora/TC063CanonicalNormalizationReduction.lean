import Witnora.TC063LocalCertificateBridge
import Witnora.TC063CanonicalLocalG5

/-!
# TC-063 exact normalization obligation

The G14 semantic component cover, finite branch choice, executable pivot
schedule and canonical-source G5 completeness now have kernel proofs.
The remaining local *representation* obstacle is isolated as a precise
positive statement: for any CertifiedAffine component there exists an
accepted canonical sparse-row witness representing the same CNF.

No normalization theorem is postulated as a global axiom here: it appears
as an explicit parameter. The unconditional TC-063 family theorem is
still open until this premise is proved and executable refinement is audited.
-/

namespace Witnora.TC063CanonicalNormalizationReduction

open Witnora.Concrete
open Witnora.SemanticSAF
open Witnora.TC063Direct
open Witnora.TC063LocalCertificateBridge
open Witnora.TC063CanonicalLocalG5

/-- Accepted semantic-affine extraction may output unsorted rows.
    This exact normalization/extraction completeness property is not
    yet proved for the current checkSemanticExactAffine checker. -/
def CanonicalWitnessComplete (r : Nat) : Prop :=
  ∀ component : CNF, CertifiedAffine r component →
    ∃ (bound : Nat) (rows : List Witnora.G5Trace.Row),
      Witnora.ExactAffineMembership.checkSemanticExactAffine
        r component rows = true ∧
      Witnora.SparseBridge.checkCanonicalRows bound rows = true

/-- A complete canonicalizing witness constructor would discharge
    the entire local G5 certificate-existence premise. -/
theorem local_g5_complete_of_canonical_witness
    (r : Nat) (hnormalize : CanonicalWitnessComplete r) :
    LocalCheckedG5Complete r := by
  intro component hmember hunsat
  obtain ⟨bound, rows, hexact, hcanonical⟩ :=
    hnormalize component hmember
  obtain ⟨steps, hchecked⟩ :=
    canonical_certified_unsat_has_closed_g5
      r bound component rows hexact hcanonical hunsat
  exact ⟨bound, rows, steps, hchecked⟩

/-- Sharp family-level TC-063 target under one explicitly named,
    currently open normalization theorem. -/
theorem tc063_family_unsat_iff_checked_cover_of_normalization
    (c r : Nat) (hnormalize : CanonicalWitnessComplete r)
    (raw : List (List Int)) (hmember : Family c r raw) :
    (¬ ∃ a, Witnora.SignedSerialization.signedCNFHolds raw a) ↔
      ∃ cert : CoverData, cert.accepts c raw = true := by
  exact tc063_family_iff_of_local_g5 c r
    (local_g5_complete_of_canonical_witness r hnormalize)
    raw hmember

#print axioms Witnora.TC063CanonicalNormalizationReduction.local_g5_complete_of_canonical_witness
#print axioms Witnora.TC063CanonicalNormalizationReduction.tc063_family_unsat_iff_checked_cover_of_normalization

end Witnora.TC063CanonicalNormalizationReduction
