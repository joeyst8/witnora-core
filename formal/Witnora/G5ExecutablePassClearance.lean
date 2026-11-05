import Witnora.G5ExecutableTargetClearance
import Witnora.G5SourceTraceSafety

/-!
# Full-pass G5 working-row pivot clearance

Generalize the actual single-target clearance and unrelated-slot
preservation theorems to workingRow-level hypotheses, then lift them
through arbitrary finite emitted passes under stable-pivot and
distinct-target conditions. This is the executable normal-form bridge
for contradiction completeness.
-/

namespace Witnora.G5ExecutablePassClearance

open Witnora.G5Trace
open Witnora.G5IndexedOperationEmitter
open Witnora.G5IndexedRowValueRefinement
open Witnora.G5ExecutableTargetClearance
open Witnora.G5EmittedPivotPass
open Witnora.G5SourceTraceSafety

/-- A successfully dereferenced working row yields both its live
    reference and the concrete DAG row lookup witness. -/
theorem workingRow_derefs
    (initial : List Row) (state : SourceState initial)
    (slot : Nat) (row : Row)
    (h : workingRow initial state slot = some row) :
    ∃ ref, state.refs[slot]? = some ref ∧
      state.dag.rows[ref]? = some row := by
  unfold workingRow at h
  cases hr : state.refs[slot]? with
  | none =>
      simp [hr] at h
  | some ref =>
      have hrow : state.dag.rows[ref]? = some row := by
        simpa [hr] using h
      exact ⟨ref, rfl, hrow⟩

/-- Every successful target emitter step clears v, stated only using
    observable working-row lookups rather than internal DAG indices. -/
theorem emitOne_clears_view
    (initial : List Row) (v pivotSlot targetSlot : Nat)
    (state result : SourceState initial) (operations : List Op)
    (pivotRow : Row)
    (hne : targetSlot ≠ pivotSlot)
    (hpivot : workingRow initial state pivotSlot = some pivotRow)
    (hv : v ∈ pivotRow.coefficients)
    (h : emitOne initial v pivotSlot targetSlot state =
      some (operations, result)) :
    ∃ newRow,
      workingRow initial result targetSlot = some newRow ∧
      v ∉ newRow.coefficients := by
  obtain ⟨pivotRef, hpref, hprow⟩ :=
    workingRow_derefs initial state pivotSlot pivotRow hpivot
  cases ht : workingRow initial state targetSlot with
  | none =>
      simp [emitOne, ht] at h
  | some targetRow =>
      obtain ⟨targetRef, htref, htrow⟩ :=
        workingRow_derefs initial state targetSlot targetRow ht
      exact emitOne_clears_target initial v pivotSlot targetSlot
        state result operations pivotRef targetRef pivotRow targetRow
        hne hpref htref hprow htrow hv h

/-- Updating one indexed target preserves any other working-row view,
    for all initially valid live DAG references. -/
theorem emitOne_preserves_other_view
    (initial : List Row) (v pivotSlot targetSlot otherSlot : Nat)
    (state result : SourceState initial) (operations : List Op)
    (pivotRow : Row)
    (hne : targetSlot ≠ pivotSlot)
    (hother : otherSlot ≠ targetSlot)
    (hpivot : workingRow initial state pivotSlot = some pivotRow)
    (hvalid : LiveRefsValid initial state)
    (h : emitOne initial v pivotSlot targetSlot state =
      some (operations, result)) :
    workingRow initial result otherSlot =
      workingRow initial state otherSlot := by
  obtain ⟨pivotRef, hpref, hprow⟩ :=
    workingRow_derefs initial state pivotSlot pivotRow hpivot
  cases ht : workingRow initial state targetSlot with
  | none =>
      simp [emitOne, ht] at h
  | some targetRow =>
      obtain ⟨targetRef, htref, htrow⟩ :=
        workingRow_derefs initial state targetSlot targetRow ht
      exact emitOne_preserves_other_slot initial v pivotSlot
        targetSlot otherSlot state result operations
        pivotRef targetRef pivotRow targetRow hne hother
        hpref htref hprow htrow
        (fun slot ref hr => valid_lookup initial state hvalid slot ref hr)
        h

/-- Accepted single-target emission preserves the live-reference
    invariant through its exact source interpreter replay. -/
theorem emitOne_preserves_valid
    (initial : List Row) (v pivotSlot targetSlot : Nat)
    (state result : SourceState initial) (operations : List Op)
    (hvalid : LiveRefsValid initial state)
    (h : emitOne initial v pivotSlot targetSlot state =
      some (operations, result)) :
    LiveRefsValid initial result := by
  have hrun := emitOne_replays initial v pivotSlot targetSlot
    state result operations h
  exact foldlM_preserves_valid initial operations state result
    hvalid (by simpa [executeFrom] using hrun)

/-- A complete successfully emitted pivot pass preserves every working
    slot excluded from the target list, including the pivot itself. -/
theorem emitPass_preserves_outside
    (initial : List Row) (v pivotSlot otherSlot : Nat)
    (targets : List Nat)
    (state result : SourceState initial) (operations : List Op)
    (pivotRow : Row)
    (hpivotNot : pivotSlot ∉ targets)
    (hotherNot : otherSlot ∉ targets)
    (hpivot : workingRow initial state pivotSlot = some pivotRow)
    (hvalid : LiveRefsValid initial state)
    (h : emitPass initial v pivotSlot targets state =
      some (operations, result)) :
    workingRow initial result otherSlot =
      workingRow initial state otherSlot := by
  induction targets generalizing state result operations with
  | nil =>
      simp [emitPass] at h
      rcases h with ⟨hops, hresult⟩
      subst result
      rfl
  | cons target rest ih =>
      have htargetPivot : target ≠ pivotSlot := by
        intro heq
        subst target
        exact hpivotNot (by simp)
      have htargetOther : otherSlot ≠ target := by
        intro heq
        subst otherSlot
        exact hotherNot (by simp)
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
                      rcases h with ⟨hops, hresult⟩
                      subst result
                      have hpivotUpdated :
                          workingRow initial updated pivotSlot =
                            some pivotRow := by
                        rw [emitOne_preserves_other_view initial v
                          pivotSlot target pivotSlot state updated
                          firstOps pivotRow htargetPivot
                          (Ne.symm htargetPivot) hpivot hvalid hf]
                        exact hpivot
                      have hupdatedValid := emitOne_preserves_valid
                        initial v pivotSlot target state updated
                        firstOps hvalid hf
                      have hpivotRest : pivotSlot ∉ rest := by
                        intro hm
                        exact hpivotNot (by simp [hm])
                      have hotherRest : otherSlot ∉ rest := by
                        intro hm
                        exact hotherNot (by simp [hm])
                      have htail := ih updated finished restOps
                        hpivotRest hotherRest hpivotUpdated
                        hupdatedValid hr
                      have hfirst := emitOne_preserves_other_view
                        initial v pivotSlot target otherSlot
                        state updated firstOps pivotRow htargetPivot
                        htargetOther hpivot hvalid hf
                      exact htail.trans hfirst

/-- Full executable pass clearance: every distinct target slot ends with
    a dereferenceable row that excludes the chosen pivot variable.
    The pivot is never in the target list and stays unchanged. -/
theorem emitPass_clears_all_targets
    (initial : List Row) (v pivotSlot : Nat)
    (targets : List Nat)
    (state result : SourceState initial) (operations : List Op)
    (pivotRow : Row)
    (hnd : targets.Nodup)
    (hpivotNot : pivotSlot ∉ targets)
    (hpivot : workingRow initial state pivotSlot = some pivotRow)
    (hvPivot : v ∈ pivotRow.coefficients)
    (hvalid : LiveRefsValid initial state)
    (h : emitPass initial v pivotSlot targets state =
      some (operations, result)) :
    ∀ slot ∈ targets, ∃ row,
      workingRow initial result slot = some row ∧
      v ∉ row.coefficients := by
  induction targets generalizing state result operations with
  | nil =>
      intro slot hm
      simp at hm
  | cons target rest ih =>
      have htargetPivot : target ≠ pivotSlot := by
        intro heq
        subst target
        exact hpivotNot (by simp)
      have hpivotRest : pivotSlot ∉ rest := by
        intro hm
        exact hpivotNot (by simp [hm])
      have htargetRest : target ∉ rest := (List.nodup_cons.mp hnd).1
      have hrestNodup : rest.Nodup := (List.nodup_cons.mp hnd).2
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
                      rcases h with ⟨hops, hresult⟩
                      subst result
                      have hfirst := emitOne_clears_view initial v
                        pivotSlot target state updated firstOps
                        pivotRow htargetPivot hpivot hvPivot hf
                      have hpivotUpdated :
                          workingRow initial updated pivotSlot =
                            some pivotRow := by
                        rw [emitOne_preserves_other_view initial v
                          pivotSlot target pivotSlot state updated
                          firstOps pivotRow htargetPivot
                          (Ne.symm htargetPivot) hpivot hvalid hf]
                        exact hpivot
                      have hupdatedValid := emitOne_preserves_valid
                        initial v pivotSlot target state updated
                        firstOps hvalid hf
                      have htail := ih updated finished restOps
                        hrestNodup hpivotRest hpivotUpdated
                        hupdatedValid hr
                      intro slot hmem
                      rcases List.mem_cons.mp hmem with hslot | hrest
                      · subst slot
                        have hkeep := emitPass_preserves_outside
                          initial v pivotSlot target rest
                          updated finished restOps pivotRow
                          hpivotRest htargetRest hpivotUpdated
                          hupdatedValid hr
                        rw [hkeep]
                        exact hfirst
                      · exact htail slot hrest

#print axioms Witnora.G5ExecutablePassClearance.emitPass_clears_all_targets

#print axioms Witnora.G5ExecutablePassClearance.emitPass_preserves_outside

#print axioms Witnora.G5ExecutablePassClearance.workingRow_derefs
#print axioms Witnora.G5ExecutablePassClearance.emitOne_clears_view
#print axioms Witnora.G5ExecutablePassClearance.emitOne_preserves_other_view
#print axioms Witnora.G5ExecutablePassClearance.emitOne_preserves_valid

end Witnora.G5ExecutablePassClearance
