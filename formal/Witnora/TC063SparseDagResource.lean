import Witnora.TC063SparseG5OperationBound

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
  exact List.Nodup.length_le_of_subset
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

end Witnora.TC063SparseDagResource
