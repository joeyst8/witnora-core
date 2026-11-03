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
      refine ⟨result, hrep,
        replayDag_length_exact inputs steps result hrep, ?_⟩
      apply replayDag_preserves_support
        (inputs.flatMap (fun row => row.coefficients))
        inputs steps result hrep
      intro row hr v hv
      exact List.mem_flatMap.mpr ⟨row, hr, hv⟩

#print axioms Witnora.TC063SparseDagResource.xorCoefficients_no_fresh_variable
#print axioms Witnora.TC063SparseDagResource.xorCoefficients_length_le_sum
#print axioms Witnora.TC063SparseDagResource.replayDag_length_exact
#print axioms Witnora.TC063SparseDagResource.replayDag_preserves_support
#print axioms Witnora.TC063SparseDagResource.checkDagContradiction_resource_sound

end Witnora.TC063SparseDagResource
