import Witnora.G5SurvivorContradictionShape

/-!
# Initial support coverage for all proof-carrying G5 DAG rows

Sparse XOR creates no new variable indices: every variable in the
output occurs in an input. A successful verified DAG replay therefore
preserves any initial finite-variable coverage throughout all appended
rows. Every indexed source working row dereferences one of those rows.

This discharges the final-row coverage assumption in the executable
survivor contradiction-shape theorem, using only the original inputs.
-/

namespace Witnora.G5InitialSupportCoverage

open Witnora.G5Trace
open Witnora.G5Dag
open Witnora.G5IndexedOperationEmitter
open Witnora.G5IndexedRowValueRefinement
open Witnora.G5SourceTraceSafety
open Witnora.G5TrackedSurvivors
open Witnora.G5SurvivorContradictionShape

/-- A finite variable schedule covers the support of every input row. -/
def Covered (variables : List Nat) (rows : List Row) : Prop :=
  ∀ row ∈ rows, ∀ v ∈ row.coefficients, v ∈ variables

/-- Every XOR variable originates in at least one of its two operands. -/
theorem xorRow_preserves_coverage
    (variables : List Nat) (left right : Row)
    (hl : ∀ v ∈ left.coefficients, v ∈ variables)
    (hr : ∀ v ∈ right.coefficients, v ∈ variables) :
    ∀ v ∈ (xorRow left right).coefficients, v ∈ variables := by
  intro v hm
  have hx := (mem_xorCoefficients
    left.coefficients right.coefficients v).mp hm
  rcases hx with ⟨hleft, _⟩ | ⟨hright, _⟩
  · exact hl v hleft
  · exact hr v hright

/-- A legal DAG replay never introduces any variable index that was
    absent from all original input rows, across any finite XOR trace. -/
theorem replayDag_preserves_coverage
    (variables : List Nat) (rows : List Row)
    (steps : List XorRef) (result : List Row)
    (hcov : Covered variables rows)
    (h : replayDag rows steps = some result) :
    Covered variables result := by
  induction steps generalizing rows with
  | nil =>
      simp [replayDag] at h
      subst result
      exact hcov
  | cons step rest ih =>
      rcases step with ⟨i, j⟩
      cases hi : rows[i]? with
      | none =>
          simp [replayDag, hi] at h
      | some left =>
          cases hj : rows[j]? with
          | none =>
              simp [replayDag, hi, hj] at h
          | some right =>
              have hleft := hcov left (getElem?_mem rows i left hi)
              have hright := hcov right (getElem?_mem rows j right hj)
              have hnew : Covered variables
                  (rows ++ [xorRow left right]) := by
                intro row hm
                rcases List.mem_append.mp hm with hold | hadd
                · exact hcov row hold
                · have heq : row = xorRow left right := by
                    simpa using hadd
                  subst row
                  exact xorRow_preserves_coverage variables left right
                    hleft hright
              have hrest : replayDag
                  (rows ++ [xorRow left right]) rest = some result := by
                simpa [replayDag, hi, hj] using h
              exact ih (rows ++ [xorRow left right]) hnew hrest

/-- Every constructed source state carries replay evidence sufficient
    to preserve the original support coverage in its entire DAG. -/
theorem source_dag_coverage
    (initial : List Row) (variables : List Nat)
    (state : SourceState initial)
    (hinput : Covered variables initial) :
    Covered variables state.dag.rows := by
  exact replayDag_preserves_coverage variables initial
    state.dag.steps state.dag.rows hinput state.dag.replay_ok

/-- Any live working row, not just a final survivor, can mention only
    variables already covered by the original source row table. -/
theorem workingRow_coverage
    (initial : List Row) (variables : List Nat)
    (state : SourceState initial)
    (hinput : Covered variables initial)
    (slot : Nat) (row : Row)
    (hrow : workingRow initial state slot = some row) :
    ∀ v ∈ row.coefficients, v ∈ variables := by
  unfold workingRow at hrow
  cases hr : state.refs[slot]? with
  | none =>
      simp [hr] at hrow
  | some ref =>
      have hdag : state.dag.rows[ref]? = some row := by
        simpa [hr] using hrow
      exact (source_dag_coverage initial variables state hinput)
        row (getElem?_mem state.dag.rows ref row hdag)

/-- The coverage premise for final survivor contradiction detection is
    automatically implied by coverage of the original input rows. -/
theorem final_coverage_from_initial
    (initial : List Row) (variables survivors : List Nat)
    (state : SourceState initial)
    (hinput : Covered variables initial) :
    FinalCoverage initial variables state survivors := by
  intro slot _ row hrow
  exact workingRow_coverage initial variables state
    hinput slot row hrow

/-- Complete finite-variable schedules force *all* final surviving
    source rows to have no variable support, with no final-state
    coverage assumption. -/
theorem final_survivor_support_empty_from_initial
    (initial : List Row)
    (variables candidates : List Nat)
    (state finished : SourceState initial)
    (operations : List Witnora.G5EmittedPivotPass.Op)
    (survivors : List Nat)
    (hinput : Covered variables initial)
    (hnd : candidates.Nodup)
    (hvalid : LiveRefsValid initial state)
    (h : emitScheduleTracked initial variables candidates state =
      some (operations, finished, survivors)) :
    ∀ slot ∈ survivors, ∀ row,
      workingRow initial finished slot = some row →
      row.coefficients = [] := by
  exact final_survivor_support_empty initial variables candidates
    state finished operations survivors hnd hvalid
    (final_coverage_from_initial initial variables survivors
      finished hinput) h

/-- An initial-support-complete G5 run has an individually contradictory
    survivor exactly when that survivor has true RHS. -/
theorem survivor_unsat_iff_true_rhs_from_initial
    (initial : List Row) (bound : Nat)
    (variables candidates : List Nat)
    (state finished : SourceState initial)
    (operations : List Witnora.G5EmittedPivotPass.Op)
    (survivors : List Nat) (slot : Nat) (row : Row)
    (hinput : Covered variables initial)
    (hnd : candidates.Nodup)
    (hvalid : LiveRefsValid initial state)
    (h : emitScheduleTracked initial variables candidates state =
      some (operations, finished, survivors))
    (hs : slot ∈ survivors)
    (hrow : workingRow initial finished slot = some row) :
    (¬ ∃ assignment : Nat → Bool,
      Witnora.G5Certificate.RowHolds bound row assignment) ↔
      row.rhs = true := by
  exact survivor_unsat_iff_true_rhs initial bound variables
    candidates state finished operations survivors slot row
    hnd hvalid
    (final_coverage_from_initial initial variables survivors finished hinput)
    h hs hrow

#print axioms Witnora.G5InitialSupportCoverage.replayDag_preserves_coverage
#print axioms Witnora.G5InitialSupportCoverage.source_dag_coverage
#print axioms Witnora.G5InitialSupportCoverage.workingRow_coverage
#print axioms Witnora.G5InitialSupportCoverage.final_survivor_support_empty_from_initial
#print axioms Witnora.G5InitialSupportCoverage.survivor_unsat_iff_true_rhs_from_initial

end Witnora.G5InitialSupportCoverage
