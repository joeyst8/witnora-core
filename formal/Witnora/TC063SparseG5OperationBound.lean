import Witnora.TC063SparseCover
import Witnora.G5IndexedScheduledEmitter

/-!
# Quadratic sparse-input operation-count bound for indexed G5 emission

A pivot pass emits at most one ADD_ROW_XOR per target slot.  A complete
schedule emits at most one pass per scheduled variable and never increases
the number of remaining target slots.  Thus, without any bound on the
*numerical values* of variable IDs, a successfully generated source trace
has at most (#schedule variables) × (#initial source rows) operations.

In the TC-063 construction the schedule is supportRows, i.e. the list
of original coefficient occurrences.  Hence the operation count is
at most (#initial rows) × (#input coefficient occurrences), quadratic
in the sparse row representation length.  This does not yet bound
the cost of discovering the trace or of replaying/serializing each row.
-/

namespace Witnora.TC063SparseG5OperationBound

open Witnora.G5Trace
open Witnora.G5IndexedOperationEmitter
open Witnora.G5IndexedRowValueRefinement
open Witnora.G5EmittedPivotPass
open Witnora.G5IndexedPivotSelection
open Witnora.G5IndexedScheduledEmitter
open Witnora.TC063CanonicalBound

/-- Each successful source-target inspection emits either zero or one
    indexed ADD_ROW_XOR operation. -/
theorem emitOne_op_count
    (initial : List Row) (v pivotSlot targetSlot : Nat)
    (state result : SourceState initial) (ops : List Op)
    (h : emitOne initial v pivotSlot targetSlot state =
      some (ops, result)) :
    ops.length ≤ 1 := by
  cases hw : workingRow initial state targetSlot with
  | none =>
      simp [emitOne, hw] at h
  | some targetRow =>
      by_cases hv : v ∈ targetRow.coefficients
      · cases hs : state.step initial (.addRowXor targetSlot pivotSlot) with
        | none => simp [emitOne, hw, hv, hs] at h
        | some updated =>
            simp [emitOne, hw, hv, hs] at h
            rcases h with ⟨hops, hresult⟩
            subst ops
            simp
      · simp [emitOne, hw, hv] at h
        rcases h with ⟨hops, hresult⟩
        subst ops
        simp

/-- Every successful pass emits no more operations than the number of
    target slots it inspects. -/
theorem emitPass_op_count
    (initial : List Row) (v pivotSlot : Nat)
    (targets : List Nat) (state result : SourceState initial)
    (ops : List Op)
    (h : emitPass initial v pivotSlot targets state =
      some (ops, result)) :
    ops.length ≤ targets.length := by
  induction targets generalizing state result ops with
  | nil =>
      simp [emitPass] at h
      rcases h with ⟨hops, hresult⟩
      subst ops
      simp
  | cons target rest ih =>
      cases he : emitOne initial v pivotSlot target state with
      | none => simp [emitPass, he] at h
      | some first =>
          cases first with
          | mk firstOps updated =>
              cases hr : emitPass initial v pivotSlot rest updated with
              | none => simp [emitPass, he, hr] at h
              | some second =>
                  cases second with
                  | mk restOps finished =>
                      simp [emitPass, he, hr] at h
                      rcases h with ⟨hops, hresult⟩
                      subst ops
                      have hfirst : firstOps.length ≤ 1 :=
                        emitOne_op_count initial v pivotSlot target
                          state updated firstOps he
                      have hrest : restOps.length ≤ rest.length :=
                        ih updated finished restOps hr
                      simp only [List.length_append, List.length_cons]
                      omega

/-- Universal bound on the number of emitted source operations.  It
    depends on the number of slots/variables, never on the numeric IDs. -/
theorem emitSchedule_op_count
    (initial : List Row) (variables candidates : List Nat)
    (state result : SourceState initial) (ops : List Op)
    (h : emitSchedule initial variables candidates state =
      some (ops, result)) :
    ops.length ≤ variables.length * candidates.length := by
  induction variables generalizing candidates state result ops with
  | nil =>
      simp [emitSchedule] at h
      rcases h with ⟨hops, hresult⟩
      subst ops
      simp
  | cons v rest ih =>
      cases hp : choosePivot initial v state candidates with
      | none =>
          have hrest : emitSchedule initial rest candidates state =
              some (ops, result) := by
            simpa [emitSchedule, hp] using h
          have hb := ih candidates state result ops hrest
          exact le_trans hb
            (Nat.mul_le_mul_right candidates.length
              (by simp : rest.length ≤ (v :: rest).length))
      | some choice =>
          cases choice with
          | mk pivotSlot pivotRow =>
              let targets := candidates.filter (fun slot => slot != pivotSlot)
              cases he : emitPass initial v pivotSlot targets state with
              | none => simp [emitSchedule, hp, targets, he] at h
              | some first =>
                  cases first with
                  | mk firstOps updated =>
                      cases hr : emitSchedule initial rest targets updated with
                      | none => simp [emitSchedule, hp, targets, he, hr] at h
                      | some second =>
                          cases second with
                          | mk restOps finished =>
                              simp [emitSchedule, hp, targets, he, hr] at h
                              rcases h with ⟨hops, hresult⟩
                              subst ops
                              have hpass : firstOps.length ≤ targets.length :=
                                emitPass_op_count initial v pivotSlot
                                  targets state updated firstOps he
                              have htail : restOps.length ≤
                                  rest.length * targets.length :=
                                ih targets updated finished restOps hr
                              have hfilter : targets.length ≤ candidates.length := by
                                dsimp [targets]
                                exact List.length_filter_le _ _
                              calc
                                (firstOps ++ restOps).length =
                                    firstOps.length + restOps.length := by simp
                                _ ≤ targets.length +
                                    rest.length * targets.length := by omega
                                _ = (rest.length + 1) * targets.length := by
                                  simp [Nat.add_mul, Nat.add_comm]
                                _ ≤ (rest.length + 1) * candidates.length :=
                                  Nat.mul_le_mul_left _ hfilter
                                _ = (v :: rest).length * candidates.length := by
                                  simp

/-- Instantiation with the actual TC-063 input-support schedule: if the
    verified emitter succeeds, operation count is bounded by initial row
    count times the total original coefficient occurrence count. -/
theorem tc063_support_schedule_quadratic_op_count
    (initial : List Row)
    (result : SourceState initial) (ops : List Op)
    (h : emitSchedule initial (supportRows initial)
        (List.range initial.length) (SourceState.start initial) =
        some (ops, result)) :
    ops.length ≤ (supportRows initial).length * initial.length := by
  simpa using emitSchedule_op_count initial
    (supportRows initial) (List.range initial.length)
    (SourceState.start initial) result ops h

#print axioms Witnora.TC063SparseG5OperationBound.emitOne_op_count
#print axioms Witnora.TC063SparseG5OperationBound.emitPass_op_count
#print axioms Witnora.TC063SparseG5OperationBound.emitSchedule_op_count
#print axioms Witnora.TC063SparseG5OperationBound.tc063_support_schedule_quadratic_op_count

end Witnora.TC063SparseG5OperationBound
