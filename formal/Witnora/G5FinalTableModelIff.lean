import Witnora.G5CandidateSlotPartition
import Witnora.G5LedgerSurvivorModel

/-!
# Exact G5 pivot-ledger and final candidate row model correspondence

Every retired pivot row occurs unchanged in a final candidate slot,
and every starting candidate slot is either retired or survives.
Therefore an assignment satisfies all final candidate working rows
iff it satisfies the recorded retired pivots and final surviving rows.

This is a universal model-set equivalence, independent of row order
and without enumerating Boolean assignments.
-/

namespace Witnora.G5FinalTableModelIff

open Witnora.G5Trace
open Witnora.G5Certificate
open Witnora.G5IndexedOperationEmitter
open Witnora.G5IndexedRowValueRefinement
open Witnora.G5RetiredPivotLedger
open Witnora.G5LedgerSurvivorModel
open Witnora.G5LedgerFinalRowEmbedding
open Witnora.G5CandidateSlotPartition
open Witnora.G5TrackedSurvivors
open Witnora.G5SourceTraceSafety

/-- Every original candidate working slot satisfies its actual final
    row equation, whenever that slot resolves to a live row. -/
def FinalCandidatesHold (initial : List Row) (bound : Nat)
    (candidates : List Nat) (outcome : PivotOutcome initial)
    (assignment : Nat → Bool) : Prop :=
  ∀ slot ∈ candidates, ∀ row,
    workingRow initial outcome.finalState slot = some row →
      RowHolds bound row assignment

/-- Exact model equivalence between the retained pivot ledger plus
    residual survivors and the entire final candidate working table. -/
theorem combined_model_iff_final_candidates
    (initial : List Row) (bound : Nat)
    (variables candidates : List Nat)
    (state : SourceState initial) (outcome : PivotOutcome initial)
    (assignment : Nat → Bool)
    (hvalid : LiveRefsValid initial state)
    (h : emitScheduleWithPivots initial variables candidates state =
      some outcome) :
    CombinedModel initial bound outcome assignment ↔
      FinalCandidatesHold initial bound candidates outcome assignment := by
  have hledger := ledger_entries_are_final_working_rows initial
    variables candidates state outcome hvalid h
  have hpartition := every_candidate_is_retired_or_survives initial
    variables candidates state outcome hvalid h
  have htracked := pivot_ledger_refines_tracked initial
    variables candidates state outcome h
  have hsurvivorsSubset := tracked_survivors_subset initial
    variables candidates state outcome.finalState
    outcome.operations outcome.survivors htracked
  constructor
  · intro hcombined
    rcases hcombined with ⟨hpivots, hsurvivors⟩
    intro slot hm row hrow
    rcases hpartition slot hm with hretired | hsurvives
    · obtain ⟨entry, hentry, hrecorded⟩ := hretired
      have hsame : row = entry.2 :=
        Option.some.inj (hrow.symm.trans hrecorded)
      subst row
      exact hpivots entry hentry
    · exact hsurvivors slot hsurvives row hrow
  · intro hfinal
    constructor
    · intro entry hm
      obtain ⟨slot, hslot, hrow⟩ := hledger entry hm
      exact hfinal slot hslot entry.2 hrow
    · intro slot hs row hrow
      exact hfinal slot (hsurvivorsSubset slot hs) row hrow

#print axioms Witnora.G5FinalTableModelIff.combined_model_iff_final_candidates

end Witnora.G5FinalTableModelIff
