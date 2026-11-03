import Witnora.GeneralResolutionIndexed

/-!
# Direct indexed-stream resolution verification

The reference indexed checker expands a compact trace into by-value steps
and then checks the expanded trace a second time. This variant validates
and appends each row in a single executable pass, without constructing an
expanded proof list. The row database is still a persistent List, so random
access and append are not yet O(1). No proof-search complexity is claimed.
-/

namespace Witnora.GeneralResolutionStream

open Witnora.Concrete
open Witnora.G5Extraction
open Witnora.GeneralResolution
open Witnora.GeneralResolutionIndexed

/-- A successful zero-based list lookup always names an existing row. -/
theorem getElem?_mem {α : Type} (xs : List α) (i : Nat) (x : α)
    (h : xs[i]? = some x) : x ∈ xs := by
  induction xs generalizing i with
  | nil =>
      cases i <;> simp at h
  | cons y ys ih =>
      cases i with
      | zero =>
          simp at h
          subst x
          simp
      | succ j =>
          simp at h
          simp [ih j h]

/-- Check each instruction in-place in the current indexed clause database.
    Missing parent rows, wrong pivot signs and missing empty conclusion fail. -/
def checkStream : CNF → List Instruction → Bool
  | database, [] => decide (([] : List Literal) ∈ database)
  | database, ins :: rest =>
      match database[ins.leftID]?, database[ins.rightID]? with
      | some left, some right =>
          if decide ((ins.pivot, true) ∈ left ∧
              (ins.pivot, false) ∈ right) then
            checkStream (database ++ [resolvent left right ins.pivot]) rest
          else false
      | _, _ => false

/-- Every streaming-accepted refutation excludes every model of its
    original CNF, independently of the number and width of clauses. -/
theorem checkStream_sound
    (source : CNF) (trace : List Instruction)
    (h : checkStream source trace = true)
    (a : Nat → Bool) :
    ¬ CNFHolds source a := by
  induction trace generalizing source with
  | nil =>
      intro hmodel
      have hempty : ([] : List Literal) ∈ source := by
        simpa [checkStream] using h
      have hfalse : ([] : List Literal).any (signedLitTrue a) = true :=
        List.all_eq_true.mp hmodel [] hempty
      simp at hfalse
  | cons ins rest ih =>
      cases hl : source[ins.leftID]? with
      | none =>
          simp [checkStream, hl] at h
      | some left =>
          cases hr : source[ins.rightID]? with
          | none =>
              simp [checkStream, hl, hr] at h
          | some right =>
              by_cases hp :
                  (ins.pivot, true) ∈ left ∧ (ins.pivot, false) ∈ right
              · have htail :
                    checkStream
                      (source ++ [resolvent left right ins.pivot])
                      rest = true := by
                    simpa [checkStream, hl, hr, hp] using h
                have hvalid :
                    checkStep source
                      {left := left, right := right, pivot := ins.pivot,
                       output := resolvent left right ins.pivot} = true := by
                  simp [checkStep, getElem?_mem source ins.leftID left hl,
                    getElem?_mem source ins.rightID right hr, hp]
                intro hmodel
                exact ih (source ++ [resolvent left right ins.pivot])
                  htail (checkStep_preserves_models source
                    {left := left, right := right, pivot := ins.pivot,
                     output := resolvent left right ins.pivot}
                    a hvalid hmodel)
              · simp [checkStream, hl, hr, hp] at h

theorem signedStream_unsat
    (raw : List (List Int)) (trace : List Instruction)
    (h : checkStream (Witnora.SignedSerialization.decodeCNF raw) trace = true) :
    ¬ ∃ a, Witnora.SignedSerialization.signedCNFHolds raw a := by
  rintro ⟨a, ha⟩
  exact checkStream_sound _ trace h a
    ((Witnora.SignedSerialization.signedCNFHolds_iff raw a).mp ha)

example :
    checkStream
      [[(1, true)], [(1, false)]]
      [{leftID := 0, rightID := 1, pivot := 1}] = true := by decide

example :
    checkStream
      [[(1, true)], [(1, false)]]
      [{leftID := 100, rightID := 1, pivot := 1}] = false := by decide

#print axioms Witnora.GeneralResolutionStream.signedStream_unsat

end Witnora.GeneralResolutionStream
