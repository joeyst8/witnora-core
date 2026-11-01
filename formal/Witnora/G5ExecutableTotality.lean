import Witnora.G5CompleteCheckedCertificate
import Witnora.G5ExecutablePassClearance
import Witnora.G5RetiredPivotLedger

/-!
# Fail-free executable indexed G5 scheduling from readable candidates

The source emitter can return none when a working slot is missing or an
indexed XOR fails. Under valid live references and a readable candidate
set, every chosen pivot and target resolves to concrete DAG rows, every
target-first XOR uses distinct slots, and every generated step succeeds.

The resulting proof constructs a successful complete pivot ledger run
for every finite requested variable schedule. An initial-state
readability theorem then removes the remaining startup premise.
-/

namespace Witnora.G5ExecutableTotality

open Witnora.G5Trace
open Witnora.G5IndexedOperationEmitter
open Witnora.G5IndexedRowValueRefinement
open Witnora.G5IndexedPivotSelection
open Witnora.G5IndexedScheduledEmitter
open Witnora.G5EmittedPivotPass
open Witnora.G5RetiredPivotLedger
open Witnora.G5ExecutablePassClearance
open Witnora.G5ExecutableTargetClearance
open Witnora.G5SourceStepSemantics
open Witnora.G5SourceTraceSafety

/-- Every active candidate slot has a concrete working row. -/
def ReadableCandidates (initial : List Row)
    (state : SourceState initial) (candidates : List Nat) : Prop :=
  ∀ slot ∈ candidates, ∃ row,
    workingRow initial state slot = some row

/-- Every target-first emitted step succeeds when the pivot and target
    both resolve to live rows and the two slot indices are distinct. -/
theorem emitOne_total
    (initial : List Row) (v pivotSlot targetSlot : Nat)
    (state : SourceState initial) (pivotRow targetRow : Row)
    (hne : targetSlot ≠ pivotSlot)
    (hpivot : workingRow initial state pivotSlot = some pivotRow)
    (htarget : workingRow initial state targetSlot = some targetRow) :
    ∃ operations result,
      emitOne initial v pivotSlot targetSlot state =
        some (operations, result) := by
  obtain ⟨pivotRef, hpref, hprow⟩ :=
    workingRow_derefs initial state pivotSlot pivotRow hpivot
  obtain ⟨targetRef, htref, htrow⟩ :=
    workingRow_derefs initial state targetSlot targetRow htarget
  by_cases hv : v ∈ targetRow.coefficients
  · have hstep := xor_step_exact initial state targetSlot pivotSlot
      targetRef pivotRef targetRow pivotRow hne htref hpref htrow hprow
    refine ⟨[.addRowXor targetSlot pivotSlot],
      xorUpdatedState initial state targetSlot targetRef pivotRef
        targetRow pivotRow htrow hprow, ?_⟩
    simp [emitOne, htarget, hv, hstep]
  · exact ⟨[], state, by simp [emitOne, htarget, hv]⟩

/-- An emitted target update leaves all candidate slots readable.
    It either retains the old target or replaces it with an exact XOR
    row, while all other candidate views remain unchanged. -/
theorem emitOne_preserves_readability
    (initial : List Row) (v pivotSlot targetSlot : Nat)
    (candidates : List Nat)
    (state updated : SourceState initial) (operations : List Op)
    (pivotRow : Row)
    (hne : targetSlot ≠ pivotSlot)
    (hpivot : workingRow initial state pivotSlot = some pivotRow)
    (hv : v ∈ pivotRow.coefficients)
    (hvalid : LiveRefsValid initial state)
    (hread : ReadableCandidates initial state candidates)
    (h : emitOne initial v pivotSlot targetSlot state =
      some (operations, updated)) :
    ReadableCandidates initial updated candidates := by
  have htarget := emitOne_clears_view initial v pivotSlot targetSlot
    state updated operations pivotRow hne hpivot hv h
  intro slot hm
  by_cases heq : slot = targetSlot
  · subst slot
    obtain ⟨row, hrow, _⟩ := htarget
    exact ⟨row, hrow⟩
  · obtain ⟨row, hrow⟩ := hread slot hm
    refine ⟨row, ?_⟩
    rw [emitOne_preserves_other_view initial v pivotSlot targetSlot
      slot state updated operations pivotRow hne heq
      hpivot hvalid h]
    exact hrow

/-- A full pivot pass cannot fail on a valid readable candidate set.
    Its final state retains readable candidates, valid references, and
    an unchanged pivot value needed by later steps. -/
theorem emitPass_total_with_invariants
    (initial : List Row) (v pivotSlot : Nat)
    (targets candidates : List Nat)
    (state : SourceState initial) (pivotRow : Row)
    (hpivotNot : pivotSlot ∉ targets)
    (htargets : ∀ slot ∈ targets, slot ∈ candidates)
    (hpivot : workingRow initial state pivotSlot = some pivotRow)
    (hv : v ∈ pivotRow.coefficients)
    (hvalid : LiveRefsValid initial state)
    (hread : ReadableCandidates initial state candidates) :
    ∃ operations result,
      emitPass initial v pivotSlot targets state =
        some (operations, result) ∧
      ReadableCandidates initial result candidates ∧
      LiveRefsValid initial result ∧
      workingRow initial result pivotSlot = some pivotRow := by
  induction targets generalizing state with
  | nil =>
      refine ⟨[], state, rfl, hread, hvalid, hpivot⟩
  | cons target rest ih =>
      have htargetMem : target ∈ candidates :=
        htargets target (by simp)
      obtain ⟨targetRow, htarget⟩ := hread target htargetMem
      have hne : target ≠ pivotSlot := by
        intro heq
        subst target
        exact hpivotNot (by simp)
      obtain ⟨firstOps, updated, hf⟩ := emitOne_total
        initial v pivotSlot target state pivotRow targetRow
        hne hpivot htarget
      have hreadUpdated := emitOne_preserves_readability initial
        v pivotSlot target candidates state updated firstOps
        pivotRow hne hpivot hv hvalid hread hf
      have hvalidUpdated := emitOne_preserves_valid initial
        v pivotSlot target state updated firstOps hvalid hf
      have hpivotUpdated : workingRow initial updated pivotSlot =
          some pivotRow := by
        rw [emitOne_preserves_other_view initial v pivotSlot target
          pivotSlot state updated firstOps pivotRow hne
          (Ne.symm hne) hpivot hvalid hf]
        exact hpivot
      have hpivotRest : pivotSlot ∉ rest := by
        intro hm
        exact hpivotNot (by simp [hm])
      have htargetsRest : ∀ slot ∈ rest, slot ∈ candidates := by
        intro slot hm
        exact htargets slot (by simp [hm])
      obtain ⟨restOps, finished, hr, hreadFinal, hvalidFinal, hpFinal⟩ :=
        ih updated hpivotRest htargetsRest hpivotUpdated
          hv hvalidUpdated hreadUpdated
      refine ⟨firstOps ++ restOps, finished, ?_,
        hreadFinal, hvalidFinal, hpFinal⟩
      simp [emitPass, hf, hr]

/-- Every finite pivot-variable schedule succeeds on a candidate set
    with valid readable source rows; no assumption about finding any
    pivot is required because missing pivots are skipped safely. -/
theorem pivot_ledger_schedule_total
    (initial : List Row)
    (variables candidates : List Nat)
    (state : SourceState initial)
    (hvalid : LiveRefsValid initial state)
    (hread : ReadableCandidates initial state candidates) :
    ∃ outcome : PivotOutcome initial,
      emitScheduleWithPivots initial variables candidates state =
        some outcome := by
  induction variables generalizing candidates state with
  | nil =>
      exact ⟨⟨[], state, candidates, []⟩, rfl⟩
  | cons v rest ih =>
      cases hp : choosePivot initial v state candidates with
      | none =>
          obtain ⟨outcome, hout⟩ := ih candidates state hvalid hread
          exact ⟨outcome, by
            simpa [emitScheduleWithPivots, hp] using hout⟩
      | some choice =>
          cases choice with
          | mk pivotSlot pivotRow =>
              let targets := candidates.filter (fun slot => slot != pivotSlot)
              obtain ⟨hpivotMem, hpivot, hv⟩ :=
                choosePivot_sound initial v state candidates
                  pivotSlot pivotRow hp
              have hpivotNot : pivotSlot ∉ targets := by
                simp [targets]
              have htargets : ∀ slot ∈ targets, slot ∈ candidates := by
                intro slot hm
                exact (List.mem_filter.mp hm).1
              obtain ⟨firstOps, updated, he, hreadUpdated, hvalidUpdated, _⟩ :=
                emitPass_total_with_invariants initial v pivotSlot
                  targets candidates state pivotRow hpivotNot
                  htargets hpivot hv hvalid hread
              have hreadTargets : ReadableCandidates initial updated
                  targets := by
                intro slot hm
                exact hreadUpdated slot (htargets slot hm)
              obtain ⟨remainder, hr⟩ :=
                ih targets updated hvalidUpdated hreadTargets
              refine ⟨{
                operations := firstOps ++ remainder.operations
                finalState := remainder.finalState
                survivors := remainder.survivors
                pivots := (v, pivotRow) :: remainder.pivots
              }, ?_⟩
              simp [emitScheduleWithPivots, hp, targets, he, hr]

#print axioms Witnora.G5ExecutableTotality.emitOne_total
#print axioms Witnora.G5ExecutableTotality.emitPass_total_with_invariants
#print axioms Witnora.G5ExecutableTotality.pivot_ledger_schedule_total

end Witnora.G5ExecutableTotality
