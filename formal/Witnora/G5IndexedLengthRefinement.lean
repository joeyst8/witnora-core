import Witnora.G5IndexedOperationEmitter

/-!
# Indexed G5 representation refinement: exact append length and references

The existing mutable compiler assigns the next DAG reference from
initialRowCount + emittedOperationCount. The proof-carrying emitter
assigns it from its live DAG row-table length. These coincide for
every valid emitted trace, not only for example executions.

Remaining: prove the full mutable row-state correspondence, including
list.set updates and source-to-DAG interpreter equivalence.
-/

namespace Witnora.G5IndexedLengthRefinement

open Witnora.G5Trace
open Witnora.G5Dag
open Witnora.G5VerifiedDagEmitter
open Witnora.G5IndexedOperationEmitter

/-- Every successful DAG XOR operation appends exactly one row. -/
theorem replayDag_length
    (initial : List Row) (steps : List XorRef) (final : List Row)
    (h : replayDag initial steps = some final) :
    final.length = initial.length + steps.length := by
  induction steps generalizing initial with
  | nil =>
      simp [replayDag] at h
      cases h
      simp
  | cons step rest ih =>
      cases step with
      | mk i j =>
          cases hi : initial[i]? with
          | none =>
              simp [replayDag, hi] at h
          | some left =>
              cases hj : initial[j]? with
              | none =>
                  simp [replayDag, hi, hj] at h
              | some right =>
                  have hrest : replayDag
                      (initial ++ [xorRow left right]) rest =
                      some final := by
                    simpa [replayDag, hi, hj] using h
                  have hh := ih (initial ++ [xorRow left right]) hrest
                  simpa [List.length_append, Nat.add_assoc,
                    Nat.add_comm, Nat.add_left_comm] using hh

/-- All proof-carrying builders maintain a universal row-count invariant. -/
theorem Builder.rows_length (initial : List Row)
    (state : Builder initial) :
    state.rows.length = initial.length + state.steps.length :=
  replayDag_length initial state.steps state.rows state.replay_ok

/-- Therefore the next mutable-compiler reference and the next
    proof-carrying emitter reference are exactly the same number. -/
theorem next_reference_agrees
    (initial : List Row) (state : Builder initial) :
    initial.length + state.steps.length = state.rows.length :=
  (Builder.rows_length initial state).symm

/-- The explicit next-reference computation used in the existing
    G5IndexedBridge compiler is universally correct for this emitter. -/
theorem source_state_next_reference
    (initial : List Row)
    (state : SourceState initial) :
    state.dag.rows.length = initial.length + state.dag.steps.length :=
  Builder.rows_length initial state.dag

#print axioms Witnora.G5IndexedLengthRefinement.replayDag_length
#print axioms Witnora.G5IndexedLengthRefinement.next_reference_agrees
#print axioms Witnora.G5IndexedLengthRefinement.source_state_next_reference

/-- A single accepted source operation refines the existing mutable
    G5IndexedBridge compiler, provided the working reference count equals
    the original input row count. This establishes identical reference
    remapping and emitted DAG operation pairs. -/
theorem accepted_step_refines_compiler
    (initial : List Row) (state next : SourceState initial)
    (op : Witnora.G5IndexedBridge.Operation)
    (hlen : state.refs.length = initial.length)
    (hstep : state.step initial op = some next) :
    ∃ compiled : Witnora.G5IndexedBridge.State,
      Witnora.G5IndexedBridge.step
        (state.refs, state.dag.steps) op = some compiled ∧
      compiled = (next.refs, next.dag.steps) := by
  cases op with
  | swapRows i j =>
      cases hi : state.refs[i]? with
      | none =>
          simp [SourceState.step, hi] at hstep
      | some left =>
          cases hj : state.refs[j]? with
          | none =>
              simp [SourceState.step, hi, hj] at hstep
          | some right =>
              simp [SourceState.step, hi, hj] at hstep
              cases hstep
              refine ⟨_, ?_, ?_⟩
              · simp [Witnora.G5IndexedBridge.step, hi, hj]
              · rfl
  | addRowXor target source =>
      by_cases hneq : target = source
      · subst source
        simp [SourceState.step] at hstep
      · have hbeq : (target == source) = false :=
          decide_eq_false hneq
        cases htref : state.refs[target]? with
        | none =>
            simp [SourceState.step, hbeq, htref] at hstep
        | some targetRef =>
            cases hsref : state.refs[source]? with
            | none =>
                simp [SourceState.step, hbeq, htref, hsref] at hstep
            | some sourceRef =>
                cases ht : state.dag.rows[targetRef]? with
                | none =>
                    simp [SourceState.step, hbeq, htref, hsref, ht] at hstep
                | some targetRow =>
                    cases hs : state.dag.rows[sourceRef]? with
                    | none =>
                        simp [SourceState.step, hbeq, htref, hsref, ht, hs] at hstep
                    | some sourceRow =>
                        simp [SourceState.step, hbeq, htref, hsref, ht, hs]
                          at hstep
                        cases hstep
                        refine ⟨_, ?_, ?_⟩
                        · simp [Witnora.G5IndexedBridge.step, hbeq,
                            htref, hsref]
                        · simp [Builder.append,
                            source_state_next_reference initial state,
                            hlen, Nat.add_comm]

#print axioms Witnora.G5IndexedLengthRefinement.accepted_step_refines_compiler

end Witnora.G5IndexedLengthRefinement
