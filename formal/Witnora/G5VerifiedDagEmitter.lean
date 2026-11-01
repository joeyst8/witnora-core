import Witnora.G5BackSubstitution
import Witnora.G5Dag

/-!
# G5: proof-carrying append-only indexed DAG emitter

Every emitted XOR pair carries exact input index lookup witnesses. The
emitter accumulates an accepted G5 DAG in lockstep with its row table.
A final contradictory row therefore gives a checker-accepted trace.

This certifies arbitrary *legal append operations*. Connecting the
pivot-selection algorithm's target-row updates to a complete list of
such operations is the next refinement theorem.
-/

namespace Witnora.G5VerifiedDagEmitter

open Witnora.G5Trace
open Witnora.G5Dag

/-- Replay is compositional over concatenated DAG operation lists. -/
theorem replayDag_append (initial : List Row)
    (first second : List XorRef) :
    replayDag initial (first ++ second) =
      (replayDag initial first).bind
        (fun intermediate => replayDag intermediate second) := by
  induction first generalizing initial with
  | nil =>
      rfl
  | cons pair rest ih =>
      cases pair with
      | mk i j =>
          cases hi : initial[i]? with
          | none =>
              simp [replayDag, hi]
          | some left =>
              cases hj : initial[j]? with
              | none =>
                  simp [replayDag, hi, hj]
              | some right =>
                  simp only [List.cons_append]
                  simp [replayDag, hi, hj, ih]

/-- A valid single XOR step appends the computed sparse row. -/
theorem replayDag_one (rows : List Row) (i j : Nat)
    (left right : Row) (hi : rows[i]? = some left)
    (hj : rows[j]? = some right) :
    replayDag rows [(i, j)] =
      some (rows ++ [xorRow left right]) := by
  simp [replayDag, hi, hj]

/-- A checked trace state: the emitted operations replay *exactly* to
    the tracked row list, not just to an equivalent set of equations. -/
structure Builder (initial : List Row) where
  steps : List XorRef
  rows : List Row
  replay_ok : replayDag initial steps = some rows

def Builder.start (initial : List Row) : Builder initial where
  steps := []
  rows := initial
  replay_ok := rfl

/-- Append one legal XOR operation and prove its row index correspondence. -/
def Builder.append (initial : List Row)
    (state : Builder initial) (i j : Nat)
    (left right : Row)
    (hi : state.rows[i]? = some left)
    (hj : state.rows[j]? = some right) :
    Builder initial where
  steps := state.steps ++ [(i, j)]
  rows := state.rows ++ [xorRow left right]
  replay_ok := by
    rw [replayDag_append, state.replay_ok]
    exact replayDag_one state.rows i j left right hi hj

/-- If any accumulated row is the actual contradiction, the unchanged
    production G5 checker accepts the emitted DAG as an UNSAT certificate. -/
theorem Builder.accepted_of_contradiction
    (initial : List Row) (state : Builder initial)
    (hbad : ∃ row ∈ state.rows,
      row.coefficients = [] ∧ row.rhs = true) :
    checkDagContradiction initial state.steps = true := by
  unfold checkDagContradiction
  rw [state.replay_ok]
  apply List.any_eq_true.mpr
  obtain ⟨row, hmem, hcoeff, hrhs⟩ := hbad
  exact ⟨row, hmem, by simp [hcoeff, hrhs]⟩

/-- Zero-operation builder correctly accepts an existing contradictory
    input row, without generating a fabricated row. -/
example :
    checkDagContradiction [⟨[], true⟩]
      (Builder.start [⟨[], true⟩]).steps = true := by decide

#print axioms Witnora.G5VerifiedDagEmitter.replayDag_append
#print axioms Witnora.G5VerifiedDagEmitter.Builder.accepted_of_contradiction

/-- Appending one derived row leaves every previously valid reference
    addressable at exactly the same index. -/
theorem Builder.append_preserves_lookup
    (initial : List Row) (state : Builder initial)
    (i j k : Nat) (left right existing : Row)
    (hi : state.rows[i]? = some left)
    (hj : state.rows[j]? = some right)
    (hk : state.rows[k]? = some existing) :
    (state.append initial i j left right hi hj).rows[k]? =
      some existing := by
  simp [Builder.append]
  exact List.getElem?_append_left hk

/-- The new row is always located at the old row-table length. This is
    the reference that the next G5 indexed operation may use. -/
theorem Builder.append_new_index
    (initial : List Row) (state : Builder initial)
    (i j : Nat) (left right : Row)
    (hi : state.rows[i]? = some left)
    (hj : state.rows[j]? = some right) :
    (state.append initial i j left right hi hj).rows[state.rows.length]? =
      some (xorRow left right) := by
  simp [Builder.append]

#print axioms Witnora.G5VerifiedDagEmitter.Builder.append_preserves_lookup
#print axioms Witnora.G5VerifiedDagEmitter.Builder.append_new_index

end Witnora.G5VerifiedDagEmitter
