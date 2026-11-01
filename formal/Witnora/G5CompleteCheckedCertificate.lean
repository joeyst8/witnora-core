import Witnora.G5ExecutableContradictionComplete
import Witnora.G5ExecutablePassClearance

/-!
# Completeness of checked DAG certificates emitted by executable G5

The universal sparse-row UNSAT-to-survivor-contradiction theorem yields
a concrete final working row. Every successfully dereferenced working
row belongs to the proof-carrying shared DAG. The unchanged production
DAG checker therefore accepts the emitted source trace.

We also package a generic CNF satisfaction contract: if the extraction
is model-equivalent, original CNF UNSAT implies an accepted G5 indexed
certificate. Proving the concrete canonical CNF extractor satisfies
this contract remains a separate TC-063 obligation.
-/

namespace Witnora.G5CompleteCheckedCertificate

open Witnora.G5Trace
open Witnora.G5Dag
open Witnora.G5Certificate
open Witnora.G5VerifiedDagEmitter
open Witnora.G5IndexedOperationEmitter
open Witnora.G5IndexedRowValueRefinement
open Witnora.G5IndexedScheduledEmitter
open Witnora.G5TrackedSurvivors
open Witnora.G5RetiredPivotLedger
open Witnora.G5ExecutableContradictionComplete
open Witnora.G5ExecutablePassClearance
open Witnora.G5InitialSupportCoverage

/-- On any successful full source-indexed G5 schedule, original sparse
    row UNSAT makes the unmodified production indexed checker accept
    the exact generated operation trace. -/
theorem original_row_unsat_yields_checked_certificate
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
    accepts initial outcome.operations = true := by
  obtain ⟨slot, hslot, row, hrow, hzero, hrhs⟩ :=
    initial_unsat_forces_executable_survivor_contradiction
      initial bound variables outcome hcoverage hvars h hunsat
  obtain ⟨ref, href, hdag⟩ :=
    workingRow_derefs initial outcome.finalState slot row hrow
  have hmember : row ∈ outcome.finalState.dag.rows :=
    getElem?_mem outcome.finalState.dag.rows ref row hdag
  have hchecked : checkDagContradiction initial
      outcome.finalState.dag.steps = true :=
    outcome.finalState.dag.accepted_of_contradiction initial
      ⟨row, hmember, hzero, hrhs⟩
  have htracked := pivot_ledger_refines_tracked initial
    variables (List.range initial.length)
    (SourceState.start initial) outcome h
  have hsched := tracked_execution_matches_schedule initial
    variables (List.range initial.length)
    (SourceState.start initial) outcome.finalState
    outcome.operations outcome.survivors htracked
  have hreplay := emitSchedule_replays initial variables
    (List.range initial.length) (SourceState.start initial)
    outcome.finalState outcome.operations hsched
  have hrun : run initial outcome.operations =
      some outcome.finalState := by
    simpa [run, Witnora.G5EmittedPivotPass.executeFrom] using hreplay
  simpa [accepts, hrun] using hchecked

/-- Conditional CNF-level completeness: if the original CNF predicate
    has exactly the models of the extracted sparse input equations,
    an UNSAT CNF produces an accepted scalable indexed G5 certificate
    under the same successful-execution and coverage hypotheses. -/
theorem cnf_unsat_yields_checked_certificate_of_equivalence
    (initial : List Row) (bound : Nat)
    (variables : List Nat)
    (outcome : PivotOutcome initial)
    (cnfHolds : (Nat → Bool) → Prop)
    (hcoverage : Covered variables initial)
    (hvars : ∀ v ∈ variables, v < bound)
    (h : emitScheduleWithPivots initial variables
      (List.range initial.length) (SourceState.start initial) =
      some outcome)
    (hextract : ∀ assignment : Nat → Bool,
      cnfHolds assignment ↔
        (∀ row ∈ initial, RowHolds bound row assignment))
    (hunsat : ¬ ∃ assignment : Nat → Bool,
      cnfHolds assignment) :
    accepts initial outcome.operations = true := by
  have hrowUnsat : ¬ ∃ assignment : Nat → Bool,
      ∀ row ∈ initial, RowHolds bound row assignment := by
    rintro ⟨assignment, hrows⟩
    exact hunsat ⟨assignment, (hextract assignment).mpr hrows⟩
  exact original_row_unsat_yields_checked_certificate initial
    bound variables outcome hcoverage hvars h hrowUnsat

#print axioms Witnora.G5CompleteCheckedCertificate.original_row_unsat_yields_checked_certificate
#print axioms Witnora.G5CompleteCheckedCertificate.cnf_unsat_yields_checked_certificate_of_equivalence

end Witnora.G5CompleteCheckedCertificate
