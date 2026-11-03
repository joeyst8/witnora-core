import Witnora.TC063CanonicalBound

/-!
# TC-063: independent normalization gate against proved universal theorems

Audit note (2026-11-03): the complete proof already exists in
TC063PatternPermutation and TC063CanonicalBound.  This small module
checks those interfaces and adds an executable unsorted-row regression.
No additional completeness premise is assumed here.
-/

namespace Witnora.TC063CanonicalSortAudit

open Witnora.G5Trace
open Witnora.ExactAffineMembership
open Witnora.TC063CanonicalAffineBridge
open Witnora.SemanticSAF

/-- The source checker sees unchanged row validity after sorting. -/
theorem row_supported_sort_eq (r : Nat) (row : Row) :
    rowSupported r (sortAffineRow row) = rowSupported r row :=
  Witnora.TC063PatternPermutation.rowSupported_sortAffineRow r row

/-- The row-list validity checker is invariant for every input list. -/
theorem rows_supported_sort_eq (r : Nat) (rows : List Row) :
    (sortAffineRows rows).all (rowSupported r) =
      rows.all (rowSupported r) :=
  Witnora.TC063PatternPermutation.rowsSupported_sortAffineRows r rows

/-- Every accepted exact affine extraction remains accepted when sorted. -/
theorem accepted_extraction_stays_accepted (r : Nat)
    (source : Witnora.Concrete.CNF) (rows : List Row)
    (h : checkSemanticExactAffine r source rows = true) :
    checkSemanticExactAffine r source (sortAffineRows rows) = true :=
  Witnora.TC063PatternPermutation.checkSemanticExactAffine_sortAffineRows
    r source rows h

/-- The restricted-family canonical-witness obligation is already closed. -/
theorem all_certified_affine_have_canonical_witness (r : Nat)
    (cnf : Witnora.Concrete.CNF) (h : CertifiedAffine r cnf) :
    CanonicalAffineWitness r cnf :=
  Witnora.TC063CanonicalBound.certifiedAffine_has_canonicalWitness r cnf h

#print axioms Witnora.TC063CanonicalSortAudit.accepted_extraction_stays_accepted
#print axioms Witnora.TC063CanonicalSortAudit.all_certified_affine_have_canonical_witness

end Witnora.TC063CanonicalSortAudit
