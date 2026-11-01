import Witnora.G5GlobalRowModelInvariant
import Witnora.G5PivotPassIndependentReplay

/-!
# Global model preservation of the executable scheduled G5 emitter

The finite indexed elimination scheduler emits only ADD_ROW_XOR
operations. Combining this structural invariant with independent replay
and the reversible XOR model theorem proves that every successful full
variable schedule preserves the exact set of satisfying assignments
of the original row system.
-/

namespace Witnora.G5ScheduledModelPreservation

open Witnora.G5Trace
open Witnora.G5IndexedOperationEmitter
open Witnora.G5EmittedPivotPass
open Witnora.G5IndexedPivotSelection
open Witnora.G5IndexedScheduledEmitter
open Witnora.G5FiniteTraceCorrespondence
open Witnora.G5GlobalRowModelInvariant
open Witnora.G5RowTableRelation
open Witnora.G5SourceTraceSafety

def SourceXorOnly (op : Op) : Prop :=
  ∃ target source, op = .addRowXor target source

theorem emitOne_only_xors
    (initial : List Row) (v pivotSlot targetSlot : Nat)
    (state result : SourceState initial) (operations : List Op)
    (h : emitOne initial v pivotSlot targetSlot state =
      some (operations, result)) :
    ∀ op ∈ operations, SourceXorOnly op := by
  cases hr : Witnora.G5IndexedRowValueRefinement.workingRow
      initial state targetSlot with
  | none =>
      simp [emitOne, hr] at h
  | some targetRow =>
      by_cases hv : v ∈ targetRow.coefficients
      · cases hs : state.step initial (.addRowXor targetSlot pivotSlot) with
        | none =>
            simp [emitOne, hr, hv, hs] at h
        | some updated =>
            simp [emitOne, hr, hv, hs] at h
            rcases h with ⟨hops, hresult⟩
            subst operations
            intro op hm
            simp at hm
            subst op
            exact ⟨targetSlot, pivotSlot, rfl⟩
      · simp [emitOne, hr, hv] at h
        rcases h with ⟨hops, hresult⟩
        subst operations
        simp

theorem emitPass_only_xors
    (initial : List Row) (v pivotSlot : Nat)
    (targets : List Nat) (state result : SourceState initial)
    (operations : List Op)
    (h : emitPass initial v pivotSlot targets state =
      some (operations, result)) :
    ∀ op ∈ operations, SourceXorOnly op := by
  induction targets generalizing state result operations with
  | nil =>
      simp [emitPass] at h
      rcases h with ⟨hops, hresult⟩
      subst operations
      simp
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
                      rcases h with ⟨hops, hresult⟩
                      subst operations
                      intro op hm
                      rcases List.mem_append.mp hm with ha | hb
                      · exact emitOne_only_xors initial v pivotSlot
                          target state updated firstOps hf op ha
                      · exact ih updated finished restOps hr op hb

/-- Every successful full variable-schedule emission is XOR-only. -/
theorem emitSchedule_only_xors
    (initial : List Row)
    (variables candidates : List Nat)
    (state result : SourceState initial)
    (operations : List Op)
    (h : emitSchedule initial variables candidates state =
      some (operations, result)) :
    ∀ op ∈ operations, SourceXorOnly op := by
  induction variables generalizing candidates state result operations with
  | nil =>
      simp [emitSchedule] at h
      rcases h with ⟨hops, hresult⟩
      subst operations
      simp
  | cons v rest ih =>
      cases hp : choosePivot initial v state candidates with
      | none =>
          have hrest : emitSchedule initial rest candidates state =
              some (operations, result) := by
            simpa [emitSchedule, hp] using h
          exact ih candidates state result operations hrest
      | some choice =>
          cases choice with
          | mk pivotSlot pivotRow =>
              let targets := candidates.filter (fun slot => slot != pivotSlot)
              cases he : emitPass initial v pivotSlot targets state with
              | none =>
                  simp [emitSchedule, hp, targets, he] at h
              | some first =>
                  cases first with
                  | mk firstOps updated =>
                      cases hr : emitSchedule initial rest targets updated with
                      | none =>
                          simp [emitSchedule, hp, targets, he, hr] at h
                      | some second =>
                          cases second with
                          | mk restOps finished =>
                              simp [emitSchedule, hp, targets, he, hr] at h
                              rcases h with ⟨hops, hresult⟩
                              subst operations
                              intro op hm
                              rcases List.mem_append.mp hm with ha | hb
                              · exact emitPass_only_xors initial v
                                  pivotSlot targets state updated firstOps
                                  he op ha
                              · exact ih targets updated finished restOps
                                  hr op hb

/-- Generated source XOR-only operations translate to XOR-only G5Trace
    operations under the already verified source-to-replay mapping. -/
theorem emitted_replay_is_xor_only
    (initial : List Row)
    (variables candidates : List Nat)
    (state result : SourceState initial)
    (operations : List Op)
    (h : emitSchedule initial variables candidates state =
      some (operations, result)) :
    ∀ step ∈ operations.map toReplayStep, XorOnly step := by
  intro step hm
  obtain ⟨op, hop, hstep⟩ := List.mem_map.mp hm
  obtain ⟨target, source, hxor⟩ :=
    emitSchedule_only_xors initial variables candidates
      state result operations h op hop
  subst op
  subst step
  exact ⟨target, source, rfl⟩

/-- Every successful complete indexed variable schedule preserves the
    satisfying assignments of the original row table *exactly*.
    This uses the real initial reference map and an independent replay. -/
theorem emitted_schedule_models_iff
    (bound : Nat) (initial : List Row)
    (variables : List Nat) (result : SourceState initial)
    (operations : List Op)
    (h : emitSchedule initial variables (List.range initial.length)
      (SourceState.start initial) = some (operations, result)) :
    ∃ finalRows,
      replay initial (operations.map toReplayStep) = some finalRows ∧
      TableRel initial result finalRows ∧
      (∀ a : Nat → Bool,
        SlotsHold bound initial a ↔ SlotsHold bound finalRows a) := by
  obtain ⟨finalRows, hreplay, hrel⟩ :=
    emitted_from_initial_replays initial variables result operations h
  refine ⟨finalRows, hreplay, hrel, ?_⟩
  intro a
  exact replay_xor_models_iff bound initial finalRows
    (operations.map toReplayStep) a
    (emitted_replay_is_xor_only initial variables
      (List.range initial.length) (SourceState.start initial)
      result operations h) hreplay

#print axioms Witnora.G5ScheduledModelPreservation.emitSchedule_only_xors
#print axioms Witnora.G5ScheduledModelPreservation.emitted_schedule_models_iff

end Witnora.G5ScheduledModelPreservation
