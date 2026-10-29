import Witnora.DIMACSTokens

/-!
# Executable ASCII decimal DIMACS token refinement

A literal lexeme is supplied as a list of ASCII codes. The arithmetic parser
is defined using kernel-reducible Nat operations, avoiding opaque String.toInt?.
Selecting token spans from an entire UTF-8 document is a separate obligation.
-/

namespace Witnora.DIMACSLexemes

def isDigit (code : Nat) : Bool :=
  decide (48 ≤ code ∧ code ≤ 57)

def decimalValue (digits : List Nat) : Option Nat :=
  if digits.isEmpty || !(digits.all isDigit) then none
  else some (digits.foldl (fun acc code => acc * 10 + (code - 48)) 0)

def parseSigned (codes : List Nat) : Option Int :=
  match codes with
  | 45 :: digits => (decimalValue digits).map (fun n => -(Int.ofNat n))
  | digits => (decimalValue digits).map Int.ofNat

/-- Compare every original ASCII decimal lexeme to its signed integer. -/
def checkLexemes (lexemes : List (List Nat)) (tokens : List Int) : Bool :=
  decide (lexemes.map parseSigned = tokens.map some)

theorem checkLexemes_sound (lexemes : List (List Nat)) (tokens : List Int)
    (h : checkLexemes lexemes tokens = true) :
    lexemes.map parseSigned = tokens.map some := by
  simpa [checkLexemes] using h

example : parseSigned [49, 50] = some 12 := by decide
example : parseSigned [45, 51] = some (-3) := by decide
example : parseSigned [48] = some 0 := by decide
example : parseSigned [45] = none := by decide
example : parseSigned [49, 120] = none := by decide
example : checkLexemes [[49, 50], [45, 51], [48]] [12, -3, 0] = true := by decide
example : checkLexemes [[49], [48]] [1] = false := by decide

#print axioms Witnora.DIMACSLexemes.checkLexemes_sound

end Witnora.DIMACSLexemes
