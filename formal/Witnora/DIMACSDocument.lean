import Witnora.DIMACSLexemes

/-!
# Restricted ASCII DIMACS document parser

An executable, independent parser for the DIMACS source *character codes*.
It recognizes a single `p cnf N M` header, whole-line `c` comments,
ASCII whitespace and signed decimal clause tokens, and checks declared
variable and clause bounds. It deliberately rejects non-ASCII text and
unsupported integer spellings. The caller must supply the actual input bytes,
not tokens already selected by Python.
-/

namespace Witnora.DIMACSDocument

open Witnora.DIMACSLexemes

def whitespace (code : Nat) : Bool :=
  code == 9 || code == 10 || code == 11 || code == 12 ||
    code == 13 || code == 32

/-- Partition a list at each delimiter, keeping empty fields. -/
def splitByte (delimiter : Nat) : List Nat → List (List Nat)
  | [] => [[]]
  | x :: xs =>
      if x == delimiter then [] :: splitByte delimiter xs
      else
        match splitByte delimiter xs with
        | [] => [[x]]
        | word :: rest => (x :: word) :: rest

def wordsAux : List Nat → List Nat → List (List Nat) → List (List Nat)
  | [], current, out =>
      if current.isEmpty then out.reverse else (current.reverse :: out).reverse
  | x :: xs, current, out =>
      if whitespace x then
        if current.isEmpty then wordsAux xs [] out
        else wordsAux xs [] (current.reverse :: out)
      else wordsAux xs (x :: current) out

def words (line : List Nat) : List (List Nat) := wordsAux line [] []

def parseHeader : List (List Nat) → Option (Nat × Nat)
  | [[112], [99, 110, 102], vars, clauses] => do
      let n ← decimalValue vars
      let m ← decimalValue clauses
      pure (n, m)
  | _ => none

/-- Header state: bound on variables, declared clause count, accumulated token stream. -/
def parseLines : List (List Nat) → Option (Nat × Nat × List Int) →
    Option (Nat × Nat × List Int)
  | [], state => state
  | line :: rest, state =>
      let fields := words line
      match fields with
      | [] => parseLines rest state
      | first :: _ =>
          if first.head? == some 99 then parseLines rest state
          else if first == [112] then
            match state, parseHeader fields with
            | none, some (n, m) => parseLines rest (some (n, m, []))
            | _, _ => none
          else
            match state with
            | none => none
            | some (n, m, tokens) =>
                match fields.mapM parseSigned with
                | none => none
                | some next =>
                    if next.all (fun lit => decide (lit.natAbs ≤ n)) then
                      parseLines rest (some (n, m, tokens ++ next))
                    else none

/-- Parse the complete ASCII source, including clause header count. -/
def parseDocument (source : List Nat) : Option (List Int) := do
  if !(source.all (fun byte => decide (byte < 128))) then none
  else
    let (_, declared, tokens) ← parseLines (splitByte 10 source) none
    if decide ((tokens.filter (· == 0)).length = declared) then
      some tokens
    else none

def checkDocument (source : List Nat) (tokens : List Int) : Bool :=
  decide (parseDocument source = some tokens)

theorem checkDocument_sound (source : List Nat) (tokens : List Int)
    (h : checkDocument source tokens = true) :
    parseDocument source = some tokens := by
  simpa [checkDocument] using h

example : parseDocument
    [99, 32, 105, 110, 116, 114, 111, 10,
     112, 32, 99, 110, 102, 32, 50, 32, 50, 10,
     49, 32, 48, 10, 45, 50, 32, 48, 10] =
    some [1, 0, -2, 0] := by decide

example : parseDocument
    [112, 32, 99, 110, 102, 32, 49, 32, 49, 10, 50, 32, 48, 10] =
    none := by decide

example : parseDocument
    [112, 32, 99, 110, 102, 32, 49, 32, 50, 10, 49, 32, 48, 10] =
    none := by decide

#print axioms Witnora.DIMACSDocument.checkDocument_sound

end Witnora.DIMACSDocument
