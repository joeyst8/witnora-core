import Witnora.ClauseViolationParity

/-!
# Geometry: direct parity-factor scope cannot erase source clause edges

A factor for a parity row contains the union of variables in every source
clause selected by that row. If every source clause occurs in at least one
row, each original clause's variable pairs occur together in some new
factor. Thus the direct parity primal graph contains the source primal
graph (and cannot have lower *optimal* treewidth).

This does NOT apply to shared auxiliary-variable decompositions,
polynomial cancellations, or more sophisticated tensor representations.
It is a no-go result only for the direct union-of-source-scopes model.
-/

namespace Witnora.GeometryScope

/-- Abstract clause variable lists. An out-of-range source row contributes
    no variables; source-index coverage is separately required. -/
def rowScope (source : List (List Nat)) (row : List Nat) : List Nat :=
  row.flatMap (fun j => (source[j]?).getD [])

/-- Any variable in a selected source clause is in the direct factor scope. -/
theorem selected_clause_variable_in_scope
    (source : List (List Nat)) (row : List Nat)
    (j v : Nat) (hj : j ∈ row)
    (hv : v ∈ (source[j]?).getD []) :
    v ∈ rowScope source row := by
  unfold rowScope
  exact List.mem_flatMap.mpr ⟨j, hj, hv⟩

/-- If clause j is selected by some row, both its variable occurrences
    survive together within a parity factor. -/
theorem selected_clause_pair_in_some_scope
    (source : List (List Nat)) (rows : List (List Nat))
    (j u v : Nat)
    (hcovered : ∃ row ∈ rows, j ∈ row)
    (hu : u ∈ (source[j]?).getD [])
    (hv : v ∈ (source[j]?).getD []) :
    ∃ row ∈ rows, u ∈ rowScope source row ∧
      v ∈ rowScope source row := by
  obtain ⟨row, hrow, hj⟩ := hcovered
  exact ⟨row, hrow,
    selected_clause_variable_in_scope source row j u hj hu,
    selected_clause_variable_in_scope source row j v hj hv⟩

def SourcePair (source : List (List Nat)) (u v : Nat) : Prop :=
  ∃ j, j < source.length ∧
    u ∈ (source[j]?).getD [] ∧ v ∈ (source[j]?).getD []

def RowPair (source : List (List Nat)) (rows : List (List Nat))
    (u v : Nat) : Prop :=
  ∃ row ∈ rows, u ∈ rowScope source row ∧
    v ∈ rowScope source row

/-- Source primal-edge containment in the direct parity-factor primal
    graph, provided that every source index is covered by a parity row. -/
theorem all_source_pairs_preserved
    (source : List (List Nat)) (rows : List (List Nat))
    (hcover : ∀ j, j < source.length → ∃ row ∈ rows, j ∈ row)
    (u v : Nat)
    (hpair : SourcePair source u v) :
    RowPair source rows u v := by
  obtain ⟨j, hj, hu, hv⟩ := hpair
  exact selected_clause_pair_in_some_scope
    source rows j u v (hcover j hj) hu hv

example : rowScope [[1, 2, 3], [2, 4]] [0, 1] =
    [1, 2, 3, 2, 4] := by decide

#print axioms Witnora.GeometryScope.selected_clause_variable_in_scope
#print axioms Witnora.GeometryScope.selected_clause_pair_in_some_scope
#print axioms Witnora.GeometryScope.all_source_pairs_preserved

end Witnora.GeometryScope
