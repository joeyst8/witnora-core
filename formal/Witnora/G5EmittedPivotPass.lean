import Witnora.G5DriverTargetEmission

/-!
# Executable source-indexed G5 pivot-pass emitter

Walk a finite list of target row slots. If a target contains the pivot
variable, append the actual ADD_ROW_XOR operation and the corresponding
proof-carrying DAG row. Otherwise leave the state unchanged.

The main theorem proves every emitted pass result is *exactly* what
replaying its returned operation sequence on the source interpreter
produces. Failed or invalid operations fail closed.
-/

namespace Witnora.G5EmittedPivotPass

open Witnora.G5Trace
open Witnora.G5IndexedOperationEmitter
open Witnora.G5IndexedRowValueRefinement

abbrev Op := Witnora.G5IndexedBridge.Operation

def executeFrom (initial : List Row) (state : SourceState initial)
    (operations : List Op) : Option (SourceState initial) :=
  operations.foldlM (fun s op => s.step initial op) state

/-- Generate zero or one source operation for a target, obtaining the
    updated source state from the actual proof-carrying interpreter. -/
def emitOne (initial : List Row) (v pivotSlot targetSlot : Nat)
    (state : SourceState initial) :
    Option (List Op × SourceState initial) :=
  match workingRow initial state targetSlot with
  | none => none
  | some targetRow =>
      if v ∈ targetRow.coefficients then
        (state.step initial (.addRowXor targetSlot pivotSlot)).map
          (fun updated => ([.addRowXor targetSlot pivotSlot], updated))
      else some ([], state)

/-- Iterate an entire finite pivot pass, retaining the emitted operation
    sequence alongside the proof-backed final source state. -/
def emitPass (initial : List Row) (v pivotSlot : Nat) :
    List Nat → SourceState initial →
      Option (List Op × SourceState initial)
  | [], state => some ([], state)
  | target :: targets, state => do
      let (firstOps, updated) ← emitOne initial v pivotSlot target state
      let (restOps, finished) ← emitPass initial v pivotSlot targets updated
      return (firstOps ++ restOps, finished)

/-- Source replay composes across concatenated operation lists. -/
theorem executeFrom_append
    (initial : List Row) (state : SourceState initial)
    (first second : List Op) :
    executeFrom initial state (first ++ second) =
      (executeFrom initial state first).bind
        (fun updated => executeFrom initial updated second) := by
  induction first generalizing state with
  | nil => rfl
  | cons op rest ih =>
      cases hs : state.step initial op with
      | none =>
          simp [executeFrom, List.foldlM_cons, hs]
      | some updated =>
          simp [executeFrom, List.foldlM_cons, hs]
          exact ih updated

/-- Every successfully emitted target operation replays exactly to the
    returned proof-carrying source state. -/
theorem emitOne_replays
    (initial : List Row) (v pivotSlot targetSlot : Nat)
    (state result : SourceState initial) (operations : List Op)
    (h : emitOne initial v pivotSlot targetSlot state =
      some (operations, result)) :
    executeFrom initial state operations = some result := by
  cases hr : workingRow initial state targetSlot with
  | none =>
      simp [emitOne, hr] at h
  | some targetRow =>
      by_cases hv : v ∈ targetRow.coefficients
      · cases hs : state.step initial (.addRowXor targetSlot pivotSlot) with
        | none =>
            simp [emitOne, hr, hv, hs] at h
        | some updated =>
            simp [emitOne, hr, hv, hs] at h
            cases h
            simp [executeFrom, List.foldlM_cons, hs]
      · simp [emitOne, hr, hv] at h
        cases h
        rfl

/-- For every finite target list, including arbitrarily long lists,
    replaying all generated source operations reproduces the emitter's
    exact final proof-carrying state. -/
theorem emitPass_replays
    (initial : List Row) (v pivotSlot : Nat)
    (targets : List Nat) (state result : SourceState initial)
    (operations : List Op)
    (h : emitPass initial v pivotSlot targets state =
      some (operations, result)) :
    executeFrom initial state operations = some result := by
  induction targets generalizing state operations with
  | nil =>
      simp [emitPass] at h
      cases h
      rfl
  | cons target rest ih =>
      cases hf : emitOne initial v pivotSlot target state with
      | none =>
          simp [emitPass, hf] at h
      | some first =>
          cases first with
          | mk firstOps updated =>
              cases hr : emitPass initial v pivotSlot rest updated with
              | none =>
                  simp [emitPass, hf, hr] at h
              | some second =>
                  cases second with
                  | mk restOps finished =>
                      simp [emitPass, hf, hr] at h
                      cases h
                      rw [executeFrom_append]
                      rw [emitOne_replays initial v pivotSlot target
                        state updated firstOps hf]
                      exact ih updated restOps hr

#print axioms Witnora.G5EmittedPivotPass.executeFrom_append
#print axioms Witnora.G5EmittedPivotPass.emitOne_replays
#print axioms Witnora.G5EmittedPivotPass.emitPass_replays

end Witnora.G5EmittedPivotPass
