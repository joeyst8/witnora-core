import Witnora.G5SourceStepSemantics

/-!
# Finite G5 source trace / independent row replay correspondence

A successful source interpreter run with distinct-row swaps has exactly
the same working-row observable values as G5Trace.replay, provided its
initial state is related to the independent row table and its references
are live. The proof composes the kernel-checked one-step refinements
over arbitrary finite operation sequences.
-/

namespace Witnora.G5FiniteTraceCorrespondence

open Witnora.G5Trace
open Witnora.G5IndexedOperationEmitter
open Witnora.G5IndexedRowValueRefinement
open Witnora.G5IndexedViewSimulation
open Witnora.G5RowTableRelation
open Witnora.G5SourceStepSemantics
open Witnora.G5SourceTraceSafety

def toReplayStep : Witnora.G5IndexedBridge.Operation → Step
  | .swapRows i j => .swap i j
  | .addRowXor i j => .addXor i j

def NoSelfSwap : Witnora.G5IndexedBridge.Operation → Prop
  | .swapRows i j => i ≠ j
  | .addRowXor _ _ => True

theorem lookup_some_of_lt {α : Type} (xs : List α) (i : Nat)
    (hi : i < xs.length) : ∃ x, xs[i]? = some x := by
  induction xs generalizing i with
  | nil => simp at hi
  | cons x tail ih =>
      cases i with
      | zero => exact ⟨x, rfl⟩
      | succ j =>
          have hj : j < tail.length := by simpa using hi
          obtain ⟨y, hy⟩ := ih j hj
          exact ⟨y, by simpa using hy⟩

/-- For every successful legal source operation, there is a matching
    independent G5 replay step, preserving the row table relation. -/
theorem step_simulates
    (initial : List Row) (state next : SourceState initial)
    (rows : List Row) (op : Witnora.G5IndexedBridge.Operation)
    (hvalid : LiveRefsValid initial state)
    (hrel : TableRel initial state rows)
    (hlegal : NoSelfSwap op)
    (hstep : state.step initial op = some next) :
    ∃ nextRows,
      applyStep rows (toReplayStep op) = some nextRows ∧
      TableRel initial next nextRows := by
  cases op with
  | swapRows i j =>
      have hne : i ≠ j := hlegal
      cases hi : state.refs[i]? with
      | none =>
          simp [SourceState.step, hi] at hstep
      | some leftRef =>
          cases hj : state.refs[j]? with
          | none =>
              simp [SourceState.step, hi, hj] at hstep
          | some rightRef =>
              have hlref := valid_lookup initial state hvalid i leftRef hi
              have hrref := valid_lookup initial state hvalid j rightRef hj
              obtain ⟨leftRow, hleft⟩ :=
                lookup_some_of_lt state.dag.rows leftRef hlref
              obtain ⟨rightRow, hright⟩ :=
                lookup_some_of_lt state.dag.rows rightRef hrref
              have hl : rows[i]? = some leftRow := by
                simpa [TableRel, workingRow, hi, hleft]
                  using (hrel i).symm
              have hr : rows[j]? = some rightRow := by
                simpa [TableRel, workingRow, hj, hright]
                  using (hrel j).symm
              have hexact := swap_step_exact initial state
                i j leftRef rightRef hi hj
              have heq : next =
                  swapUpdatedState initial state i j leftRef rightRef :=
                Option.some.inj (hstep.symm.trans hexact)
              subst next
              refine ⟨(rows.set i rightRow).set j leftRow, ?_, ?_⟩
              · exact applyStep_swap_exact rows i j leftRow rightRow hl hr
              · exact swap_preserves_table_relation initial state rows
                  i j leftRef rightRef leftRow rightRow
                  hrel hne hi hj hl hr
  | addRowXor target source =>
      by_cases hne : target ≠ source
      · cases hi : state.refs[target]? with
        | none =>
            simp [SourceState.step, decide_eq_false hne, hi] at hstep
        | some targetRef =>
            cases hj : state.refs[source]? with
            | none =>
                simp [SourceState.step, decide_eq_false hne, hi, hj] at hstep
            | some sourceRef =>
                have htref := valid_lookup initial state hvalid
                  target targetRef hi
                have hsref := valid_lookup initial state hvalid
                  source sourceRef hj
                obtain ⟨targetRow, ht⟩ :=
                  lookup_some_of_lt state.dag.rows targetRef htref
                obtain ⟨sourceRow, hs⟩ :=
                  lookup_some_of_lt state.dag.rows sourceRef hsref
                have hexact := xor_step_exact initial state
                  target source targetRef sourceRef targetRow sourceRow
                  hne hi hj ht hs
                have heq : next =
                    xorUpdatedState initial state target targetRef sourceRef
                      targetRow sourceRow ht hs :=
                  Option.some.inj (hstep.symm.trans hexact)
                subst next
                have hrowTarget : rows[target]? = some targetRow := by
                  simpa [TableRel, workingRow, hi, ht]
                    using (hrel target).symm
                have hrowSource : rows[source]? = some sourceRow := by
                  simpa [TableRel, workingRow, hj, hs]
                    using (hrel source).symm
                refine ⟨rows.set target (xorRow targetRow sourceRow),
                  ?_, ?_⟩
                · exact applyStep_addXor_exact rows target source
                    targetRow sourceRow hne hrowTarget hrowSource
                · exact xor_preserves_table_relation initial state rows
                    target targetRef sourceRef targetRow sourceRow
                    hrel hi ht hs
                    (fun slot ref h => valid_lookup initial state
                      hvalid slot ref h)
      · have heq : target = source := by
          exact Decidable.not_not.mp hne
        subst source
        simp [SourceState.step] at hstep

/-- Arbitrary finite successful source traces have identical row views
    to an independent G5Trace.replay execution. -/
theorem foldlM_simulates
    (initial : List Row)
    (operations : List Witnora.G5IndexedBridge.Operation)
    (state next : SourceState initial)
    (rows : List Row)
    (hvalid : LiveRefsValid initial state)
    (hrel : TableRel initial state rows)
    (hlegal : ∀ op ∈ operations, NoSelfSwap op)
    (hrun : operations.foldlM
      (fun s op => s.step initial op) state = some next) :
    ∃ finalRows,
      replay rows (operations.map toReplayStep) = some finalRows ∧
      TableRel initial next finalRows := by
  induction operations generalizing state rows with
  | nil =>
      simp at hrun
      cases hrun
      exact ⟨rows, rfl, hrel⟩
  | cons op rest ih =>
      cases hs : state.step initial op with
      | none =>
          simp [List.foldlM_cons, hs] at hrun
      | some updated =>
          have hrest : rest.foldlM (fun s op => s.step initial op)
              updated = some next := by
            simpa [List.foldlM_cons, hs] using hrun
          have hop : NoSelfSwap op := hlegal op (by simp)
          obtain ⟨updatedRows, happly, hupdatedRel⟩ :=
            step_simulates initial state updated rows op hvalid hrel hop hs
          have hupdatedValid :=
            step_preserves_valid initial state updated op hvalid hs
          have hrestLegal : ∀ x ∈ rest, NoSelfSwap x := by
            intro x hx
            exact hlegal x (by simp [hx])
          obtain ⟨finalRows, hreplay, hfinalRel⟩ :=
            ih updated updatedRows hupdatedValid hupdatedRel
              hrestLegal hrest
          refine ⟨finalRows, ?_, hfinalRel⟩
          simpa [replay, happly] using hreplay

/-- The real source interpreter starts with the same observable table as
    the independent replay interpreter. -/
theorem start_table_relation (initial : List Row) :
    TableRel initial (SourceState.start initial) initial := by
  intro slot
  simp only [TableRel, workingRow, SourceState.start,
    Witnora.G5VerifiedDagEmitter.Builder.start]
  by_cases h : slot < initial.length
  · simp [List.getElem?_range, h]
  · have hr : (List.range initial.length)[slot]? = none := by
      simp [List.getElem?_range, h]
    have hn : initial[slot]? = none := by
      simp [List.getElem?_eq_none_iff, Nat.le_of_not_gt h]
    simp [hr, hn]

/-- Direct theorem for SourceState.run from initial rows: the independent
    replay succeeds and exposes exactly the same row at every slot. -/
theorem run_simulates
    (initial : List Row)
    (operations : List Witnora.G5IndexedBridge.Operation)
    (result : SourceState initial)
    (hlegal : ∀ op ∈ operations, NoSelfSwap op)
    (hrun : run initial operations = some result) :
    ∃ finalRows,
      replay initial (operations.map toReplayStep) = some finalRows ∧
      TableRel initial result finalRows := by
  exact foldlM_simulates initial operations
    (SourceState.start initial) result initial
    (start_valid initial) (start_table_relation initial)
    hlegal hrun

#print axioms Witnora.G5FiniteTraceCorrespondence.start_table_relation
#print axioms Witnora.G5FiniteTraceCorrespondence.run_simulates

#print axioms Witnora.G5FiniteTraceCorrespondence.step_simulates
#print axioms Witnora.G5FiniteTraceCorrespondence.foldlM_simulates

end Witnora.G5FiniteTraceCorrespondence
