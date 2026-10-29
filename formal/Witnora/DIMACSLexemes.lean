import Witnora.DIMACSTokens

/-!
# Decimal DIMACS token refinement

The Lean parser independently parses each provided literal-token spelling.
The preceding operation that identifies token spans in arbitrary UTF-8 text
remains outside this theorem and must not be silently treated as verified.
-/

namespace Witnora.DIMACSLexemes

/-- Compare Lean's parsed signed decimals to the supplied integer stream. -/
def checkLexemes (spellings : List String) (tokens : List Int) : Bool :=
  decide (spellings.map String.toInt? = tokens.map some)

/-- An accepted stream has exactly the Lean decimal values, with no failed
    lexical conversion or additional/missing integer tokens. -/
theorem checkLexemes_sound (spellings : List String) (tokens : List Int)
    (h : checkLexemes spellings tokens = true) :
    spellings.map String.toInt? = tokens.map some := by
  simpa [checkLexemes] using h

example : checkLexemes ["12", "-3", "0"] [12, -3, 0] = true := by decide
example : checkLexemes ["12", "not-a-number"] [12, 3] = false := by decide
example : checkLexemes ["1", "0"] [1] = false := by decide

#print axioms Witnora.DIMACSLexemes.checkLexemes_sound

end Witnora.DIMACSLexemes
