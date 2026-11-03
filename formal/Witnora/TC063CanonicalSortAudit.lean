import Witnora.TC063CanonicalAffineBridge

/-!
# TC-063: structural validity preserved by canonical coefficient sorting

The certified-affine domain already forbids repeated and zero variables.
Sorting must preserve the row arity, positive variable IDs and Nodup
predicate. This theorem removes the row-supportedness portion of the
normalization gap without assuming extraction reacceptance.

The still-open part is transporting *syntactic forbidden-pattern coverage*
for checkSemanticExactAffine across arbitrary row-variable permutations.
-/

namespace Witnora.TC063CanonicalSortAudit

open Witnora.G5Trace
open Witnora.ExactAffineMembership
open Witnora.TC063CanonicalAffineBridge

/-- Sorting an affine row preserves every validated domain restriction,
    including arity bound, distinctness and strictly positive IDs. -/
theorem row_supported_sort_eq (r : Nat) (row : Row) :
    rowSupported r (sortAffineRow row) = rowSupported r row := by
  have hp :=
    Witnora.FiniteXor.sortVariables_perm row.coefficients
  have hlen :
      (Witnora.FiniteXor.sortVariables row.coefficients).length =
      row.coefficients.length := hp.length_eq
  have hn :
      (Witnora.FiniteXor.sortVariables row.coefficients).Nodup ↔
      row.coefficients.Nodup := hp.nodup_iff
  have hall :
      (Witnora.FiniteXor.sortVariables row.coefficients).all
        (fun v => decide (v > 0)) =
      row.coefficients.all (fun v => decide (v > 0)) :=
    Witnora.ComponentPartition.all_perm
      (fun v => decide (v > 0)) hp
  simp [rowSupported, sortAffineRow, hlen, hn, hall]

/-- The row-validation conjunction is invariant for *every* row list. -/
theorem rows_supported_sort_eq (r : Nat) (rows : List Row) :
    (sortAffineRows rows).all (rowSupported r) =
      rows.all (rowSupported r) := by
  induction rows with
  | nil => rfl
  | cons row rest ih =>
      simp only [sortAffineRows, List.map_cons, List.all_cons]
      rw [row_supported_sort_eq, ih]

example :
    rowSupported 3
      (sortAffineRow { coefficients := [3, 1, 2], rhs := true }) =
    rowSupported 3 { coefficients := [3, 1, 2], rhs := true } := by decide

#print axioms Witnora.TC063CanonicalSortAudit.row_supported_sort_eq
#print axioms Witnora.TC063CanonicalSortAudit.rows_supported_sort_eq

end Witnora.TC063CanonicalSortAudit
