import Witnora.G14NormalizedPartition

/-!
# Universal left-to-right G14 conditioning-loop refinement

Model Python's _reduce_clause loop as an explicit accumulator carrying
unassigned literals in reverse. A satisfied separator literal returns
none immediately; a falsified assigned literal is skipped.

The proof covers *all* finite clauses, separators, and accumulator
states, rather than testing only a bounded family of formulas. It is a
Lean algorithm-level refinement, not a semantics theorem about CPython.
-/

namespace Witnora.G14PythonConditioningLoop

open Witnora.Concrete
open Witnora.Conditioning
open Witnora.G5Extraction
open Witnora.G14NormalizedPartition

/-- Iterative accumulator model of Python's clause-reduction loop. -/
def pythonConditionLoop (fixed : Nat → Option Bool) :
    List Literal → List Literal → Option (List Literal)
  | [], keptRev => some keptRev.reverse
  | lit :: rest, keptRev =>
      match fixed lit.1 with
      | none => pythonConditionLoop fixed rest (lit :: keptRev)
      | some b =>
          if (if lit.2 then b else !b) then none
          else pythonConditionLoop fixed rest keptRev

def pythonConditionClause (fixed : Nat → Option Bool)
    (clause : List Literal) : Option (List Literal) :=
  pythonConditionLoop fixed clause []

/-- The loop invariant accounts for arbitrary previously retained
    literals, including early satisfaction and empty residual clauses. -/
theorem pythonConditionLoop_eq
    (fixed : Nat → Option Bool) (clause keptRev : List Literal) :
    pythonConditionLoop fixed clause keptRev =
      (conditionClause fixed clause).map
        (fun remaining => keptRev.reverse ++ remaining) := by
  induction clause generalizing keptRev with
  | nil =>
      simp [pythonConditionLoop, conditionClause]
  | cons lit rest ih =>
      cases hfixed : fixed lit.1 with
      | none =>
          simp only [pythonConditionLoop, conditionClause, hfixed]
          rw [ih]
          cases hrest : conditionClause fixed rest with
          | none => simp [hrest]
          | some tail =>
              simp [hrest, List.reverse_cons, List.append_assoc]
      | some b =>
          by_cases hsatisfied : (if lit.2 then b else !b) = true
          · simp [pythonConditionLoop, conditionClause,
              hfixed, hsatisfied]
          · have hfalse : (if lit.2 then b else !b) = false := by
              cases hv : (if lit.2 then b else !b) <;> simp_all
            simp only [pythonConditionLoop, conditionClause,
              hfixed, hfalse, Bool.false_eq_true, ↓reduceIte]
            exact ih keptRev

/-- Exact output equality, not merely satisfiability equivalence,
    for all accepted clauses and all partial separator assignments. -/
theorem pythonConditionClause_eq
    (fixed : Nat → Option Bool) (clause : List Literal) :
    pythonConditionClause fixed clause =
      conditionClause fixed clause := by
  simpa [pythonConditionClause] using
    pythonConditionLoop_eq fixed clause []

/-- Apply the left-to-right loop to all clauses, dropping satisfied
    clauses exactly as the reference conditioner does. -/
def pythonConditionCNF (fixed : Nat → Option Bool)
    (cnf : CNF) : CNF :=
  cnf.filterMap (pythonConditionClause fixed)

theorem pythonConditionCNF_eq
    (fixed : Nat → Option Bool) (cnf : CNF) :
    pythonConditionCNF fixed cnf = conditionCNF fixed cnf := by
  induction cnf with
  | nil => rfl
  | cons clause rest ih =>
      simp [pythonConditionCNF, conditionCNF,
        pythonConditionClause_eq, ih]

/-- Full source-model correspondence of the iterative Python-style
    conditioning algorithm under a consistent separator assignment. -/
theorem pythonConditionCNF_models_iff
    (fixed : Nat → Option Bool) (cnf : CNF)
    (a : Nat → Bool) (hag : agreesWith fixed a) :
    CNFHolds (pythonConditionCNF fixed cnf) a ↔ CNFHolds cnf a := by
  rw [pythonConditionCNF_eq]
  exact conditionCNF_correct fixed a hag cnf

/-- The actual normalization-aware G14 checker can consume the loop
    output without changing its accepted semantics. -/
theorem pythonConditionCNF_normalized_partition_models_iff
    (fixed : Nat → Option Bool) (cnf : CNF)
    (components : List CNF)
    (h : checkNormalizedPartition
      (pythonConditionCNF fixed cnf) components = true)
    (a : Nat → Bool) (hag : agreesWith fixed a) :
    CNFHolds cnf a ↔
      components.all (fun c =>
        c.all (fun clause => clause.any (signedLitTrue a))) = true := by
  rw [pythonConditionCNF_eq] at h
  exact conditioned_normalized_partition_models_iff
    fixed cnf components h a hag

/-- Assigned false literals are removed; unassigned ones stay ordered. -/
example :
    pythonConditionClause
      (fun v => if v == 1 then some false else none)
      [(1, true), (3, false), (2, true)] =
      some [(3, false), (2, true)] := by decide

/-- A true separator literal discards the entire clause. -/
example :
    pythonConditionClause
      (fun v => if v == 1 then some true else none)
      [(3, false), (1, true), (2, true)] = none := by decide

#print axioms Witnora.G14PythonConditioningLoop.pythonConditionClause_eq
#print axioms Witnora.G14PythonConditioningLoop.pythonConditionCNF_eq
#print axioms Witnora.G14PythonConditioningLoop.pythonConditionCNF_normalized_partition_models_iff

end Witnora.G14PythonConditioningLoop
