import Witnora.G5EmittedPassAcceptedCertificate
import Witnora.G5PivotPassIndependentReplay

/-!
# Executable indexed pivot selection connected to a verified pass emitter

Scan a finite list of live working-row slots for the first row containing
a requested pivot variable. A selected row is proved to exist at a
candidate slot and to contain the variable. Remove that pivot slot from
the target list, then use the existing proof-carrying pass emitter.

This connects pivot choice to certificate generation. Scheduling every
variable and matching the elimination driver's residual normal form
remain separate obligations.
-/

namespace Witnora.G5IndexedPivotSelection

open Witnora.G5Trace
open Witnora.G5IndexedOperationEmitter
open Witnora.G5IndexedRowValueRefinement
open Witnora.G5EmittedPivotPass
open Witnora.G5PivotPassIndependentReplay
open Witnora.G5RowTableRelation
open Witnora.G5SourceTraceSafety

/-- Finite deterministic first-match pivot selection in the actual
    source working-row view. -/
def choosePivot (initial : List Row) (v : Nat)
    (state : SourceState initial) : List Nat → Option (Nat × Row)
  | [] => none
  | slot :: rest =>
      match workingRow initial state slot with
      | none => choosePivot initial v state rest
      | some row =>
          if v ∈ row.coefficients then some (slot, row)
          else choosePivot initial v state rest

/-- Every selected pivot is one of the candidates and genuinely contains
    the requested variable in the row visible to the source interpreter. -/
theorem choosePivot_sound
    (initial : List Row) (v : Nat)
    (state : SourceState initial) (candidates : List Nat)
    (slot : Nat) (row : Row)
    (h : choosePivot initial v state candidates = some (slot, row)) :
    slot ∈ candidates ∧
      workingRow initial state slot = some row ∧
      v ∈ row.coefficients := by
  induction candidates with
  | nil =>
      simp [choosePivot] at h
  | cons head tail ih =>
      cases hr : workingRow initial state head with
      | none =>
          have ht : choosePivot initial v state tail = some (slot, row) := by
            simpa [choosePivot, hr] using h
          obtain ⟨hmem, hlook, hv⟩ := ih ht
          exact ⟨by simp [hmem], hlook, hv⟩
      | some current =>
          by_cases hv : v ∈ current.coefficients
          · simp [choosePivot, hr, hv] at h
            rcases h with ⟨hslot, hrow⟩
            subst slot
            subst row
            exact ⟨by simp, hr, hv⟩
          · have ht : choosePivot initial v state tail =
                some (slot, row) := by
              simpa [choosePivot, hr, hv] using h
            obtain ⟨hmem, hlook, hvar⟩ := ih ht
            exact ⟨by simp [hmem], hlook, hvar⟩

/-- Select an indexed pivot and emit XORs for every other candidate slot.
    Failure to select a pivot or execute a legal pass returns none. -/
def emitSelectedPass (initial : List Row) (v : Nat)
    (candidates : List Nat) (state : SourceState initial) :
    Option (Nat × List Op × SourceState initial) := do
  let (pivotSlot, _pivotRow) ← choosePivot initial v state candidates
  let targets := candidates.filter (fun slot => slot != pivotSlot)
  let (operations, finished) ←
    emitPass initial v pivotSlot targets state
  return (pivotSlot, operations, finished)

/-- The pivot itself is never a target for its emitted pass. -/
theorem selected_targets_exclude_pivot
    (candidates : List Nat) (pivotSlot : Nat) :
    pivotSlot ∉ candidates.filter (fun slot => slot != pivotSlot) := by
  simp

/-- Every successful selected pass uses a genuine source pivot and
    returns exactly the state obtained from replaying its emitted
    indexed operations. -/
theorem emitSelectedPass_sound
    (initial : List Row) (v : Nat)
    (candidates : List Nat) (state result : SourceState initial)
    (pivotSlot : Nat) (operations : List Op)
    (h : emitSelectedPass initial v candidates state =
      some (pivotSlot, operations, result)) :
    ∃ pivotRow,
      choosePivot initial v state candidates =
        some (pivotSlot, pivotRow) ∧
      pivotSlot ∈ candidates ∧
      workingRow initial state pivotSlot = some pivotRow ∧
      v ∈ pivotRow.coefficients ∧
      executeFrom initial state operations = some result := by
  cases hp : choosePivot initial v state candidates with
  | none =>
      simp [emitSelectedPass, hp] at h
  | some choice =>
      cases choice with
      | mk selected pivotRow =>
          cases he : emitPass initial v selected
              (candidates.filter (fun slot => slot != selected))
              state with
          | none =>
              simp [emitSelectedPass, hp, he] at h
          | some output =>
              cases output with
              | mk produced finished =>
                  simp [emitSelectedPass, hp, he] at h
                  rcases h with ⟨hslot, hops, hresult⟩
                  subst pivotSlot
                  subst operations
                  subst result
                  obtain ⟨hmem, hlook, hv⟩ :=
                    choosePivot_sound initial v state candidates
                      selected pivotRow hp
                  refine ⟨pivotRow, rfl, hmem, hlook, hv, ?_⟩
                  exact emitPass_replays initial v selected
                    (candidates.filter (fun slot => slot != selected))
                    state finished produced he

/-- Returning no pivot means every candidate that resolves to a row
    genuinely lacks the chosen variable. -/
theorem choosePivot_none_absent
    (initial : List Row) (v : Nat)
    (state : SourceState initial) (candidates : List Nat)
    (h : choosePivot initial v state candidates = none) :
    ∀ slot ∈ candidates, ∀ row,
      workingRow initial state slot = some row →
      v ∉ row.coefficients := by
  induction candidates with
  | nil =>
      intro slot hmem
      simp at hmem
  | cons head tail ih =>
      cases hr : workingRow initial state head with
      | none =>
          have ht : choosePivot initial v state tail = none := by
            simpa [choosePivot, hr] using h
          intro slot hmem row hlook
          rcases List.mem_cons.mp hmem with heq | htail
          · subst slot
            simp [hr] at hlook
          · exact ih ht slot htail row hlook
      | some current =>
          by_cases hv : v ∈ current.coefficients
          · simp [choosePivot, hr, hv] at h
          · have ht : choosePivot initial v state tail = none := by
              simpa [choosePivot, hr, hv] using h
            intro slot hmem row hlook
            rcases List.mem_cons.mp hmem with heq | htail
            · subst slot
              have hrow : row = current := by
                exact Option.some.inj (hlook.symm.trans hr)
              subst row
              exact hv
            · exact ih ht slot htail row hlook

/-- If any candidate row contains v, finite indexed pivot selection
    necessarily discovers a pivot rather than silently skipping it. -/
theorem choosePivot_complete
    (initial : List Row) (v : Nat)
    (state : SourceState initial) (candidates : List Nat)
    (slot : Nat) (row : Row)
    (hmem : slot ∈ candidates)
    (hrow : workingRow initial state slot = some row)
    (hv : v ∈ row.coefficients) :
    ∃ chosen chosenRow,
      choosePivot initial v state candidates =
        some (chosen, chosenRow) := by
  cases hp : choosePivot initial v state candidates with
  | none =>
      have hnot := choosePivot_none_absent initial v state
        candidates hp slot hmem row hrow
      exact False.elim (hnot hv)
  | some choice =>
      cases choice with
      | mk chosen chosenRow =>
          exact ⟨chosen, chosenRow, rfl⟩

#print axioms Witnora.G5IndexedPivotSelection.choosePivot_none_absent
#print axioms Witnora.G5IndexedPivotSelection.choosePivot_complete

#print axioms Witnora.G5IndexedPivotSelection.choosePivot_sound
#print axioms Witnora.G5IndexedPivotSelection.selected_targets_exclude_pivot
#print axioms Witnora.G5IndexedPivotSelection.emitSelectedPass_sound

end Witnora.G5IndexedPivotSelection
