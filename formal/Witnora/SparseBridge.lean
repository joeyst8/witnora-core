import Witnora.G5Verified

/-!
# Canonical support refinement for sparse G5 rows

The canonical-support function lists all supported indices in ascending
order, without duplicates. Its upper bound is *exclusive*: to include
variable n, call the checker with bound n+1.

A row is admitted only if its supplied coefficients equal this canonical
support. This validates ordering, uniqueness, and bounds, and provides
a direct representation bridge without enumerating assignments.
-/

namespace Witnora.SparseBridge

open Witnora.G5Trace
open Witnora.SparseParity
open Witnora.Extraction
open Witnora.G5Dag
open Witnora.G5Extraction

def canonicalSupport : Nat → List Nat → List Nat
  | 0, _ => []
  | bound + 1, coeff =>
      canonicalSupport bound coeff ++
        (if decide (bound ∈ coeff) then [bound] else [])

/-- For any coefficient list and assignment, the sparse evaluator is
exactly the list-parity evaluator on its bounded canonical support. -/
theorem sparseParity_canonicalSupport
    (bound : Nat) (coeff : List Nat) (a : Nat → Bool) :
    sparseParity bound coeff a =
      parityVars (canonicalSupport bound coeff) a := by
  induction bound with
  | zero => rfl
  | succ n ih =>
      change Bool.xor (sparseParity n coeff a)
        ((decide (n ∈ coeff)) && a n) =
        parityVars (canonicalSupport n coeff ++
          (if decide (n ∈ coeff) then [n] else [])) a
      rw [ih, parityVars_append]
      by_cases hmem : n ∈ coeff
      · simp [hmem, parityVars]
      · simp [hmem, parityVars]

def checkCanonicalRow (bound : Nat) (row : Row) : Bool :=
  decide (row.coefficients = canonicalSupport bound row.coefficients)

def checkCanonicalRows (bound : Nat) (rows : List Row) : Bool :=
  rows.all (checkCanonicalRow bound)

/-- Passing the canonical-support check proves sparse/list parity equality
for every accepted row and every assignment. -/
theorem checkCanonicalRows_sound
    (bound : Nat) (rows : List Row)
    (h : checkCanonicalRows bound rows = true)
    (row : Row) (hr : row ∈ rows)
    (a : Nat → Bool) :
    sparseParity bound row.coefficients a =
      parityVars row.coefficients a := by
  have hrow := List.all_eq_true.mp h row hr
  have heq : row.coefficients =
      canonicalSupport bound row.coefficients := by
    simpa [checkCanonicalRows, checkCanonicalRow] using hrow
  rw [heq]
  exact sparseParity_canonicalSupport bound row.coefficients a

/-- A closed, executable checker: original CNF clause coverage, canonical
sparse-row representation, and indexed DAG contradiction proof. -/
def checkG5Closed (bound : Nat) (cnf : Witnora.Concrete.CNF)
    (rows : List Row) (steps : List XorRef) : Bool :=
  checkInitialRows cnf rows &&
    checkCanonicalRows bound rows &&
    checkDagContradiction rows steps

/-- No external semantic extraction or sparse-representation assumption.
All three checkable conditions suffice for UNSAT, without global SAT search. -/
theorem checkG5Closed_unsat (bound : Nat)
    (cnf : Witnora.Concrete.CNF)
    (rows : List Row) (steps : List XorRef)
    (h : checkG5Closed bound cnf rows steps = true) :
    ¬ ∃ a, CNFHolds cnf a := by
  have hsplit := h
  simp [checkG5Closed] at hsplit
  apply Witnora.G5Verified.checkG5_unsat_of_sparse_bridge
    bound cnf rows steps
  · intro row hr a
    exact checkCanonicalRows_sound bound rows hsplit.1.2 row hr a
  · simp [Witnora.G5Verified.checkG5, hsplit.1.1, hsplit.2]

example : checkCanonicalRow 3 ⟨[1, 2], false⟩ = true := by decide
example : checkCanonicalRow 3 ⟨[2, 1], false⟩ = false := by decide
example : checkCanonicalRow 3 ⟨[3], true⟩ = false := by decide

#print axioms Witnora.SparseBridge.sparseParity_canonicalSupport
#print axioms Witnora.SparseBridge.checkCanonicalRows_sound
#print axioms Witnora.SparseBridge.checkG5Closed_unsat

end Witnora.SparseBridge
