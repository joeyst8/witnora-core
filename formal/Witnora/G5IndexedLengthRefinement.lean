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

end Witnora.G5IndexedLengthRefinement
