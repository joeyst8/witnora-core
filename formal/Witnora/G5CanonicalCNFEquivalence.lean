import Witnora.ExactSignedXorCNF
import Witnora.SparseBridge
import Witnora.G5ExecutableTotality

/-!
# Exact canonical XOR-CNF to executable G5 rows

The source is an actual CNF of signed literals, assembled from the
canonical forbidden-parity clauses for each initial equation. This
discharges the extraction *equivalence* obligation for that family of
CNFs, not for arbitrary CNFs.
-/

namespace Witnora.G5CanonicalCNFEquivalence

open Witnora.Concrete
open Witnora.G5Trace
open Witnora.G5Extraction
open Witnora.ExactSignedXorCNF
open Witnora.SparseBridge
open Witnora.G5Certificate
open Witnora.Extraction

/-- Concatenate concrete signed clauses generated for every input row. -/
def rowsCNF : List Row → CNF
  | [] => []
  | row :: rest =>
      generateSignedClauses row.coefficients row.rhs ++ rowsCNF rest

/-- Exact model equivalence for the literal-level generated CNF. -/
theorem rowsCNF_iff_list_parity (rows : List Row)
    (a : Nat → Bool) :
    CNFHolds (rowsCNF rows) a ↔
      ∀ row ∈ rows, parityVars row.coefficients a = row.rhs := by
  induction rows with
  | nil =>
      simp [rowsCNF, CNFHolds]
  | cons row rest ih =>
      change
        ((generateSignedClauses row.coefficients row.rhs ++
          rowsCNF rest).all
          (fun clause => clause.any (signedLitTrue a)) = true) ↔
        (∀ r ∈ row :: rest, parityVars r.coefficients a = r.rhs)
      rw [List.all_append, Bool.and_eq_true]
      change
        (generatedSignedHolds row.coefficients row.rhs a = true ∧
          CNFHolds (rowsCNF rest) a) ↔
        (∀ r ∈ row :: rest, parityVars r.coefficients a = r.rhs)
      rw [generatedSignedHolds_iff, ih]
      simp

/-- The canonical-support check turns each list-parity equation into
    exactly the sparse equation evaluated by the G5 certificate kernel. -/
theorem rowsCNF_iff_sparse_rows
    (bound : Nat) (rows : List Row)
    (hcanonical : checkCanonicalRows bound rows = true)
    (a : Nat → Bool) :
    CNFHolds (rowsCNF rows) a ↔
      ∀ row ∈ rows, RowHolds bound row a := by
  rw [rowsCNF_iff_list_parity]
  constructor
  · intro h row hr
    have hp := h row hr
    have heq := checkCanonicalRows_sound bound rows
      hcanonical row hr a
    change sparseParity bound row.coefficients a = row.rhs
    exact heq.trans hp
  · intro h row hr
    have hp : sparseParity bound row.coefficients a = row.rhs :=
      h row hr
    have heq := checkCanonicalRows_sound bound rows
      hcanonical row hr a
    exact heq.symm.trans hp

/-- For exactly encoded canonical XOR-CNF, a complete bounded schedule
    eliminates the formerly assumed CNF-to-sparse-row equivalence.
    The executable indexed G5 pipeline returns an accepted certificate
    for every UNSAT instance satisfying the finite coverage conditions. -/
theorem canonical_cnf_unsat_has_checked_certificate
    (rows : List Row) (bound : Nat) (variables : List Nat)
    (hcanonical : checkCanonicalRows bound rows = true)
    (hcoverage : Witnora.G5InitialSupportCoverage.Covered
      variables rows)
    (hvars : ∀ v ∈ variables, v < bound)
    (hunsat : ¬ ∃ a : Nat → Bool, CNFHolds (rowsCNF rows) a) :
    ∃ outcome : Witnora.G5RetiredPivotLedger.PivotOutcome rows,
      Witnora.G5RetiredPivotLedger.emitScheduleWithPivots
        rows variables (List.range rows.length)
        (Witnora.G5IndexedOperationEmitter.SourceState.start rows) =
          some outcome ∧
      Witnora.G5IndexedOperationEmitter.accepts
        rows outcome.operations = true := by
  exact Witnora.G5ExecutableTotality.cnf_unsat_has_checked_certificate_of_equivalence
    rows bound variables
    (fun a => CNFHolds (rowsCNF rows) a)
    hcoverage hvars
    (rowsCNF_iff_sparse_rows bound rows hcanonical)
    hunsat

/-- A single disjunction is not a canonical parity clause family:
    the extraction checker correctly rejects its incomplete pattern. -/
example :
    checkPattern [[(1, true), (2, true)]]
      [1, 2] false = false := by decide

#print axioms Witnora.G5CanonicalCNFEquivalence.rowsCNF_iff_sparse_rows
#print axioms Witnora.G5CanonicalCNFEquivalence.canonical_cnf_unsat_has_checked_certificate

end Witnora.G5CanonicalCNFEquivalence
