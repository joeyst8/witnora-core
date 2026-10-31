import Witnora.ExactSignedXorCNF
import Witnora.ComponentPartition

/-!
# Exact affine component membership: equivalence, not mere entailment

The old G5 extraction check proves CNF => selected XOR equations. That
implication is sufficient for UNSAT soundness, but *not* sufficient for
asserting a residual CNF is exactly an affine system: extra clauses could
exclude some XOR solutions. Here a checked clause permutation of the full
generated XOR-CNF gives an iff for every assignment.

This deliberately checks a strict canonical affine subfamily. Completeness
of Python's richer affine recognizer is not claimed.
-/

namespace Witnora.ExactAffineMembership

open Witnora.Concrete
open Witnora.Extraction
open Witnora.G5Extraction
open Witnora.ExactSignedXorCNF
open Witnora.ComponentPartition

def rowClauses (row : Witnora.G5Trace.Row) : CNF :=
  generateSignedClauses row.coefficients row.rhs

def expanded (rows : List Witnora.G5Trace.Row) : CNF :=
  (rows.map rowClauses).flatten

def rowSupported (r : Nat) (row : Witnora.G5Trace.Row) : Bool :=
  decide (row.coefficients.length ≤ r) &&
    decide row.coefficients.Nodup &&
    row.coefficients.all (fun v => decide (v > 0))

/-- A clause-exact affine witness (with no hidden additional restrictions).
    Permutation allows different source-clause ordering, but not extra,
    omitted, or duplicated clauses. The arity and ID checks are separate
    from the semantic equivalence proof. -/
def checkExactAffine (r : Nat) (cnf : CNF)
    (rows : List Witnora.G5Trace.Row) : Bool :=
  rows.all (rowSupported r) &&
    decide (List.Perm cnf (expanded rows))

theorem expandedHolds_iff (rows : List Witnora.G5Trace.Row)
    (a : Nat → Bool) :
    CNFHolds (expanded rows) a ↔
      ∀ row ∈ rows, parityVars row.coefficients a = row.rhs := by
  unfold CNFHolds expanded
  rw [all_flatten]
  simp only [List.all_map]
  constructor
  · intro h row hr
    have hh := List.all_eq_true.mp h row hr
    change generatedSignedHolds row.coefficients row.rhs a = true at hh
    exact (generatedSignedHolds_iff row.coefficients row.rhs a).mp hh
  · intro h
    apply List.all_eq_true.mpr
    intro row hr
    change generatedSignedHolds row.coefficients row.rhs a = true
    exact (generatedSignedHolds_iff row.coefficients row.rhs a).mpr (h row hr)

/-- Universal exactness theorem: passing membership establishes equality
    of the source CNF's models and the conjunction of *all* witness rows. -/
theorem checkExactAffine_sound (r : Nat) (cnf : CNF)
    (rows : List Witnora.G5Trace.Row)
    (h : checkExactAffine r cnf rows = true)
    (a : Nat → Bool) :
    CNFHolds cnf a ↔
      ∀ row ∈ rows, parityVars row.coefficients a = row.rhs := by
  unfold checkExactAffine at h
  simp at h
  have hp : List.Perm cnf (expanded rows) := h.2
  have hs : CNFHolds cnf a ↔ CNFHolds (expanded rows) a := by
    unfold CNFHolds
    rw [all_perm (fun clause => clause.any (signedLitTrue a)) hp]
  exact hs.trans (expandedHolds_iff rows a)

/-- A complete single-equation encoding is accepted. -/
example :
    checkExactAffine 2
      [[(1, true), (2, false)], [(1, false), (2, true)]]
      [{coefficients := [1, 2], rhs := false}] = true := by decide

/-- Omitting either forbidden-parity clause fails exact membership. -/
example :
    checkExactAffine 2
      [[(1, true), (2, false)]]
      [{coefficients := [1, 2], rhs := false}] = false := by decide

/-- An extra source restriction makes the CNF stronger than the XOR system.
    The old one-way extraction test may accept it; exact membership rejects. -/
example :
    checkExactAffine 2
      [[(1, true), (2, false)], [(1, false), (2, true)], [(1, true)]]
      [{coefficients := [1, 2], rhs := false}] = false := by decide

/-- Non-positive IDs and duplicate variable supports are rejected. -/
example :
    checkExactAffine 2
      [[(0, true)]]
      [{coefficients := [0], rhs := true}] = false := by decide

example :
    rowSupported 2 {coefficients := [1, 1], rhs := false} = false := by decide

#print axioms Witnora.ExactAffineMembership.checkExactAffine_sound

end Witnora.ExactAffineMembership
