import Witnora.SignedSerialization

/-!
# Clause-violation parity sketches: experimental ETH mathematical bridge

Each violation bit is 1 exactly when a source CNF clause is false. A parity
row selects clause-violation bits, not original Boolean variable bits. For
3-CNF the violations are degree-at-most-3 polynomials over F_2, so ordinary
G5 Gaussian elimination alone is not a general solver.

This file universally proves SAT -> parity acceptance. The converse is false
for arbitrary masks and is assessed by exhaustive finite diagnostics only.
-/

namespace Witnora.ClauseViolationParity

open Witnora.Concrete
open Witnora.FiniteXor
open Witnora.G5Extraction
open Witnora.SignedSerialization

def violationVector (cnf : List (List Int)) (a : Nat → Bool) : List Bool :=
  cnf.map (fun clause => !(clause.any (fun lit => signedLitTrue a (decode lit))))

/-- XOR of selected violation bits, with equal-length masks in experiments. -/
def rowParity : List Bool → List Bool → Bool
  | v :: vs, selected :: selections =>
      (v && selected) != rowParity vs selections
  | _, _ => false

def accepts (cnf : List (List Int)) (rows : List (List Bool))
    (a : Nat → Bool) : Bool :=
  rows.all (fun row => !(rowParity (violationVector cnf a) row))

theorem rowParity_of_zero (v row : List Bool)
    (h : v.all (fun b => !b) = true) : rowParity v row = false := by
  induction v generalizing row with
  | nil =>
      cases row <;> rfl
  | cons head tail ih =>
      cases head with
      | true =>
          simp at h
      | false =>
          have htail : tail.all (fun b => !b) = true := by
            simpa using h
          cases row with
          | nil => rfl
          | cons selected rest =>
              simpa [rowParity] using ih rest htail

theorem source_model_has_no_violations (cnf : List (List Int))
    (a : Nat → Bool) (h : signedCNFHolds cnf a) :
    (violationVector cnf a).all (fun b => !b) = true := by
  simpa [violationVector, signedCNFHolds, List.all_map] using h

/-- Every source model passes EVERY selected parity check, for any CNF. -/
theorem source_model_passes (cnf : List (List Int))
    (rows : List (List Bool)) (a : Nat → Bool)
    (h : signedCNFHolds cnf a) : accepts cnf rows a = true := by
  unfold accepts
  apply List.all_eq_true.mpr
  intro row _
  have hzero := source_model_has_no_violations cnf a h
  simp [rowParity_of_zero (violationVector cnf a) row hzero]

/-- None of the selected positions is a violated clause. This is a
    sufficient condition for a false-positive collision, not necessary:
    two selected violations also cancel mod 2. -/
def disjointMask : List Bool → List Bool → Bool
  | v :: vs, selected :: selections =>
      !(v && selected) && disjointMask vs selections
  | _, _ => true

theorem disjointMask_implies_even (v row : List Bool)
    (h : disjointMask v row = true) : rowParity v row = false := by
  induction v generalizing row with
  | nil =>
      cases row <;> rfl
  | cons head tail ih =>
      cases row with
      | nil => rfl
      | cons selected rest =>
          have hparts :
              !(head && selected) = true ∧ disjointMask tail rest = true := by
            simpa [disjointMask] using h
          have hrest := ih rest hparts.2
          cases head <;> cases selected <;>
            simp_all [rowParity, disjointMask]

/-- Source models and also nonmodels with no tested violated clause pass.
    This provides a formally checkable geometric collision mechanism. -/
theorem all_disjoint_rows_accept (cnf : List (List Int))
    (rows : List (List Bool)) (a : Nat → Bool)
    (h : rows.all (fun row => disjointMask (violationVector cnf a) row) = true) :
    accepts cnf rows a = true := by
  unfold accepts
  apply List.all_eq_true.mpr
  intro row hmem
  have hr := List.all_eq_true.mp h row hmem
  have heven := disjointMask_implies_even (violationVector cnf a) row hr
  simp [heven]

def assignmentBits (bits varId : Nat) : Bool :=
  decide ((bits / (2 ^ (varId - 1))) % 2 = 1)

def sourceSatisfiedBool (cnf : List (List Int)) (a : Nat → Bool) : Bool :=
  cnf.all (fun clause => clause.any (fun lit => signedLitTrue a (decode lit)))

/-- Exponential finite check of BOTH directions on the first n variables. -/
def boundedExact (cnf : List (List Int)) (rows : List (List Bool))
    (n : Nat) : Bool :=
  (List.range (2 ^ n)).all (fun bits =>
    sourceSatisfiedBool cnf (assignmentBits bits) ==
      accepts cnf rows (assignmentBits bits))

example : rowParity [true, true] [true, true] = false := by decide
example : disjointMask [true, false] [false, true] = true := by decide
example : rowParity [true, false] [true, true] = true := by decide

/-- Two violated clauses can cancel: arbitrary parity rows are not exact. -/
example : boundedExact [[1], [2]] [[true, true]] 2 = false := by decide

#print axioms Witnora.ClauseViolationParity.rowParity_of_zero
#print axioms Witnora.ClauseViolationParity.source_model_has_no_violations
#print axioms Witnora.ClauseViolationParity.source_model_passes
#print axioms Witnora.ClauseViolationParity.disjointMask_implies_even
#print axioms Witnora.ClauseViolationParity.all_disjoint_rows_accept

end Witnora.ClauseViolationParity
