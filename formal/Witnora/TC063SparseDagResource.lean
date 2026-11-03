import Witnora.TC063SparseG5OperationBound
import Witnora.G5IndexedExecutionInvariant

/-!
# Indexed G5 DAG resource and sparse support closure

The actual append-only certificate replay adds exactly one derived row for
each accepted indexed XOR reference, regardless of numeric variable IDs.
Every derived row uses only variables appearing in its initial source rows.
The simple one-step sparse XOR length upper bound is also proved.

These are independent resource invariants for the sound, source-bound
checker.  A uniform bound on *each individual derived row's length*
requires the additional duplicate-free support-cardinality invariant.
-/

namespace Witnora.TC063SparseDagResource

open Witnora.G5Trace
open Witnora.G5Dag

/-- Sparse symmetric difference cannot introduce a variable that was
    absent from both source lists. -/
theorem xorCoefficients_no_fresh_variable
    (left right : List Nat) (v : Nat)
    (h : v ∈ xorCoefficients left right) :
    v ∈ left ∨ v ∈ right := by
  rcases (mem_xorCoefficients left right v).mp h with
    ⟨hl, _⟩ | ⟨hr, _⟩
  · exact Or.inl hl
  · exact Or.inr hr

/-- Each XOR row is no longer than the combined lengths of its
    two source rows; it introduces no expanded variable names. -/
theorem xorCoefficients_length_le_sum
    (left right : List Nat) :
    (xorCoefficients left right).length ≤
      left.length + right.length := by
  unfold xorCoefficients
  have hl :
      (left.filter (fun x => decide (x ∉ right))).length ≤
        left.length := List.length_filter_le _ _
  have hr :
      (right.filter (fun x => decide (x ∉ left))).length ≤
        right.length := List.length_filter_le _ _
  simp only [List.length_append]
  omega

/-- The replayed DAG adds exactly one row per source-indexed XOR step.
    No rescan of [0, maxVariable) is involved. -/
theorem replayDag_length_exact
    (inputs : List Row) (steps : List XorRef) (result : List Row)
    (h : replayDag inputs steps = some result) :
    result.length = inputs.length + steps.length := by
  induction steps generalizing inputs with
  | nil =>
      simp [replayDag] at h
      cases h
      simp
  | cons step rest ih =>
      rcases step with ⟨i, j⟩
      cases hi : inputs[i]? with
      | none => simp [replayDag, hi] at h
      | some left =>
          cases hj : inputs[j]? with
          | none => simp [replayDag, hi, hj] at h
          | some right =>
              have hrest :
                  replayDag (inputs ++ [xorRow left right]) rest =
                    some result := by
                simpa [replayDag, hi, hj] using h
              have hlen := ih (inputs ++ [xorRow left right]) hrest
              simp only [List.length_append, List.length_singleton,
                List.length_cons, List.length_nil] at hlen
              simp only [List.length_cons]
              omega

/-- Every output row of a successful DAG replay uses only variables
    from one explicitly supplied input support list. -/
theorem replayDag_preserves_support
    (support : List Nat)
    (inputs : List Row) (steps : List XorRef) (result : List Row)
    (h : replayDag inputs steps = some result)
    (hinput : ∀ row ∈ inputs, ∀ v ∈ row.coefficients, v ∈ support) :
    ∀ row ∈ result, ∀ v ∈ row.coefficients, v ∈ support := by
  induction steps generalizing inputs with
  | nil =>
      simp [replayDag] at h
      cases h
      exact hinput
  | cons step rest ih =>
      rcases step with ⟨i, j⟩
      cases hi : inputs[i]? with
      | none => simp [replayDag, hi] at h
      | some left =>
          cases hj : inputs[j]? with
          | none => simp [replayDag, hi, hj] at h
          | some right =>
              have hrest :
                  replayDag (inputs ++ [xorRow left right]) rest =
                    some result := by
                simpa [replayDag, hi, hj] using h
              have hnext :
                  ∀ row ∈ inputs ++ [xorRow left right],
                    ∀ v ∈ row.coefficients, v ∈ support := by
                intro row hrow v hv
                rcases List.mem_append.mp hrow with hold | hnew
                · exact hinput row hold v hv
                · have heq : row = xorRow left right := by
                    simpa using hnew
                  subst row
                  change v ∈ xorCoefficients
                    left.coefficients right.coefficients at hv
                  rcases xorCoefficients_no_fresh_variable
                    left.coefficients right.coefficients v hv with hl | hr
                  · exact hinput left (getElem?_mem inputs i left hi) v hl
                  · exact hinput right (getElem?_mem inputs j right hj) v hr
              exact ih (inputs ++ [xorRow left right]) hrest hnext

/-- For any accepted source-bound DAG contradiction, the exact number
    of rows and universal no-fresh-variable property are established. -/
theorem checkDagContradiction_resource_sound
    (inputs : List Row) (steps : List XorRef)
    (h : checkDagContradiction inputs steps = true) :
    ∃ result : List Row,
      replayDag inputs steps = some result ∧
      result.length = inputs.length + steps.length ∧
      (∀ row ∈ result, ∀ v ∈ row.coefficients,
        v ∈ inputs.flatMap (fun row => row.coefficients)) := by
  unfold checkDagContradiction at h
  cases hrep : replayDag inputs steps with
  | none => simp [hrep] at h
  | some result =>
      refine ⟨result, by simp [hrep],
        replayDag_length_exact inputs steps result hrep, ?_⟩
      apply replayDag_preserves_support
        (inputs.flatMap (fun row => row.coefficients))
        inputs steps result hrep
      intro row hr v hv
      exact List.mem_flatMap.mpr ⟨row, hr, hv⟩


/-- Symmetric-difference output remains a duplicate-free sparse support
    whenever the two source supports are duplicate-free. -/
theorem xorCoefficients_nodup
    (left right : List Nat)
    (hl : left.Nodup) (hr : right.Nodup) :
    (xorCoefficients left right).Nodup := by
  unfold xorCoefficients
  apply (List.pairwise_append).2
  refine ⟨hl.filter _, hr.filter _, ?_⟩
  intro a ha b hb heq
  have hnot : a ∉ right := by
    have hp := (List.mem_filter.mp ha).2
    simpa using hp
  have hbmem : b ∈ right := (List.mem_filter.mp hb).1
  subst b
  exact hnot hbmem

/-- A row XOR preserves duplicate-free representation. -/
theorem xorRow_nodup
    (left right : Row)
    (hl : left.coefficients.Nodup)
    (hr : right.coefficients.Nodup) :
    (xorRow left right).coefficients.Nodup :=
  xorCoefficients_nodup left.coefficients right.coefficients hl hr

/-- Every row in the replayed append-only DAG remains duplicate-free
    if each original sparse source row is duplicate-free. -/
theorem replayDag_preserves_nodup
    (inputs : List Row) (steps : List XorRef) (result : List Row)
    (h : replayDag inputs steps = some result)
    (hinput : ∀ row ∈ inputs, row.coefficients.Nodup) :
    ∀ row ∈ result, row.coefficients.Nodup := by
  induction steps generalizing inputs with
  | nil =>
      simp [replayDag] at h
      cases h
      exact hinput
  | cons step rest ih =>
      rcases step with ⟨i, j⟩
      cases hi : inputs[i]? with
      | none => simp [replayDag, hi] at h
      | some left =>
          cases hj : inputs[j]? with
          | none => simp [replayDag, hi, hj] at h
          | some right =>
              have hrest :
                  replayDag (inputs ++ [xorRow left right]) rest =
                    some result := by
                simpa [replayDag, hi, hj] using h
              have hnext :
                  ∀ row ∈ inputs ++ [xorRow left right],
                    row.coefficients.Nodup := by
                intro row hrow
                rcases List.mem_append.mp hrow with hold | hnew
                · exact hinput row hold
                · have heq : row = xorRow left right := by
                    simpa using hnew
                  subst row
                  exact xorRow_nodup left right
                    (hinput left (getElem?_mem inputs i left hi))
                    (hinput right (getElem?_mem inputs j right hj))
              exact ih (inputs ++ [xorRow left right]) hrest hnext

#print axioms Witnora.TC063SparseDagResource.xorCoefficients_nodup
#print axioms Witnora.TC063SparseDagResource.replayDag_preserves_nodup


/-- Lean 4.19-compatible finite injection bound: a duplicate-free
    list included in another cannot have more elements than its host. -/
private theorem nodup_subset_length_v419 :
    ∀ (xs ys : List Nat), xs.Nodup → xs ⊆ ys →
      xs.length ≤ ys.length := by
  intro xs
  induction xs with
  | nil =>
      intro ys _ _
      simp
  | cons head tail ih =>
      intro ys hNo hSub
      have hHead : head ∈ ys := hSub (by simp)
      have hNoHead : head ∉ tail := (List.nodup_cons.mp hNo).1
      have hTailNo : tail.Nodup := (List.nodup_cons.mp hNo).2
      have hTailSub : tail ⊆ ys.erase head := by
        intro v hv
        have hNe : v ≠ head := by
          intro heq
          subst v
          exact hNoHead hv
        exact (List.mem_erase_of_ne hNe).2
          (hSub (by simp [hv]))
      have hBound := ih (ys.erase head) hTailNo hTailSub
      have hErase := List.length_erase_of_mem hHead
      have hPositive : 0 < ys.length := by
        cases ys with
        | nil => simp at hHead
        | cons v rest => simp
      simp only [List.length_cons]
      omega

/-- Every derived sparse row has at most as many coefficients as the
    total coefficient occurrences in the *original* row table.
    Crucially, this does not depend on the length of the DAG trace or
    on the numeric magnitude of variable IDs. -/
theorem replayDag_row_width_le_original_support
    (inputs : List Row) (steps : List XorRef) (result : List Row)
    (h : replayDag inputs steps = some result)
    (hNodup : ∀ row ∈ inputs, row.coefficients.Nodup) :
    ∀ row ∈ result,
      row.coefficients.length ≤
        (Witnora.TC063CanonicalBound.supportRows inputs).length := by
  have hNo := replayDag_preserves_nodup inputs steps result h hNodup
  have hSupport := replayDag_preserves_support
    (Witnora.TC063CanonicalBound.supportRows inputs)
    inputs steps result h
    (Witnora.TC063CanonicalBound.row_membership_supportRows inputs)
  intro row hr
  exact nodup_subset_length_v419
    row.coefficients
    (Witnora.TC063CanonicalBound.supportRows inputs)
    (hNo row hr) (hSupport row hr)

/-- An accepted bound-independent source-G5 checker certificate has:
    exactly input_rows + XOR_steps replay rows, and every replay row
    is bounded by the original input coefficient occurrence count. -/
theorem checkSparseG5_resource_bound
    (cnf : Witnora.Concrete.CNF) (rows : List Row)
    (steps : List XorRef)
    (h : Witnora.TC063SparseDirectChecker.checkSparseG5
      cnf rows steps = true) :
    ∃ final : List Row,
      replayDag rows steps = some final ∧
      final.length = rows.length + steps.length ∧
      (∀ row ∈ final,
        row.coefficients.length ≤
          (Witnora.TC063CanonicalBound.supportRows rows).length) := by
  have hp := h
  simp [Witnora.TC063SparseDirectChecker.checkSparseG5] at hp
  have hNodup : ∀ row ∈ rows, row.coefficients.Nodup := hp.1.1
  have hDag : checkDagContradiction rows steps = true := hp.2
  obtain ⟨final, hrep, hlen, _⟩ :=
    checkDagContradiction_resource_sound rows steps hDag
  exact ⟨final, hrep, hlen,
    replayDag_row_width_le_original_support
      rows steps final hrep hNodup⟩

#print axioms Witnora.TC063SparseDagResource.replayDag_row_width_le_original_support
#print axioms Witnora.TC063SparseDagResource.checkSparseG5_resource_bound


/-- The *entire materialized replay table* has a polynomial aggregate
    coefficient count: at most (initial rows + XOR steps) times total
    initial sparse coefficient occurrences. -/
theorem checkSparseG5_total_replay_coefficients_bound
    (cnf : Witnora.Concrete.CNF) (rows : List Row)
    (steps : List XorRef)
    (h : Witnora.TC063SparseDirectChecker.checkSparseG5
      cnf rows steps = true) :
    ∃ final : List Row,
      replayDag rows steps = some final ∧
      (Witnora.TC063CanonicalBound.supportRows final).length ≤
        (rows.length + steps.length) *
          (Witnora.TC063CanonicalBound.supportRows rows).length := by
  obtain ⟨final, hrep, hlen, hwidth⟩ :=
    checkSparseG5_resource_bound cnf rows steps h
  refine ⟨final, hrep, ?_⟩
  have hsum :=
    Witnora.TC063SparseG5OperationBound.supportRows_length_le_arity
      final
      (Witnora.TC063CanonicalBound.supportRows rows).length
      hwidth
  simpa [hlen] using hsum

#print axioms Witnora.TC063SparseDagResource.checkSparseG5_total_replay_coefficients_bound

#print axioms Witnora.TC063SparseDagResource.xorCoefficients_no_fresh_variable
#print axioms Witnora.TC063SparseDagResource.xorCoefficients_length_le_sum
#print axioms Witnora.TC063SparseDagResource.replayDag_length_exact
#print axioms Witnora.TC063SparseDagResource.replayDag_preserves_support
#print axioms Witnora.TC063SparseDagResource.checkDagContradiction_resource_sound


/-! ## Source-operation to compiled-DAG size bridge -/

/-- A successful mutable source operation adds at most one indexed XOR
    reference. Swaps only modify the reference map. -/
private theorem indexedStep_adds_at_most_one
    (state next : Witnora.G5IndexedBridge.State)
    (op : Witnora.G5IndexedBridge.Operation)
    (h : Witnora.G5IndexedBridge.step state op = some next) :
    next.2.length ≤ state.2.length + 1 := by
  rcases state with ⟨refs, steps⟩
  cases op with
  | swapRows i j =>
      cases hi : refs[i]? with
      | none => simp [Witnora.G5IndexedBridge.step, hi] at h
      | some left =>
          cases hj : refs[j]? with
          | none => simp [Witnora.G5IndexedBridge.step, hi, hj] at h
          | some right =>
              simp [Witnora.G5IndexedBridge.step, hi, hj] at h
              cases h
              simp
  | addRowXor target source =>
      by_cases hsame : target == source
      · simp [Witnora.G5IndexedBridge.step, hsame] at h
      · cases hi : refs[target]? with
        | none => simp [Witnora.G5IndexedBridge.step, hsame, hi] at h
        | some left =>
            cases hj : refs[source]? with
            | none =>
                simp [Witnora.G5IndexedBridge.step, hsame, hi, hj] at h
            | some right =>
                simp [Witnora.G5IndexedBridge.step, hsame, hi, hj] at h
                cases h
                simp

/-- In a successful fold, the compiler appends no more XOR pairs than
    the number of mutable source operations it processes. -/
private theorem indexedFold_steps_length_le
    (operations : List Witnora.G5IndexedBridge.Operation)
    (state result : Witnora.G5IndexedBridge.State)
    (h : operations.foldlM Witnora.G5IndexedBridge.step state =
      some result) :
    result.2.length ≤ state.2.length + operations.length := by
  induction operations generalizing state with
  | nil =>
      simp at h
      cases h
      simp
  | cons op rest ih =>
      cases hs : Witnora.G5IndexedBridge.step state op with
      | none => simp [List.foldlM, hs] at h
      | some next =>
          have hrest :
              rest.foldlM Witnora.G5IndexedBridge.step next =
                some result := by
            simpa [List.foldlM, hs] using h
          have hstep := indexedStep_adds_at_most_one state next op hs
          have htail := ih next hrest
          simp only [List.length_cons]
          omega

/-- The actual indexed source-operation compiler emits at most one
    append-only DAG XOR reference for each source instruction.
    This is a universal size guarantee for every successful compile. -/
theorem compile_steps_length_le_source_operations
    (initialRows : Nat)
    (operations : List Witnora.G5IndexedBridge.Operation)
    (steps : List XorRef)
    (h : Witnora.G5IndexedBridge.compile initialRows operations =
      some steps) :
    steps.length ≤ operations.length := by
  unfold Witnora.G5IndexedBridge.compile at h
  cases hf : operations.foldlM Witnora.G5IndexedBridge.step
      (List.range initialRows, []) with
  | none => simp [hf] at h
  | some result =>
      simp [hf] at h
      subst steps
      have hb := indexedFold_steps_length_le operations
        (List.range initialRows, []) result hf
      simpa using hb

/-- If compiled source instructions form an accepted sparse certificate,
    the total replay table has at most (initial rows + source instruction
    count) times original coefficient occurrences. -/
theorem checkSparseG5_compiled_replay_bound
    (cnf : Witnora.Concrete.CNF)
    (rows : List Row)
    (operations : List Witnora.G5IndexedBridge.Operation)
    (steps : List XorRef)
    (hCompile : Witnora.G5IndexedBridge.compile rows.length operations =
      some steps)
    (hCheck : Witnora.TC063SparseDirectChecker.checkSparseG5
      cnf rows steps = true) :
    ∃ final : List Row,
      replayDag rows steps = some final ∧
      (Witnora.TC063CanonicalBound.supportRows final).length ≤
        (rows.length + operations.length) *
          (Witnora.TC063CanonicalBound.supportRows rows).length := by
  obtain ⟨final, hrep, hbound⟩ :=
    checkSparseG5_total_replay_coefficients_bound cnf rows steps hCheck
  have hsteps := compile_steps_length_le_source_operations
    rows.length operations steps hCompile
  exact ⟨final, hrep, Nat.le_trans hbound
    (Nat.mul_le_mul_right
      (Witnora.TC063CanonicalBound.supportRows rows).length
      (Nat.add_le_add_left hsteps rows.length))⟩

#print axioms Witnora.TC063SparseDagResource.compile_steps_length_le_source_operations
#print axioms Witnora.TC063SparseDagResource.checkSparseG5_compiled_replay_bound


/-- The actual total pivot-ledger emitter's operation count composes with
    the exact indexed compiler and checker bounds.  Both compiler
    success and checker acceptance remain explicit hypotheses. -/
theorem emitted_sparse_schedule_compiled_replay_bound
    (cnf : Witnora.Concrete.CNF)
    (rows : List Row)
    (outcome : Witnora.G5RetiredPivotLedger.PivotOutcome rows)
    (steps : List XorRef)
    (hEmit : Witnora.G5RetiredPivotLedger.emitScheduleWithPivots
      rows (Witnora.TC063CanonicalBound.supportRows rows)
      (List.range rows.length)
      (Witnora.G5IndexedOperationEmitter.SourceState.start rows) =
        some outcome)
    (hCompile : Witnora.G5IndexedBridge.compile
      rows.length outcome.operations = some steps)
    (hCheck : Witnora.TC063SparseDirectChecker.checkSparseG5
      cnf rows steps = true) :
    ∃ final : List Row,
      replayDag rows steps = some final ∧
      (Witnora.TC063CanonicalBound.supportRows final).length ≤
        (rows.length +
          (Witnora.TC063CanonicalBound.supportRows rows).length *
            rows.length) *
          (Witnora.TC063CanonicalBound.supportRows rows).length := by
  obtain ⟨produced, hRun, hCount⟩ :=
    Witnora.TC063SparseG5OperationBound.tc063_total_sparse_schedule_quadratic_op_count
      rows
  rw [hEmit] at hRun
  cases hRun
  obtain ⟨final, hRep, hBound⟩ :=
    checkSparseG5_compiled_replay_bound
      cnf rows outcome.operations steps hCompile hCheck
  exact ⟨final, hRep,
    Nat.le_trans hBound
      (Nat.mul_le_mul_right
        (Witnora.TC063CanonicalBound.supportRows rows).length
        (Nat.add_le_add_left hCount rows.length))⟩

#print axioms Witnora.TC063SparseDagResource.emitted_sparse_schedule_compiled_replay_bound


/-! ## Universal source interpreter to indexed compiler refinement -/

/-- For every successful source-state transition, the original indexed
    compiler performs the matching reference-map and DAG-step update.
    The input-slot count is the persistent source-state invariant. -/
private theorem sourceStep_refines_indexedCompiler
    (initial : List Row)
    (state next : Witnora.G5IndexedOperationEmitter.SourceState initial)
    (op : Witnora.G5IndexedBridge.Operation)
    (hLength : state.refs.length = initial.length)
    (hStep : Witnora.G5IndexedOperationEmitter.SourceState.step
      initial state op = some next) :
    Witnora.G5IndexedBridge.step (state.refs, state.dag.steps) op =
      some (next.refs, next.dag.steps) := by
  cases op with
  | swapRows i j =>
      cases hi : state.refs[i]? with
      | none =>
          simp [Witnora.G5IndexedOperationEmitter.SourceState.step, hi] at hStep
      | some left =>
          cases hj : state.refs[j]? with
          | none =>
              simp [Witnora.G5IndexedOperationEmitter.SourceState.step,
                hi, hj] at hStep
          | some right =>
              simp [Witnora.G5IndexedOperationEmitter.SourceState.step,
                hi, hj] at hStep
              subst next
              exact Witnora.G5IndexedLengthRefinement.swap_step_refines_compiler
                initial state i j left right hi hj
  | addRowXor target source =>
      by_cases hEq : target = source
      · subst source
        simp [Witnora.G5IndexedOperationEmitter.SourceState.step] at hStep
      · have hNe : (target == source) = false :=
          decide_eq_false hEq
        cases ht : state.refs[target]? with
        | none =>
            simp [Witnora.G5IndexedOperationEmitter.SourceState.step,
              hNe, ht] at hStep
        | some targetRef =>
            cases hs : state.refs[source]? with
            | none =>
                simp [Witnora.G5IndexedOperationEmitter.SourceState.step,
                  hNe, ht, hs] at hStep
            | some sourceRef =>
                cases htr : state.dag.rows[targetRef]? with
                | none =>
                    simp [Witnora.G5IndexedOperationEmitter.SourceState.step,
                      hNe, ht, hs, htr] at hStep
                | some targetRow =>
                    cases hsr : state.dag.rows[sourceRef]? with
                    | none =>
                        simp [Witnora.G5IndexedOperationEmitter.SourceState.step,
                          hNe, ht, hs, htr, hsr] at hStep
                    | some sourceRow =>
                        simp [Witnora.G5IndexedOperationEmitter.SourceState.step,
                          hNe, ht, hs, htr, hsr] at hStep
                        simp [htr, hsr] at hStep
                        cases hStep
                        exact Witnora.G5IndexedLengthRefinement.xor_step_refines_compiler
                          initial state target source targetRef sourceRef
                          hEq hLength ht hs

/-- Inductively, *all* successful source-interpreter operations agree
    exactly with compiler state: both the mutable refs and XOR DAG steps. -/
private theorem sourceFold_refines_indexedCompiler
    (initial : List Row)
    (operations : List Witnora.G5IndexedBridge.Operation)
    (state result :
      Witnora.G5IndexedOperationEmitter.SourceState initial)
    (hLength : state.refs.length = initial.length)
    (hRun : operations.foldlM
      (fun s op =>
        Witnora.G5IndexedOperationEmitter.SourceState.step initial s op)
      state = some result) :
    operations.foldlM Witnora.G5IndexedBridge.step
      (state.refs, state.dag.steps) =
        some (result.refs, result.dag.steps) := by
  induction operations generalizing state with
  | nil =>
      simp at hRun
      cases hRun
      simp
  | cons op rest ih =>
      cases hs :
          Witnora.G5IndexedOperationEmitter.SourceState.step
            initial state op with
      | none =>
          simp [List.foldlM_cons, hs] at hRun
      | some next =>
          have hRest : rest.foldlM
              (fun s op =>
                Witnora.G5IndexedOperationEmitter.SourceState.step
                  initial s op)
              next = some result := by
            simpa [List.foldlM_cons, hs] using hRun
          have hBridge := sourceStep_refines_indexedCompiler
            initial state next op hLength hs
          have hNextLength : next.refs.length = initial.length := by
            have hPreserve :=
              Witnora.G5IndexedExecutionInvariant.step_preserves_ref_length
                (state.refs, state.dag.steps)
                (next.refs, next.dag.steps) op hBridge
            exact hPreserve.trans hLength
          simpa [List.foldlM_cons, hBridge] using
            ih next hNextLength hRest

/-- A successful execution by the *actual* proof-carrying source
    interpreter always compiles to exactly its recorded DAG step list.
    No separate successful-compile hypothesis is needed. -/
theorem sourceRun_compiler_exact
    (initial : List Row)
    (operations : List Witnora.G5IndexedBridge.Operation)
    (result : Witnora.G5IndexedOperationEmitter.SourceState initial)
    (hRun : Witnora.G5IndexedOperationEmitter.run
      initial operations = some result) :
    Witnora.G5IndexedBridge.compile initial.length operations =
      some result.dag.steps := by
  have hLength :
      (Witnora.G5IndexedOperationEmitter.SourceState.start initial).refs.length =
        initial.length := by
    simp [Witnora.G5IndexedOperationEmitter.SourceState.start]
  have hFold := sourceFold_refines_indexedCompiler
    initial operations
    (Witnora.G5IndexedOperationEmitter.SourceState.start initial)
    result hLength hRun
  have hFold' :
      operations.foldlM Witnora.G5IndexedBridge.step
        (List.range initial.length, []) =
          some (result.refs, result.dag.steps) := by
    simpa [Witnora.G5IndexedOperationEmitter.SourceState.start,
      Witnora.G5VerifiedDagEmitter.Builder.start] using hFold
  simp [Witnora.G5IndexedBridge.compile, hFold']

#print axioms Witnora.TC063SparseDagResource.sourceRun_compiler_exact

end Witnora.TC063SparseDagResource
