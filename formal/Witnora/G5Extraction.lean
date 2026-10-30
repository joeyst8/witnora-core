import Witnora.FiniteXor
import Witnora.G5Trace

/-!
# Proof-producing CNF-to-XOR pattern extraction

Check that every wrong-parity pattern clause is literally present in the
original CNF. This is exponential only in the extracted equation's width,
not in the total number of variables. The theorem establishes CNF entails
the equation for every assignment. Bridging parityVars to the G5 sparse
row representation remains a separate theorem.
-/

namespace Witnora.G5Extraction

open Witnora.Concrete
open Witnora.FiniteXor
open Witnora.Extraction

def CNFHolds (cnf : CNF) (a : Nat → Bool) : Prop :=
  cnf.all (fun clause => clause.any (signedLitTrue a)) = true

/-- A source clause is sufficient evidence for a forbidden clause if
every literal in the source appears in the forbidden clause. A satisfying
source clause then satisfies the forbidden clause, regardless of order. -/
def clauseSubsumes (source expected : List (Nat × Bool)) : Bool :=
  source.all (fun lit => decide (lit ∈ expected))

/-- Check that at least one original CNF clause entails the expected clause. -/
def checkClauseCoverage (cnf : CNF) (expected : List (Nat × Bool)) : Bool :=
  cnf.any (fun source => clauseSubsumes source expected)

theorem checkClauseCoverage_sound (cnf : CNF)
    (expected : List (Nat × Bool))
    (a : Nat → Bool)
    (hcnf : CNFHolds cnf a)
    (h : checkClauseCoverage cnf expected = true) :
    expected.any (signedLitTrue a) = true := by
  have hsource := List.any_eq_true.mp h
  rcases hsource with ⟨source, hmem, hsub⟩
  have hholds := List.all_eq_true.mp hcnf source hmem
  rcases List.any_eq_true.mp hholds with ⟨lit, hlit, hlitTrue⟩
  have hcovered := List.all_eq_true.mp hsub lit hlit
  have hmember : lit ∈ expected := by
    simpa [clauseSubsumes] using hcovered
  exact List.any_eq_true.mpr ⟨lit, hmember, hlitTrue⟩

def checkPattern (cnf : CNF) (vars : List Nat) (rhs : Bool) : Bool :=
  (generateForbiddenPatterns vars.length rhs).all (fun bad =>
    checkClauseCoverage cnf
      (signForbiddenClause (List.zip vars bad)))

theorem parityBits_map (vars : List Nat) (a : Nat → Bool) :
    parityBits (vars.map a) = parityVars vars a := by
  induction vars with
  | nil => rfl
  | cons v rest ih =>
      simp only [List.map_cons, parityBits, parityVars, ih]

theorem zip_map_agrees (vars : List Nat) (a : Nat → Bool) :
    (List.zip vars (vars.map a)).all (fun p => a p.1 == p.2) = true := by
  induction vars with
  | nil => rfl
  | cons v rest ih =>
      simp [ih]

/-- A complete set of canonical forbidden clauses syntactically embedded in
the original CNF entails the represented XOR equation for every assignment.
No global assignment enumeration, oracle, or unverified extraction claim. -/
theorem checkPattern_sound (cnf : CNF) (vars : List Nat)
    (rhs : Bool) (hcheck : checkPattern cnf vars rhs = true)
    (a : Nat → Bool) (hcnf : CNFHolds cnf a) :
    parityVars vars a = rhs := by
  by_cases hright : parityVars vars a = rhs
  · exact hright
  · let bad := vars.map a
    have hlen : bad.length = vars.length := by simp [bad]
    have hmem : bad ∈ allBits vars.length := by
      simpa [hlen] using allBits_complete bad
    have hwrong : parityBits bad ≠ rhs := by
      simpa [bad, parityBits_map] using hright
    have hbad : bad ∈ generateForbiddenPatterns vars.length rhs := by
      simp [generateForbiddenPatterns, hmem, hwrong]
    have hcovered :
        checkClauseCoverage cnf (signForbiddenClause (List.zip vars bad)) = true := by
      have hrow := List.all_eq_true.mp hcheck bad hbad
      simpa [checkPattern] using hrow
    have hclauses :=
      checkClauseCoverage_sound cnf
        (signForbiddenClause (List.zip vars bad)) a hcnf hcovered
    have hfalse :
        (signForbiddenClause (List.zip vars bad)).any (signedLitTrue a) = false := by
      rw [signForbiddenClause_true]
      simp [bad, zip_map_agrees]
    rw [hfalse] at hclauses
    cases hclauses

/-- Check every proposed initial G5 row using the original CNF clauses. -/
def checkInitialRows (cnf : CNF) (rows : List Witnora.G5Trace.Row) : Bool :=
  rows.all (fun row => checkPattern cnf row.coefficients row.rhs)

/-- A successful multirow extraction certificate entails every initial
equation in list-parity semantics for every original CNF model. -/
theorem checkInitialRows_sound (cnf : CNF)
    (rows : List Witnora.G5Trace.Row)
    (hcheck : checkInitialRows cnf rows = true)
    (a : Nat → Bool) (hcnf : CNFHolds cnf a)
    (row : Witnora.G5Trace.Row) (hmem : row ∈ rows) :
    parityVars row.coefficients a = row.rhs := by
  have hrow := List.all_eq_true.mp hcheck row hmem
  exact checkPattern_sound cnf row.coefficients row.rhs hrow a hcnf

#print axioms Witnora.G5Extraction.checkInitialRows_sound

/-- Reordered signed literals provide the same valid clause evidence. -/
example :
    checkClauseCoverage
      [[(2, false), (1, true)]]
      [(1, true), (2, false)] = true := by decide

/-- A strictly stronger source unit clause implies the required clause. -/
example :
    checkClauseCoverage
      [[(1, true)]]
      [(1, true), (2, false)] = true := by decide

/-- A weaker source clause must not be mistaken for a stronger unit clause. -/
example :
    checkClauseCoverage
      [[(1, true), (2, false)]]
      [(1, true)] = false := by decide

/-- Reject an incomplete 2-variable XOR encoding. -/
example :
    checkPattern
      [[(1, true), (2, true)]]
      [1, 2] false = false := by decide

/-- A complete encoding for x1 XOR x2 = false. -/
example :
    checkPattern
      [[(1, true), (2, false)], [(1, false), (2, true)]]
      [1, 2] false = true := by decide

#print axioms Witnora.G5Extraction.checkPattern_sound

end Witnora.G5Extraction
