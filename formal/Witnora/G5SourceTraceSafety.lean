import Witnora.G5IndexedViewSimulation
import Witnora.G5IndexedReferenceSafety

/-!
# Source interpreter finite-trace live-reference invariant

The proof-carrying DAG's live working references all resolve to an existing
DAG row. Prove this directly for each accepted SourceState.step and lift it
through SourceState.run over arbitrary finite operation lists. This discharges
the range premise of xor_all_slots for every reachable source state.
-/

namespace Witnora.G5SourceTraceSafety

open Witnora.G5Trace
open Witnora.G5Dag
open Witnora.G5IndexedOperationEmitter
open Witnora.G5IndexedViewSimulation

def LiveRefsValid (initial : List Row) (state : SourceState initial) : Prop :=
  ∀ ref ∈ state.refs, ref < state.dag.rows.length

theorem start_valid (initial : List Row) :
    LiveRefsValid initial (SourceState.start initial) := by
  intro ref href
  simpa [SourceState.start, Witnora.G5VerifiedDagEmitter.Builder.start]
    using List.mem_range.mp href

theorem valid_lookup
    (initial : List Row) (state : SourceState initial)
    (hvalid : LiveRefsValid initial state)
    (slot ref : Nat) (h : state.refs[slot]? = some ref) :
    ref < state.dag.rows.length :=
  hvalid ref (getElem?_mem state.refs slot ref h)

theorem step_preserves_valid
    (initial : List Row) (state next : SourceState initial)
    (op : Witnora.G5IndexedBridge.Operation)
    (hvalid : LiveRefsValid initial state)
    (hstep : state.step initial op = some next) :
    LiveRefsValid initial next := by
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
              have hl := valid_lookup initial state hvalid i left hi
              have hr := valid_lookup initial state hvalid j right hj
              exact Witnora.G5IndexedReferenceSafety.property_set
                _ _ j left
                (Witnora.G5IndexedReferenceSafety.property_set
                  _ _ i right hvalid hr) hl
  | addRowXor target source =>
      by_cases heq : target = source
      · subst source
        simp [SourceState.step] at hstep
      · have hneq : (target == source) = false := decide_eq_false heq
        cases hi : state.refs[target]? with
        | none =>
            simp [SourceState.step, hneq, hi] at hstep
        | some targetRef =>
            cases hj : state.refs[source]? with
            | none =>
                simp [SourceState.step, hneq, hi, hj] at hstep
            | some sourceRef =>
                cases ht : state.dag.rows[targetRef]? with
                | none =>
                    simp [SourceState.step, hneq, hi, hj, ht] at hstep
                | some targetRow =>
                    cases hs : state.dag.rows[sourceRef]? with
                    | none =>
                        simp [SourceState.step, hneq, hi, hj, ht, hs] at hstep
                    | some sourceRow =>
                        simp [SourceState.step, hneq, hi, hj, ht, hs] at hstep
                        cases hstep
                        have hnew : state.dag.rows.length <
                            (state.dag.append initial targetRef sourceRef
                              targetRow sourceRow ht hs).rows.length := by
                          simp [Witnora.G5VerifiedDagEmitter.Builder.append]
                        have hprev : ∀ ref ∈ state.refs,
                            ref < (state.dag.append initial targetRef sourceRef
                              targetRow sourceRow ht hs).rows.length := by
                          intro ref hm
                          exact Nat.lt_of_lt_of_le (hvalid ref hm)
                            (by simp [Witnora.G5VerifiedDagEmitter.Builder.append])
                        exact Witnora.G5IndexedReferenceSafety.property_set
                          _ _ target state.dag.rows.length hprev hnew

theorem foldlM_preserves_valid
    (initial : List Row)
    (operations : List Witnora.G5IndexedBridge.Operation)
    (state next : SourceState initial)
    (hvalid : LiveRefsValid initial state)
    (h : operations.foldlM (fun s op => s.step initial op) state =
      some next) :
    LiveRefsValid initial next := by
  induction operations generalizing state with
  | nil =>
      simp at h
      cases h
      exact hvalid
  | cons op rest ih =>
      cases hs : state.step initial op with
      | none =>
          simp [List.foldlM_cons, hs] at h
      | some updated =>
          have hrest : rest.foldlM (fun s op => s.step initial op)
              updated = some next := by
            simpa [List.foldlM_cons, hs] using h
          exact ih updated
            (step_preserves_valid initial state updated op hvalid hs) hrest

theorem run_refs_valid
    (initial : List Row)
    (operations : List Witnora.G5IndexedBridge.Operation)
    (result : SourceState initial)
    (hrun : run initial operations = some result) :
    LiveRefsValid initial result := by
  exact foldlM_preserves_valid initial operations
    (SourceState.start initial) result (start_valid initial) hrun

/-- The all-slot XOR simulation premise is automatic on every reachable
    source state, whatever finite legal trace produced it. -/
theorem run_live_slots_bounded
    (initial : List Row)
    (operations : List Witnora.G5IndexedBridge.Operation)
    (result : SourceState initial)
    (hrun : run initial operations = some result)
    (slot ref : Nat)
    (hlookup : result.refs[slot]? = some ref) :
    ref < result.dag.rows.length :=
  valid_lookup initial result
    (run_refs_valid initial operations result hrun) slot ref hlookup

#print axioms Witnora.G5SourceTraceSafety.step_preserves_valid
#print axioms Witnora.G5SourceTraceSafety.run_refs_valid
#print axioms Witnora.G5SourceTraceSafety.run_live_slots_bounded

end Witnora.G5SourceTraceSafety
