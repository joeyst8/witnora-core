import Witnora.G5FullScheduleAbsence
import Witnora.G5ExecutablePassClearance

/-!
# Selected pivot clearance survives the rest of an executable G5 schedule

A successful pivot pass clears the chosen variable from all surviving
candidate slots. Since the full schedule preserves absent variables,
every subsequent pivot pass leaves that selected variable absent from
the survivors of its own pass.
-/

namespace Witnora.G5SelectedPivotPersistence

open Witnora.G5Trace
open Witnora.G5IndexedOperationEmitter
open Witnora.G5IndexedRowValueRefinement
open Witnora.G5IndexedPivotSelection
open Witnora.G5IndexedScheduledEmitter
open Witnora.G5ScheduledAbsenceInvariant
open Witnora.G5FullScheduleAbsence
open Witnora.G5ExecutablePassClearance
open Witnora.G5EmittedPivotPass
open Witnora.G5SourceTraceSafety

/-- Turn the complete executable clearance proof into the source
    working-row absence invariant for the surviving candidates. -/
theorem emitted_pass_clears_remaining
    (initial : List Row) (v pivotSlot : Nat)
    (targets : List Nat)
    (state updated : SourceState initial) (firstOps : List Op)
    (pivotRow : Row)
    (hnd : targets.Nodup)
    (hpivotNot : pivotSlot ∉ targets)
    (hpivot : workingRow initial state pivotSlot = some pivotRow)
    (hv : v ∈ pivotRow.coefficients)
    (hvalid : LiveRefsValid initial state)
    (he : emitPass initial v pivotSlot targets state =
      some (firstOps, updated)) :
    AbsentOn initial v updated targets := by
  have hall := emitPass_clears_all_targets initial v pivotSlot
    targets state updated firstOps pivotRow
    hnd hpivotNot hpivot hv hvalid he
  intro slot hm row hrow
  obtain ⟨newRow, hnew, hnot⟩ := hall slot hm
  have heq : row = newRow :=
    Option.some.inj (hrow.symm.trans hnew)
  subst row
  exact hnot

/-- Once a chosen pivot variable has been cleared from the current
    survivors, no later scheduled elimination can reintroduce it there.
    This theorem concerns the actual emitted source operations, even
    when the later schedule selects and retires other pivot rows. -/
theorem selected_pivot_stays_clear_through_remainder
    (initial : List Row) (v pivotSlot : Nat)
    (remaining targets : List Nat)
    (state updated finished : SourceState initial)
    (firstOps restOps : List Op) (pivotRow : Row)
    (hnd : targets.Nodup)
    (hpivotNot : pivotSlot ∉ targets)
    (hpivot : workingRow initial state pivotSlot = some pivotRow)
    (hv : v ∈ pivotRow.coefficients)
    (hvalid : LiveRefsValid initial state)
    (he : emitPass initial v pivotSlot targets state =
      some (firstOps, updated))
    (hr : emitSchedule initial remaining targets updated =
      some (restOps, finished)) :
    AbsentOn initial v finished targets := by
  have hcleared := emitted_pass_clears_remaining initial v pivotSlot
    targets state updated firstOps pivotRow
    hnd hpivotNot hpivot hv hvalid he
  have hreplay := emitPass_replays initial v pivotSlot
    targets state updated firstOps he
  have hvalidUpdated : LiveRefsValid initial updated :=
    foldlM_preserves_valid initial firstOps state updated hvalid
      (by simpa [executeFrom] using hreplay)
  exact emitSchedule_preserves_absent_candidates initial v
    remaining targets updated finished restOps
    hvalidUpdated hcleared hr

#print axioms Witnora.G5SelectedPivotPersistence.emitted_pass_clears_remaining
#print axioms Witnora.G5SelectedPivotPersistence.selected_pivot_stays_clear_through_remainder

end Witnora.G5SelectedPivotPersistence
