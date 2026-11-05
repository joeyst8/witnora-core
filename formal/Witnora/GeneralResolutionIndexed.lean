import Witnora.GeneralResolution

/-!
# Indexed DAG wire format for arbitrary-CNF resolution refutations

The first general checker carries complete parent clauses in each step.
This compact format refers to previously present rows by zero-based IDs;
the Lean decoder reconstructs both parents, computes the exact resolvent,
and routes it through the universally proved reference checker.

Malformed row references and invalid pivot orientations fail closed.
Neither the Python emitter nor a solver's UNSAT verdict is trusted.
This is an executable correctness-by-construction bridge, not an optimized
random-access checker or a polynomial proof-search claim.
-/

namespace Witnora.GeneralResolutionIndexed

open Witnora.Concrete
open Witnora.G5Extraction
open Witnora.GeneralResolution

structure Instruction where
  leftID : Nat
  rightID : Nat
  pivot : Nat
deriving Repr, DecidableEq

/-- Every successful expansion names two existing rows at the time of use. -/
def expand : CNF → List Instruction → Option (List Step)
  | _, [] => some []
  | database, instruction :: rest => do
      let some left := database[instruction.leftID]? | none
      let some right := database[instruction.rightID]? | none
      let pivot := instruction.pivot
      if !(decide ((pivot, true) ∈ left ∧ (pivot, false) ∈ right)) then
        none
      else
        let output := resolvent left right pivot
        let some tail := expand (database ++ [output]) rest | none
        some ({ left := left, right := right, pivot := pivot,
                output := output } :: tail)

/-- Validate a compact indexed trace by kernel-executed expansion and the
    already-proved universal reference checker. -/
def checkIndexed (source : CNF) (trace : List Instruction) : Bool :=
  match expand source trace with
  | none => false
  | some full => checkResolution source full

theorem checkIndexed_sound
    (source : CNF) (trace : List Instruction)
    (h : checkIndexed source trace = true)
    (a : Nat → Bool) :
    ¬ CNFHolds source a := by
  unfold checkIndexed at h
  split at h
  · cases h
  · exact checkResolution_sound source _ h a

theorem signedIndexed_unsat
    (raw : List (List Int)) (trace : List Instruction)
    (h : checkIndexed (Witnora.SignedSerialization.decodeCNF raw) trace = true) :
    ¬ ∃ a, Witnora.SignedSerialization.signedCNFHolds raw a := by
  rintro ⟨a, ha⟩
  exact checkIndexed_sound _ trace h a
    ((Witnora.SignedSerialization.signedCNFHolds_iff raw a).mp ha)

example :
    checkIndexed
      [[(1, true)], [(1, false)]]
      [{leftID := 0, rightID := 1, pivot := 1}] = true := by decide

example :
    checkIndexed
      [[(1, true)], [(1, false)]]
      [{leftID := 0, rightID := 100, pivot := 1}] = false := by decide

example :
    checkIndexed
      [[(1, true)], [(1, false)]]
      [{leftID := 1, rightID := 0, pivot := 1}] = false := by decide

#print axioms Witnora.GeneralResolutionIndexed.signedIndexed_unsat

end Witnora.GeneralResolutionIndexed
