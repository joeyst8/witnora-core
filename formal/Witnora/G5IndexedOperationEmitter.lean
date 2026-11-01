import Witnora.G5VerifiedDagEmitter
import Witnora.G5IndexedBridge

/-!
# Proof-carrying indexed operation emitter

This module accepts the actual source operation shapes SWAP_ROWS and
ADD_ROW_XOR, keeps mutable row-to-DAG references, and appends a source
operation's XOR only after the referenced DAG rows have been checked.

Every successful run carries the exact G5 replay proof. The remaining
refinement obligation is a universal correspondence between the working
row-table semantics and the verified Gaussian elimination driver.
-/

namespace Witnora.G5IndexedOperationEmitter

open Witnora.G5Trace
open Witnora.G5Dag
open Witnora.G5VerifiedDagEmitter
open Witnora.G5IndexedBridge

/-- Indexed mutable references, plus a proof-carrying append-only G5 DAG. -/
structure SourceState (initial : List Row) where
  dag : Builder initial
  refs : List Nat

def SourceState.start (initial : List Row) : SourceState initial where
  dag := Builder.start initial
  refs := List.range initial.length

/-- Every operation fails closed on an out-of-range reference. -/
def SourceState.step (initial : List Row)
    (state : SourceState initial) : Operation → Option (SourceState initial)
  | .swapRows i j =>
      match state.refs[i]?, state.refs[j]? with
      | some left, some right =>
          some { state with refs :=
            (state.refs.set i right).set j left }
      | _, _ => none
  | .addRowXor target source =>
      if target == source then none
      else
        match state.refs[target]?, state.refs[source]? with
        | some targetRef, some sourceRef =>
            match ht : state.dag.rows[targetRef]?,
                  hs : state.dag.rows[sourceRef]? with
            | some targetRow, some sourceRow =>
                let next := state.dag.append initial
                  targetRef sourceRef targetRow sourceRow ht hs
                some { dag := next,
                  refs := state.refs.set target state.dag.rows.length }
            | _, _ => none
        | _, _ => none

/-- Terminating interpreter for mutable source row operations with a
    trusted DAG witness built at every accepted XOR update. -/
def run (initial : List Row) (operations : List Operation) :
    Option (SourceState initial) :=
  operations.foldlM (fun state op => state.step initial op)
    (SourceState.start initial)

/-- A successful interpreter result has exactly replayable G5 DAG rows. -/
theorem run_replay_exact (initial : List Row) (operations : List Operation)
    (result : SourceState initial)
    (_h : run initial operations = some result) :
    replayDag initial result.dag.steps = some result.dag.rows :=
  result.dag.replay_ok

/-- The same checker as production is used for emitted operations. -/
def accepts (initial : List Row) (operations : List Operation) : Bool :=
  match run initial operations with
  | none => false
  | some state => checkDagContradiction initial state.dag.steps

theorem accepts_has_checked_dag (initial : List Row)
    (operations : List Operation)
    (h : accepts initial operations = true) :
    ∃ result : SourceState initial,
      run initial operations = some result ∧
      checkDagContradiction initial result.dag.steps = true := by
  unfold accepts at h
  cases hr : run initial operations with
  | none =>
      simp [hr] at h
  | some result =>
      refine ⟨result, hr, ?_⟩
      simpa [hr] using h

/-- Two conflicting input rows are emitted as a verified indexed XOR. -/
example :
    accepts [⟨[1], true⟩, ⟨[1], false⟩]
      [.addRowXor 0 1] = true := by decide

/-- Invalid references fail closed. -/
example :
    accepts [⟨[1], true⟩]
      [.addRowXor 0 3] = false := by decide

/-- Self-XOR is not a legal indexed source operation. -/
example :
    accepts [⟨[1], true⟩]
      [.addRowXor 0 0] = false := by decide

#print axioms Witnora.G5IndexedOperationEmitter.run_replay_exact
#print axioms Witnora.G5IndexedOperationEmitter.accepts_has_checked_dag

end Witnora.G5IndexedOperationEmitter
