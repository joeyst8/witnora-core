import Witnora.G5FinalTableModelIff
import Witnora.G5ScheduledModelPreservation
import Witnora.G5InitialSupportCoverage

/-!
# Executable indexed G5 contradiction-discovery completeness

The certified ledger-plus-survivor equation system has a model exactly
when the surviving rows contain no contradiction. Its models equal the
entire final candidate working table; the XOR-only schedule preserves
all input row models. For a successful schedule started at the identity
row table, original UNSAT therefore forces a true-RHS final survivor.

This theorem concerns the original sparse row system with complete
variable coverage, valid bounded indices, and successful emitted
execution. CNF extraction, Python refinement, and G14 remain separate
TC-063 obligations.
-/

namespace Witnora.G5ExecutableContradictionComplete

open Witnora.G5Trace
open Witnora.G5Certificate
open Witnora.G5IndexedOperationEmitter
open Witnora.G5IndexedRowValueRefinement
open Witnora.G5IndexedScheduledEmitter
open Witnora.G5TrackedSurvivors
open Witnora.G5RetiredPivotLedger
open Witnora.G5LedgerSurvivorModel
open Witnora.G5FinalTableModelIff
open Witnora.G5InitialSupportCoverage
open Witnora.G5GlobalRowModelInvariant
open Witnora.G5ScheduledModelPreservation
open Witnora.G5RowTableRelation
open Witnora.G5SourceTraceSafety

private theorem lookup_index_lt {α : Type}
    (rows : List α) (slot : Nat) (row : α)
    (h : rows[slot]? = some row) : slot < rows.length := by
  induction rows generalizing slot with
  | nil =>
      cases slot <;> simp at h
  | cons head tail ih =>
      cases slot with
      | zero => simp
      | succ n =>
          have ht : tail[n]? = some row := by
            simpa using h
          exact Nat.succ_lt_succ (ih n ht)

/-- Legal XOR replacement never changes the number of working rows. -/
private theorem xor_step_keeps_length
    (rows result : List Row) (target source : Nat)
    (h : applyStep rows (.addXor target source) = some result) :
    result.length = rows.length := by
  by_cases hne : target ≠ source
  · cases ht : rows[target]? with
    | none =>
        simp [applyStep, hne, ht] at h
    | some targetRow =>
        cases hs : rows[source]? with
        | none =>
            simp [applyStep, hne, ht, hs] at h
        | some sourceRow =>
            have hexact := applyStep_addXor_exact rows target source
              targetRow sourceRow hne ht hs
            have heq : result = rows.set target
                (xorRow targetRow sourceRow) :=
              Option.some.inj (h.symm.trans hexact)
            subst result
            simp
  · have heq : target = source := Decidable.not_not.mp hne
    subst source
    simp [applyStep] at h

/-- Any finite successful XOR-only replay retains its original
    row-table length exactly, including across arbitrary XOR updates. -/
theorem xor_only_replay_keeps_length
    (rows result : List Row) (steps : List Step)
    (honly : ∀ step ∈ steps, XorOnly step)
    (h : replay rows steps = some result) :
    result.length = rows.length := by
  induction steps generalizing rows with
  | nil =>
      simp [replay] at h
      subst result
      rfl
  | cons step rest ih =>
      obtain ⟨target, source, hstep⟩ :=
        honly step (by simp)
      subst step
      cases hs : applyStep rows (.addXor target source) with
      | none =>
          simp [replay, hs] at h
      | some updated =>
          have hrest : replay updated rest = some result := by
            simpa [replay, hs] using h
          have hrestOnly : ∀ step ∈ rest, XorOnly step := by
            intro step hm
            exact honly step (by simp [hm])
          exact (ih updated hrestOnly hrest).trans
            (xor_step_keeps_length rows updated target source hs)

/-- An exact working-row relation plus equal table lengths identifies
    satisfaction of the final row list with satisfaction of all
    original-range source working slots. -/
theorem slots_hold_iff_original_candidates
    (initial rows : List Row) (bound : Nat)
    (outcome : PivotOutcome initial) (assignment : Nat → Bool)
    (hrel : TableRel initial outcome.finalState rows)
    (hlen : rows.length = initial.length) :
    SlotsHold bound rows assignment ↔
      FinalCandidatesHold initial bound
        (List.range initial.length) outcome assignment := by
  constructor
  · intro hall
    intro slot _ row hrow
    have hlookup : rows[slot]? = some row :=
      (hrel slot).symm.trans hrow
    exact hall slot row hlookup
  · intro hfinal
    intro slot row hlookup
    have hlt : slot < rows.length :=
      lookup_index_lt rows slot row hlookup
    have hm : slot ∈ List.range initial.length := by
      apply List.mem_range.mpr
      simpa [hlen] using hlt
    have hrow : workingRow initial outcome.finalState slot =
        some row := (hrel slot).trans hlookup
    exact hfinal slot hm row hrow

/-- Full original sparse-row completeness for a successful executable
    G5 schedule: if no assignment satisfies the original input rows,
    the final surviving candidate set contains an explicit zero-support
    true-RHS contradiction row. -/
theorem initial_unsat_forces_executable_survivor_contradiction
    (initial : List Row) (bound : Nat)
    (variables : List Nat)
    (outcome : PivotOutcome initial)
    (hcoverage : Covered variables initial)
    (hvars : ∀ v ∈ variables, v < bound)
    (h : emitScheduleWithPivots initial variables
      (List.range initial.length) (SourceState.start initial) =
      some outcome)
    (hunsat : ¬ ∃ assignment : Nat → Bool,
      ∀ row ∈ initial, RowHolds bound row assignment) :
    ∃ slot ∈ outcome.survivors, ∃ row,
      workingRow initial outcome.finalState slot = some row ∧
      row.coefficients = [] ∧ row.rhs = true := by
  have hvalid := start_valid initial
  have hnd : (List.range initial.length).Nodup :=
    List.nodup_range
  have htracked := pivot_ledger_refines_tracked initial variables
    (List.range initial.length) (SourceState.start initial) outcome h
  have hsched := tracked_execution_matches_schedule initial variables
    (List.range initial.length) (SourceState.start initial)
    outcome.finalState outcome.operations outcome.survivors htracked
  obtain ⟨rows, hreplay, hrel, hmodels⟩ :=
    emitted_schedule_models_iff bound initial variables
      outcome.finalState outcome.operations hsched
  have hlength : rows.length = initial.length :=
    xor_only_replay_keeps_length initial rows
      (outcome.operations.map
        Witnora.G5FiniteTraceCorrespondence.toReplayStep)
      (emitted_replay_is_xor_only initial variables
        (List.range initial.length) (SourceState.start initial)
        outcome.finalState outcome.operations hsched) hreplay
  have hcandidate := slots_hold_iff_original_candidates initial
    rows bound outcome (fun _ => false) hrel hlength
  have hcombinedUnsat : ¬ ∃ assignment : Nat → Bool,
      CombinedModel initial bound outcome assignment := by
    rintro ⟨assignment, hcombined⟩
    have hfinal := (combined_model_iff_final_candidates initial
      bound variables (List.range initial.length)
      (SourceState.start initial) outcome assignment
      hvalid h).mp hcombined
    have hfinalRows := (slots_hold_iff_original_candidates initial
      rows bound outcome assignment hrel hlength).mpr hfinal
    have hinitial := (hmodels assignment).mpr hfinalRows
    have hall := (slotsHold_iff_all bound initial assignment).mp hinitial
    exact hunsat ⟨assignment, hall⟩
  obtain ⟨slot, hslot, row, hrow, hrhs⟩ :=
    combined_unsat_forces_survivor_contradiction initial bound
      variables (List.range initial.length)
      (SourceState.start initial) outcome hcoverage hnd hvalid
      hvars h hcombinedUnsat
  have hzero := final_survivor_support_empty_from_initial initial
    variables (List.range initial.length)
    (SourceState.start initial) outcome.finalState
    outcome.operations outcome.survivors hcoverage hnd hvalid
    htracked slot hslot row hrow
  exact ⟨slot, hslot, row, hrow, hzero, hrhs⟩

#print axioms Witnora.G5ExecutableContradictionComplete.xor_only_replay_keeps_length
#print axioms Witnora.G5ExecutableContradictionComplete.slots_hold_iff_original_candidates
#print axioms Witnora.G5ExecutableContradictionComplete.initial_unsat_forces_executable_survivor_contradiction

end Witnora.G5ExecutableContradictionComplete
