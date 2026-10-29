import Witnora.SignedSerialization

/-!
# DIMACS integer-token boundary

DIMACS clause terminators are zero; signed literals themselves cannot be zero.
This checker validates that a claimed clause segmentation exactly reconstructs
the original signed integer token stream, including every terminator.

The preceding UTF-8/whitespace/header lexer is a separate refinement obligation.
-/

namespace Witnora.DIMACSTokens

open Witnora.SignedSerialization

/-- The canonical stream of signed clauses with zero delimiters. -/
def serialize (clauses : List (List Int)) : List Int :=
  clauses.flatMap (fun clause => clause ++ [0])

def validClauses (clauses : List (List Int)) : Bool :=
  clauses.all (fun clause => clause.all validSigned)

/-- Fail closed on any missing, extra, or embedded zero terminator. -/
def checkStream (tokens : List Int) (clauses : List (List Int)) : Bool :=
  decide (tokens = serialize clauses) && validClauses clauses

theorem checkStream_sound (tokens : List Int) (clauses : List (List Int))
    (h : checkStream tokens clauses = true) :
    tokens = serialize clauses ∧
      ∀ clause ∈ clauses, ∀ lit ∈ clause, lit ≠ 0 := by
  have hparts : decide (tokens = serialize clauses) = true ∧
      validClauses clauses = true := by
    exact Bool.and_eq_true.mp h
  constructor
  · exact of_decide_true hparts.1
  · intro clause hc lit hl
    have hc' : clause.all validSigned = true :=
      List.all_eq_true.mp hparts.2 clause hc
    have hl' : validSigned lit = true :=
      List.all_eq_true.mp hc' lit hl
    exact of_decide_true hl'

example : checkStream [2, 1, 0, -1, 0, 0]
    [[2, 1], [-1], []] = true := by decide

example : checkStream [2, 1, 0, -1, 0]
    [[2, 1], [-1], []] = false := by decide

example : checkStream [1, 0] [[1, 0]] = false := by decide

#print axioms Witnora.DIMACSTokens.checkStream_sound

end Witnora.DIMACSTokens
