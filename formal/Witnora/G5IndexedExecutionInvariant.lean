import Witnora.G5IndexedLengthRefinement

/-!
# G5 compiler execution invariant: reference-table arity

The source indexed compiler may swap its live row references or replace one
target with a new DAG reference, but its mutable reference table must never
change length. This is proved for every accepted operation and lifted to
arbitrary finite operation sequences. This supplies the persistent arity
invariant required by the per-step DAG refinement theorem.
-/

namespace Witnora.G5IndexedExecutionInvariant

open Witnora.G5IndexedBridge

/-- Every accepted mutable indexed operation preserves the number of
    active row references, including source swaps and target XOR updates. -/
theorem step_preserves_ref_length
    (state next : State) (op : Operation)
    (h : step state op = some next) :
    next.1.length = state.1.length := by
  cases op with
  | swapRows i j =>
      cases hi : state.1[i]? with
      | none =>
          simp [step, hi] at h
      | some left =>
          cases hj : state.1[j]? with
          | none =>
              simp [step, hi, hj] at h
          | some right =>
              simp [step, hi, hj] at h
              cases h
              simp
  | addRowXor target source =>
      by_cases heq : target = source
      · subst source
        simp [step] at h
      · have hneq : (target == source) = false :=
          decide_eq_false heq
        cases hi : state.1[target]? with
        | none =>
            simp [step, hneq, hi] at h
        | some left =>
            cases hj : state.1[source]? with
            | none =>
                simp [step, hneq, hi, hj] at h
            | some right =>
                simp [step, hneq, hi, hj] at h
                cases h
                simp

/-- Every finite successful interpreter run preserves its initial active
    row count, independent of how many XOR rows were appended to the DAG. -/
theorem foldlM_preserves_ref_length
    (operations : List Operation) (state next : State)
    (h : operations.foldlM step state = some next) :
    next.1.length = state.1.length := by
  induction operations generalizing state with
  | nil =>
      simp at h
      cases h
      rfl
  | cons op rest ih =>
      cases hs : step state op with
      | none =>
          simp [List.foldlM_cons, hs] at h
      | some updated =>
          have hrest : rest.foldlM step updated = some next := by
            simpa [List.foldlM_cons, hs] using h
          exact (ih updated hrest).trans
            (step_preserves_ref_length state updated op hs)

/-- This invariant holds for the actual compile input's initial range
    and every accepted source sequence. -/
theorem indexed_run_preserves_input_row_count
    (inputRows : Nat) (operations : List Operation) (result : State)
    (h : operations.foldlM step (List.range inputRows, []) =
      some result) :
    result.1.length = inputRows := by
  have hh := foldlM_preserves_ref_length operations
    (List.range inputRows, []) result h
  simpa using hh

#print axioms Witnora.G5IndexedExecutionInvariant.step_preserves_ref_length
#print axioms Witnora.G5IndexedExecutionInvariant.foldlM_preserves_ref_length
#print axioms Witnora.G5IndexedExecutionInvariant.indexed_run_preserves_input_row_count

end Witnora.G5IndexedExecutionInvariant
