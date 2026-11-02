import Witnora.G14DFSPreseen

/-!
# G14 numerical owner labels from verified DFS components

The verified outer scan returns pairwise-disjoint, complete components.
This module assigns a deterministic numeric index to the first component
containing each variable, proves the labels agree across every original
primal edge surviving separator removal, and composes this result with
the universal conditioned residual-clause ownership theorem.

Membership-based ownership remains correct under *any* permutation of
the component list, so Python's final sorting does not affect soundness.
Matching Python's exact sorting and CPython execution is still open.
-/

namespace Witnora.G14DFSOwnerLabels

open Witnora.G14DFSSeenEnqueue
open Witnora.G14DFSOuterScan
open Witnora.G14DFSPreseen
open Witnora.G14PrimalEdgeOwnership

def residualNeighbors (source : Witnora.Concrete.CNF)
    (separator : List Nat) : Nat → List Nat :=
  separatedNeighbors (clauseNeighbors source) separator

def residualVertices (source : Witnora.Concrete.CNF)
    (separator : List Nat) : List Nat :=
  remainingVertices (sourceVertices source) separator

def rawResidualComponents (source : Witnora.Concrete.CNF)
    (separator : List Nat) : List (List Nat) :=
  (scanComponents (residualNeighbors source separator)
    (residualVertices source separator).length
    (residualVertices source separator) [] []).2

/-- Every nonseparator edge sees exactly the same component membership
    at its two endpoints, for each recorded component. -/
def EdgeHomogeneous (source : Witnora.Concrete.CNF)
    (separator : List Nat) (components : List (List Nat)) : Prop :=
  ∀ component ∈ components, ∀ u v,
    SourceEdge source u v →
    u ∉ separator → v ∉ separator →
      (u ∈ component ↔ v ∈ component)

/-- The outer scan preserves the edge-homogeneity property of its
    accumulator, since every new component is a full DFS root component. -/
theorem scan_preserves_edge_homogeneous
    (source : Witnora.Concrete.CNF) (separator : List Nat)
    (starts : List Nat) :
    ∀ (seen : List Nat) (components : List (List Nat)),
      (∀ root ∈ starts, root ∈ residualVertices source separator) →
      EdgeHomogeneous source separator components →
      EdgeHomogeneous source separator
        (scanComponents (residualNeighbors source separator)
          (residualVertices source separator).length
          starts seen components).2 := by
  induction starts with
  | nil =>
      intro seen components _ hOld
      simpa [scanComponents] using hOld
  | cons root rest ih =>
      intro seen components hStarts hOld
      have hRoot :
          root ∈ residualVertices source separator :=
        hStarts root (by simp)
      have hRest : ∀ w ∈ rest,
          w ∈ residualVertices source separator := by
        intro w hw
        exact hStarts w (by simp [hw])
      by_cases hr : root ∈ seen
      · simpa [scanComponents, hr] using
          ih seen components hRest hOld
      · let found := (run (residualNeighbors source separator)
          (residualVertices source separator).length (start root)).processed
        have hRootParts :=
          (mem_remainingVertices_iff
            (sourceVertices source) separator root).mp hRoot
        have hFoundHomogeneous :
            ∀ u v, SourceEdge source u v →
              u ∉ separator → v ∉ separator →
              (u ∈ found ↔ v ∈ found) := by
          intro u v hEdge hu hv
          exact residual_primal_edge_processed_iff
            source separator root u v
            hRootParts.1 hRootParts.2 hEdge hu hv
        have hNew : EdgeHomogeneous source separator
            (found :: components) := by
          intro component hc u v hEdge hu hv
          rcases List.mem_cons.mp hc with hEq | hOldComponent
          · subst component
            exact hFoundHomogeneous u v hEdge hu hv
          · exact hOld component hOldComponent u v hEdge hu hv
        simpa [scanComponents, hr, found, residualNeighbors,
          residualVertices] using
          ih (found ++ seen) (found :: components) hRest hNew

theorem raw_residual_components_edge_homogeneous
    (source : Witnora.Concrete.CNF) (separator : List Nat) :
    EdgeHomogeneous source separator
      (rawResidualComponents source separator) := by
  exact scan_preserves_edge_homogeneous source separator
    (residualVertices source separator) [] []
    (by intro root hRoot; exact hRoot)
    (by intro component hc; cases hc)

/-- Missing variables receive the sentinel index `components.length`.
    Coverage theorems later ensure no nonseparator source variable needs it. -/
def componentIndex : List (List Nat) → Nat → Nat
  | [], _ => 0
  | component :: rest, v =>
      if v ∈ component then 0 else Nat.succ (componentIndex rest v)

theorem componentIndex_eq_of_membership_agreement
    (components : List (List Nat)) (u v : Nat) :
    (∀ component ∈ components, u ∈ component ↔ v ∈ component) →
      componentIndex components u = componentIndex components v := by
  induction components with
  | nil =>
      intro _
      rfl
  | cons component rest ih =>
      intro hAgree
      have hHead := hAgree component (by simp)
      have hRest : ∀ other ∈ rest, u ∈ other ↔ v ∈ other := by
        intro other hOther
        exact hAgree other (by simp [hOther])
      by_cases hu : u ∈ component
      · have hv : v ∈ component := hHead.mp hu
        simp [componentIndex, hu, hv]
      · have hv : v ∉ component := by
          intro hv
          exact hu (hHead.mpr hv)
        simp [componentIndex, hu, hv, ih hRest]

theorem componentIndex_edge_consistent
    (source : Witnora.Concrete.CNF) (separator : List Nat)
    (components : List (List Nat))
    (hHomogeneous : EdgeHomogeneous source separator components) :
    EdgeConsistent source separator (componentIndex components) := by
  intro u v hEdge hu hv
  apply componentIndex_eq_of_membership_agreement
  intro component hc
  exact hHomogeneous component hc u v hEdge hu hv

theorem raw_component_index_edge_consistent
    (source : Witnora.Concrete.CNF) (separator : List Nat) :
    EdgeConsistent source separator
      (componentIndex (rawResidualComponents source separator)) := by
  exact componentIndex_edge_consistent source separator
    (rawResidualComponents source separator)
    (raw_residual_components_edge_homogeneous source separator)

/-- The component index inferred from DFS agrees on every surviving
    nonseparator literal of any conditioned source clause. -/
theorem conditioned_residual_owner_from_dfs
    (source : Witnora.Concrete.CNF) (separator : List Nat)
    (fixed : Nat → Option Bool)
    (clause residual : List Witnora.Concrete.Literal)
    (hSource : clause ∈ source)
    (hCondition :
      Witnora.Conditioning.conditionClause fixed clause = some residual)
    (u v : Witnora.Concrete.Literal)
    (hu : u ∈ residual) (hv : v ∈ residual)
    (huOutside : u.1 ∉ separator) (hvOutside : v.1 ∉ separator) :
    componentIndex (rawResidualComponents source separator) u.1 =
      componentIndex (rawResidualComponents source separator) v.1 := by
  exact conditioned_residual_has_one_component
    source separator
    (componentIndex (rawResidualComponents source separator))
    (raw_component_index_edge_consistent source separator)
    fixed clause residual hSource hCondition
    u v hu hv huOutside hvOutside

theorem edge_homogeneous_perm
    (source : Witnora.Concrete.CNF) (separator : List Nat)
    (components ordered : List (List Nat))
    (hHomogeneous : EdgeHomogeneous source separator components)
    (hPerm : components.Perm ordered) :
    EdgeHomogeneous source separator ordered := by
  intro component hc u v hEdge hu hv
  exact hHomogeneous component ((hPerm.mem_iff).mpr hc)
    u v hEdge hu hv

/-- In particular, Python may reorder the completed component list
    before numbering it without creating a cross-component clause. -/
theorem permuted_dfs_component_index_edge_consistent
    (source : Witnora.Concrete.CNF) (separator : List Nat)
    (ordered : List (List Nat))
    (hPerm : (rawResidualComponents source separator).Perm ordered) :
    EdgeConsistent source separator (componentIndex ordered) := by
  exact componentIndex_edge_consistent source separator ordered
    (edge_homogeneous_perm source separator
      (rawResidualComponents source separator) ordered
      (raw_residual_components_edge_homogeneous source separator) hPerm)


/-!
## Component coverage and actual index lookup

A label is only useful for the G14 residual partition when it points to
an emitted component containing the vertex.  We first show that every
marked vertex appears in a recorded component, then combine this invariant
with the existing exact seen-set coverage theorem.
-/

/-- Every vertex marked by the scan belongs to a recorded component. -/
def SeenRepresented (seen : List Nat)
    (components : List (List Nat)) : Prop :=
  ∀ v ∈ seen, ∃ component, component ∈ components ∧ v ∈ component

theorem scan_preserves_seen_represented
    (neighbors : Nat → List Nat) (fuel : Nat)
    (starts seen : List Nat) (components : List (List Nat))
    (hRepresented : SeenRepresented seen components) :
    SeenRepresented
      (scanComponents neighbors fuel starts seen components).1
      (scanComponents neighbors fuel starts seen components).2 := by
  induction starts generalizing seen components with
  | nil =>
      simpa [scanComponents] using hRepresented
  | cons root rest ih =>
      by_cases hr : root ∈ seen
      · simpa [scanComponents, hr] using
          ih seen components hRepresented
      · let found := (run neighbors fuel (start root)).processed
        have hNew : SeenRepresented
            (found ++ seen) (found :: components) := by
          intro v hv
          rcases List.mem_append.mp hv with hFound | hOld
          · exact ⟨found, by simp, hFound⟩
          · rcases hRepresented v hOld with ⟨component, hc, hvc⟩
            exact ⟨component, by simp [hc], hvc⟩
        simpa [scanComponents, hr, found] using
          ih (found ++ seen) (found :: components) hNew

/-- Every nonseparator source variable belongs to a completed
    residual DFS component, not merely to the global seen set. -/
theorem raw_residual_components_cover
    (source : Witnora.Concrete.CNF) (separator : List Nat)
    (v : Nat) (hv : v ∈ residualVertices source separator) :
    ∃ component, component ∈ rawResidualComponents source separator ∧
      v ∈ component := by
  have hSeen :
      v ∈ (scanComponents
        (residualNeighbors source separator)
        (residualVertices source separator).length
        (residualVertices source separator) [] []).1 :=
    (scan_seen_exact_residual_source source separator v).mpr hv
  have hRepresented := scan_preserves_seen_represented
    (residualNeighbors source separator)
    (residualVertices source separator).length
    (residualVertices source separator) [] []
    (by intro w hw; cases hw)
  exact hRepresented v hSeen

/-- If a vertex is contained in one of the component records, its
    computed index retrieves a component that contains the vertex. -/
theorem componentIndex_selects_member
    (components : List (List Nat)) (v : Nat)
    (hCovered : ∃ component, component ∈ components ∧ v ∈ component) :
    ∃ component,
      components.get? (componentIndex components v) = some component ∧
      v ∈ component := by
  induction components with
  | nil =>
      rcases hCovered with ⟨component, hc, _⟩
      cases hc
  | cons first rest ih =>
      by_cases hv : v ∈ first
      · exact ⟨first, by simp [componentIndex, hv], hv⟩
      · have hRest : ∃ component, component ∈ rest ∧
            v ∈ component := by
          rcases hCovered with ⟨component, hc, hMember⟩
          rcases List.mem_cons.mp hc with hEq | hTail
          · subst component
            exact False.elim (hv hMember)
          · exact ⟨component, hTail, hMember⟩
        rcases ih hRest with ⟨component, hGet, hMember⟩
        refine ⟨component, ?_, hMember⟩
        simpa [componentIndex, hv] using hGet

theorem raw_component_index_selects_member
    (source : Witnora.Concrete.CNF) (separator : List Nat)
    (v : Nat) (hv : v ∈ residualVertices source separator) :
    ∃ component,
      (rawResidualComponents source separator).get?
        (componentIndex (rawResidualComponents source separator) v) =
          some component ∧
      v ∈ component := by
  exact componentIndex_selects_member
    (rawResidualComponents source separator) v
    (raw_residual_components_cover source separator v hv)

/-- Any permutation, including the final Python-style component ordering,
    still assigns every residual variable to an actual containing record. -/
theorem permuted_dfs_component_index_selects_member
    (source : Witnora.Concrete.CNF) (separator : List Nat)
    (ordered : List (List Nat))
    (hPerm : (rawResidualComponents source separator).Perm ordered)
    (v : Nat) (hv : v ∈ residualVertices source separator) :
    ∃ component,
      ordered.get? (componentIndex ordered v) = some component ∧
      v ∈ component := by
  apply componentIndex_selects_member ordered v
  rcases raw_residual_components_cover source separator v hv with
    ⟨component, hc, hMember⟩
  exact ⟨component, (hPerm.mem_iff).mp hc, hMember⟩

#print axioms Witnora.G14DFSOwnerLabels.raw_residual_components_cover
#print axioms Witnora.G14DFSOwnerLabels.raw_component_index_selects_member
#print axioms Witnora.G14DFSOwnerLabels.permuted_dfs_component_index_selects_member

#print axioms Witnora.G14DFSOwnerLabels.raw_component_index_edge_consistent
#print axioms Witnora.G14DFSOwnerLabels.conditioned_residual_owner_from_dfs
#print axioms Witnora.G14DFSOwnerLabels.permuted_dfs_component_index_edge_consistent

end Witnora.G14DFSOwnerLabels
