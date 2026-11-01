import Witnora.G5RetiredPivotLedger
import Witnora.G5ExecutablePassClearance

/-!
# Triangularity of actual retired indexed G5 pivot equations

The executable scheduler records pivot rows when selected. Every
subsequent pivot is drawn only from surviving candidate slots, from
which the earlier variable has been eliminated. Because later XOR
passes preserve that absence, the retained pivot ledger is triangular.

This theorem connects the source-indexed emitter to the existing
verified triangular back-substitution model constructor.
-/

namespace Witnora.G5RetiredPivotTriangular

open Witnora.G5Trace
open Witnora.G5Dag
open Witnora.G5BackSubstitution
open Witnora.G5IndexedOperationEmitter
open Witnora.G5IndexedRowValueRefinement
open Witnora.G5IndexedPivotSelection
open Witnora.G5EmittedPivotPass
open Witnora.G5RetiredPivotLedger
open Witnora.G5ExecutablePassClearance
open Witnora.G5ScheduledAbsenceInvariant
open Witnora.G5SourceTraceSafety

private theorem nodup_filter_slots (slots : List Nat)
    (pred : Nat → Bool) (h : slots.Nodup) :
    (slots.filter pred).Nodup := by
  induction slots with
  | nil => simp
  | cons slot rest ih =>
      have hnot : slot ∉ rest := (List.nodup_cons.mp h).1
      have hrest : rest.Nodup := (List.nodup_cons.mp h).2
      simp only [List.filter_cons]
      split
      · apply List.nodup_cons.mpr
        constructor
        · intro hm
          exact hnot (List.mem_filter.mp hm).1
        · exact ih hrest
      · exact ih hrest

/-- Once a variable is absent from all active candidate rows, no later
    pivot row selected by this executable scheduler can mention it. -/
theorem ledger_pivots_preserve_absence
    (initial : List Row) (w : Nat)
    (variables candidates : List Nat)
    (state : SourceState initial) (outcome : PivotOutcome initial)
    (hvalid : LiveRefsValid initial state)
    (habs : AbsentOn initial w state candidates)
    (h : emitScheduleWithPivots initial variables candidates state =
      some outcome) :
    ∀ entry ∈ outcome.pivots, w ∉ entry.2.coefficients := by
  induction variables generalizing candidates state outcome with
  | nil =>
      simp [emitScheduleWithPivots] at h
      subst outcome
      intro entry hm
      simp at hm
  | cons v rest ih =>
      cases hp : choosePivot initial v state candidates with
      | none =>
          have hrest : emitScheduleWithPivots initial rest candidates state =
              some outcome := by
            simpa [emitScheduleWithPivots, hp] using h
          exact ih candidates state outcome hvalid habs hrest
      | some choice =>
          cases choice with
          | mk pivotSlot pivotRow =>
              let targets := candidates.filter (fun slot => slot != pivotSlot)
              obtain ⟨hpivotMem, hpivotRow, _⟩ :=
                choosePivot_sound initial v state candidates
                  pivotSlot pivotRow hp
              have hpivotNot : pivotSlot ∉ targets := by
                simp [targets]
              have htargets : ∀ slot ∈ targets, slot ∈ candidates := by
                intro slot hm
                exact (List.mem_filter.mp hm).1
              cases he : emitPass initial v pivotSlot targets state with
              | none =>
                  simp [emitScheduleWithPivots, hp, targets, he] at h
              | some first =>
                  cases first with
                  | mk firstOps updated =>
                      cases hr : emitScheduleWithPivots initial rest targets updated with
                      | none =>
                          simp [emitScheduleWithPivots, hp, targets, he, hr] at h
                      | some remainder =>
                          simp [emitScheduleWithPivots, hp, targets, he, hr] at h
                          subst outcome
                          have habsUpdated := emitPass_preserves_absent_candidates
                            initial v w pivotSlot targets candidates
                            state updated firstOps pivotRow hpivotMem
                            htargets hpivotNot hpivotRow hvalid habs he
                          have htargetsAbsent :
                              AbsentOn initial w updated targets := by
                            intro slot hm row hrow
                            exact habsUpdated slot (htargets slot hm)
                              row hrow
                          have hreplay := emitPass_replays initial v
                            pivotSlot targets state updated firstOps he
                          have hvalidUpdated : LiveRefsValid initial updated :=
                            foldlM_preserves_valid initial firstOps state
                              updated hvalid
                              (by simpa [executeFrom] using hreplay)
                          have htail := ih targets updated remainder
                            hvalidUpdated htargetsAbsent hr
                          intro entry hm
                          rcases List.mem_cons.mp hm with heq | htailMem
                          · subst entry
                            exact habs pivotSlot hpivotMem pivotRow hpivotRow
                          · exact htail entry htailMem

/-- The complete retired pivot ledger is triangular: each tagged
    variable appears in its own selected pivot row but disappears
    from every later selected pivot row. -/
theorem emitted_pivot_ledger_triangular
    (initial : List Row)
    (variables candidates : List Nat)
    (state : SourceState initial) (outcome : PivotOutcome initial)
    (hnd : candidates.Nodup)
    (hvalid : LiveRefsValid initial state)
    (h : emitScheduleWithPivots initial variables candidates state =
      some outcome) :
    Triangular outcome.pivots := by
  induction variables generalizing candidates state outcome with
  | nil =>
      simp [emitScheduleWithPivots] at h
      subst outcome
      trivial
  | cons v rest ih =>
      cases hp : choosePivot initial v state candidates with
      | none =>
          have hrest : emitScheduleWithPivots initial rest candidates state =
              some outcome := by
            simpa [emitScheduleWithPivots, hp] using h
          exact ih candidates state outcome hnd hvalid hrest
      | some choice =>
          cases choice with
          | mk pivotSlot pivotRow =>
              let targets := candidates.filter (fun slot => slot != pivotSlot)
              have hndTargets : targets.Nodup :=
                nodup_filter_slots candidates
                  (fun slot => slot != pivotSlot) hnd
              have hpivotNot : pivotSlot ∉ targets := by
                simp [targets]
              obtain ⟨_, hpivotRow, hv⟩ :=
                choosePivot_sound initial v state candidates
                  pivotSlot pivotRow hp
              cases he : emitPass initial v pivotSlot targets state with
              | none =>
                  simp [emitScheduleWithPivots, hp, targets, he] at h
              | some first =>
                  cases first with
                  | mk firstOps updated =>
                      cases hr : emitScheduleWithPivots initial rest targets updated with
                      | none =>
                          simp [emitScheduleWithPivots, hp, targets, he, hr] at h
                      | some remainder =>
                          simp [emitScheduleWithPivots, hp, targets, he, hr] at h
                          subst outcome
                          have hcleared := emitted_pass_clears_remaining
                            initial v pivotSlot targets state updated
                            firstOps pivotRow hndTargets hpivotNot
                            hpivotRow hv hvalid he
                          have hreplay := emitPass_replays initial v
                            pivotSlot targets state updated firstOps he
                          have hvalidUpdated : LiveRefsValid initial updated :=
                            foldlM_preserves_valid initial firstOps state
                              updated hvalid
                              (by simpa [executeFrom] using hreplay)
                          have htailAbs := ledger_pivots_preserve_absence
                            initial v rest targets updated remainder
                            hvalidUpdated hcleared hr
                          have htailTri := ih targets updated remainder
                            hndTargets hvalidUpdated hr
                          change v ∈ pivotRow.coefficients ∧
                            (∀ entry ∈ remainder.pivots,
                              v ∉ entry.2.coefficients) ∧
                            Triangular remainder.pivots
                          exact ⟨hv, htailAbs, htailTri⟩

#print axioms Witnora.G5RetiredPivotTriangular.ledger_pivots_preserve_absence
#print axioms Witnora.G5RetiredPivotTriangular.emitted_pivot_ledger_triangular

end Witnora.G5RetiredPivotTriangular
