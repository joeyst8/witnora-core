import Witnora.G5ExecutablePassClearance
import Witnora.G5IndexedScheduledEmitter

/-!
# Persistent absence of eliminated variables in indexed G5 execution

When a variable has already disappeared from every candidate working
row, subsequent target-first XOR operations among those candidates
cannot reintroduce it. This file establishes the source-level
candidate-set invariant and lifts it to generated pivot passes.
-/

namespace Witnora.G5ScheduledAbsenceInvariant

open Witnora.G5Trace
open Witnora.G5IndexedOperationEmitter
open Witnora.G5IndexedRowValueRefinement
open Witnora.G5IndexedViewSimulation
open Witnora.G5ExecutablePassClearance
open Witnora.G5EmittedPivotPass
open Witnora.G5SourceStepSemantics
open Witnora.G5SourceTraceSafety
open Witnora.G5IndexedScheduledEmitter

/-- Every candidate slot that resolves to a row excludes v. -/
def AbsentOn (initial : List Row) (v : Nat)
    (state : SourceState initial) (slots : List Nat) : Prop :=
  ∀ slot ∈ slots, ∀ row,
    workingRow initial state slot = some row →
      v ∉ row.coefficients

/-- XOR of two rows that both omit v still omits v, independent of
    coefficient ordering and duplicate coefficients. -/
theorem xorRow_preserves_absence
    (v : Nat) (left right : Row)
    (hl : v ∉ left.coefficients)
    (hr : v ∉ right.coefficients) :
    v ∉ (xorRow left right).coefficients := by
  intro hbad
  have hx := (mem_xorCoefficients
    left.coefficients right.coefficients v).mp hbad
  rcases hx with ⟨hm, _⟩ | ⟨hm, _⟩
  · exact hl hm
  · exact hr hm

/-- A single emitted target update among candidates cannot reintroduce
    a variable already absent from all candidate working rows. -/
theorem emitOne_preserves_absent_candidates
    (initial : List Row) (w v pivotSlot targetSlot : Nat)
    (candidates : List Nat)
    (state result : SourceState initial) (operations : List Op)
    (pivotRow : Row)
    (hpivotMem : pivotSlot ∈ candidates)
    (htargetMem : targetSlot ∈ candidates)
    (hne : targetSlot ≠ pivotSlot)
    (hpivot : workingRow initial state pivotSlot = some pivotRow)
    (hvalid : LiveRefsValid initial state)
    (habs : AbsentOn initial v state candidates)
    (h : emitOne initial w pivotSlot targetSlot state =
      some (operations, result)) :
    AbsentOn initial v result candidates := by
  obtain ⟨pivotRef, hpref, hprow⟩ :=
    workingRow_derefs initial state pivotSlot pivotRow hpivot
  cases ht : workingRow initial state targetSlot with
  | none =>
      simp [emitOne, ht] at h
  | some targetRow =>
      obtain ⟨targetRef, htref, htrow⟩ :=
        workingRow_derefs initial state targetSlot targetRow ht
      by_cases hactive : w ∈ targetRow.coefficients
      · cases hs : state.step initial (.addRowXor targetSlot pivotSlot) with
        | none =>
            simp [emitOne, ht, hactive, hs] at h
        | some updated =>
            simp [emitOne, ht, hactive, hs] at h
            rcases h with ⟨hops, hresult⟩
            subst result
            have hexact := xor_step_exact initial state
              targetSlot pivotSlot targetRef pivotRef
              targetRow pivotRow hne htref hpref htrow hprow
            have heq : updated =
                xorUpdatedState initial state targetSlot targetRef
                  pivotRef targetRow pivotRow htrow hprow :=
              Option.some.inj (hs.symm.trans hexact)
            subst updated
            unfold AbsentOn at habs ⊢
            intro slot hmem row hlook
            by_cases hslot : slot = targetSlot
            · subst slot
              have hnew := xor_target_has_exact_new_row initial state
                targetSlot targetRef pivotRef targetRow pivotRow
                htref htrow hprow
              have hrow : row = xorRow targetRow pivotRow :=
                Option.some.inj (hlook.symm.trans hnew)
              subst row
              exact xorRow_preserves_absence v targetRow pivotRow
                (habs targetSlot htargetMem targetRow ht)
                (habs pivotSlot hpivotMem pivotRow hpivot)
            · have hslots := xor_all_slots initial state targetSlot
                targetRef pivotRef targetRow pivotRow htref htrow
                hprow (fun s ref hr =>
                  valid_lookup initial state hvalid s ref hr) slot
              have hold : workingRow initial state slot =
                  some row := by
                simpa [hslot] using hslots.symm.trans hlook
              exact habs slot hmem row hold
      · simp [emitOne, ht, hactive] at h
        rcases h with ⟨hops, hresult⟩
        subst result
        exact habs

#print axioms Witnora.G5ScheduledAbsenceInvariant.xorRow_preserves_absence
#print axioms Witnora.G5ScheduledAbsenceInvariant.emitOne_preserves_absent_candidates

end Witnora.G5ScheduledAbsenceInvariant
