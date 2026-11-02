import Witnora.G14DFSSeenEnqueue

/-!
# G14 outer component scan: coverage and monotone seen bookkeeping

Python's `_components_after_removing` visits every remaining graph key in
sorted order. It skips any root already discovered by earlier traversal,
otherwise performs a full DFS and adds that component to the global seen set.

This mathematical outer-loop model computes each root's verified complete
component using the seen-at-enqueue traversal. Subsequent theorems prove
that the scan keeps all previously marked vertices and covers every input
start vertex, regardless of scan order or duplicate start entries.
Proving the list of output components contains no duplicates and directly
refining Python's shared mutable `seen` set remain separate steps.
-/

namespace Witnora.G14DFSOuterScan

open Witnora.G14DFSSeenEnqueue

/-- A functional outer-loop analog of Python's global seen guard.
    The component accumulator is in reverse discovery order. -/
def scanComponents (neighbors : Nat → List Nat) (fuel : Nat) :
    List Nat → List Nat → List (List Nat) → List Nat × List (List Nat)
  | [], seen, components => (seen, components)
  | root :: rest, seen, components =>
      if root ∈ seen then
        scanComponents neighbors fuel rest seen components
      else
        let found := (run neighbors fuel (start root)).processed
        scanComponents neighbors fuel rest
          (found ++ seen) (found :: components)

/-- Scanning never loses an already discovered vertex. -/
theorem scan_seen_monotone
    (neighbors : Nat → List Nat) (fuel : Nat)
    (starts seen : List Nat) (components : List (List Nat))
    (v : Nat) (h : v ∈ seen) :
    v ∈ (scanComponents neighbors fuel starts seen components).1 := by
  induction starts generalizing seen components with
  | nil => simpa [scanComponents] using h
  | cons root rest ih =>
      by_cases hr : root ∈ seen
      · simpa [scanComponents, hr] using ih seen components h
      · let found := (run neighbors fuel (start root)).processed
        have hNew : v ∈ found ++ seen := by
          simp [h]
        simpa [scanComponents, hr, found] using
          ih (found ++ seen) (found :: components) hNew

/-- Every possible root is included in its complete bounded traversal. -/
theorem root_in_full_component
    (neighbors : Nat → List Nat) (vertices : List Nat)
    (hClosed : NeighborWithin neighbors vertices)
    (root : Nat) (hRoot : root ∈ vertices) :
    root ∈ (run neighbors vertices.length (start root)).processed := by
  exact (start_run_exact_reachable neighbors vertices root root
    hClosed hRoot).mpr Reachable.base

/-- Independently of initial seen and accumulator contents, scanning
    a list of eligible roots eventually marks every root in that list. -/
theorem scan_covers_starts
    (neighbors : Nat → List Nat) (vertices : List Nat)
    (hClosed : NeighborWithin neighbors vertices)
    (starts : List Nat) :
    ∀ (seen : List Nat) (components : List (List Nat)),
      (∀ v ∈ starts, v ∈ vertices) →
      ∀ v ∈ starts,
        v ∈ (scanComponents neighbors vertices.length
          starts seen components).1 := by
  induction starts with
  | nil =>
      intro seen components _ v hv
      cases hv
  | cons root rest ih =>
      intro seen components hStarts v hv
      have hRoot : root ∈ vertices :=
        hStarts root (by simp)
      have hRest : ∀ w ∈ rest, w ∈ vertices := by
        intro w hw
        exact hStarts w (by simp [hw])
      by_cases hr : root ∈ seen
      · have hTarget :
            v ∈ (scanComponents neighbors vertices.length
              rest seen components).1 := by
          rcases List.mem_cons.mp hv with hEq | hTail
          · subst v
            exact scan_seen_monotone neighbors vertices.length
              rest seen components root hr
          · exact ih seen components hRest v hTail
        simpa [scanComponents, hr] using hTarget
      · let found := (run neighbors vertices.length (start root)).processed
        let newSeen := found ++ seen
        let newComponents := found :: components
        have hRootFound : root ∈ found :=
          root_in_full_component neighbors vertices hClosed root hRoot
        have hTarget :
            v ∈ (scanComponents neighbors vertices.length
              rest newSeen newComponents).1 := by
          rcases List.mem_cons.mp hv with hEq | hTail
          · subst v
            have hMarked : root ∈ newSeen := by
              simp [newSeen, hRootFound]
            exact scan_seen_monotone neighbors vertices.length
              rest newSeen newComponents root hMarked
          · exact ih newSeen newComponents hRest v hTail
        simpa [scanComponents, hr, found, newSeen, newComponents] using hTarget

/-- A full outer scan marks every vertex in a finite closed graph. -/
theorem scan_covers_finite_graph
    (neighbors : Nat → List Nat) (vertices : List Nat)
    (hClosed : NeighborWithin neighbors vertices) :
    ∀ v ∈ vertices,
      v ∈ (scanComponents neighbors vertices.length
        vertices [] []).1 := by
  exact scan_covers_starts neighbors vertices hClosed
    vertices [] [] (by intro v hv; exact hv)

/-- Specialization to source-CNF primal components after removing the
    separator, matching Python's mathematical outer-loop iteration set. -/
theorem scan_covers_residual_source_variables
    (source : Witnora.Concrete.CNF) (separator : List Nat) :
    ∀ v ∈ remainingVertices (sourceVertices source) separator,
      v ∈ (scanComponents
        (separatedNeighbors (clauseNeighbors source) separator)
        (remainingVertices (sourceVertices source) separator).length
        (remainingVertices (sourceVertices source) separator)
        [] []).1 := by
  exact scan_covers_finite_graph
    (separatedNeighbors (clauseNeighbors source) separator)
    (remainingVertices (sourceVertices source) separator)
    (separatedNeighbors_closed
      (clauseNeighbors source) (sourceVertices source)
      separator (clauseNeighbors_closed source))

/-!
## Exact global seen-set coverage

Coverage alone does not establish that Python's global seen set has no
spurious variables. We also prove closure of every discovered component
under the finite universe, then prove that the outer scan preserves
universe containment. Together the two directions yield exact membership.
-/

theorem full_component_within
    (neighbors : Nat → List Nat) (vertices : List Nat)
    (hClosed : NeighborWithin neighbors vertices)
    (root v : Nat) (hRoot : root ∈ vertices)
    (hProcessed :
      v ∈ (run neighbors vertices.length (start root)).processed) :
    v ∈ vertices := by
  have hStrong :=
    start_run_strong_safe neighbors vertices.length root
  have hSeen : v ∈ (run neighbors vertices.length (start root)).seen :=
    hStrong.2.2.2 v hProcessed
  have hWithin :=
    run_preserves_seen_within neighbors vertices vertices.length
      (start root) hClosed (start_strong_safe root)
      (start_seen_within vertices root hRoot)
  exact hWithin v hSeen

theorem scan_seen_within
    (neighbors : Nat → List Nat) (vertices : List Nat)
    (hClosed : NeighborWithin neighbors vertices)
    (starts : List Nat) :
    ∀ (seen : List Nat) (components : List (List Nat)),
      (∀ v ∈ seen, v ∈ vertices) →
      (∀ v ∈ starts, v ∈ vertices) →
      ∀ v ∈ (scanComponents neighbors vertices.length
        starts seen components).1, v ∈ vertices := by
  induction starts with
  | nil =>
      intro seen components hSeen _ v hv
      exact hSeen v (by simpa [scanComponents] using hv)
  | cons root rest ih =>
      intro seen components hSeen hStarts v hv
      have hRoot : root ∈ vertices :=
        hStarts root (by simp)
      have hRest : ∀ w ∈ rest, w ∈ vertices := by
        intro w hw
        exact hStarts w (by simp [hw])
      by_cases hr : root ∈ seen
      · have hTail :=
          ih seen components hSeen hRest v
        exact hTail (by simpa [scanComponents, hr] using hv)
      · let found := (run neighbors vertices.length (start root)).processed
        have hNewSeen : ∀ w ∈ found ++ seen, w ∈ vertices := by
          intro w hw
          rcases List.mem_append.mp hw with hFound | hOld
          · exact full_component_within
              neighbors vertices hClosed root w hRoot hFound
          · exact hSeen w hOld
        have hTail :=
          ih (found ++ seen) (found :: components) hNewSeen hRest v
        exact hTail (by simpa [scanComponents, hr, found] using hv)

/-- Full scan of a finite closed graph sets `seen` to exactly that
    graph's vertex set as a membership predicate. -/
theorem scan_seen_exact_finite_graph
    (neighbors : Nat → List Nat) (vertices : List Nat)
    (hClosed : NeighborWithin neighbors vertices)
    (v : Nat) :
    v ∈ (scanComponents neighbors vertices.length
      vertices [] []).1 ↔ v ∈ vertices := by
  constructor
  · intro hv
    exact scan_seen_within neighbors vertices hClosed
      vertices [] [] (by intro w hw; cases hw)
      (by intro w hw; exact hw) v hv
  · intro hv
    exact scan_covers_finite_graph neighbors vertices hClosed v hv

theorem scan_seen_exact_residual_source
    (source : Witnora.Concrete.CNF) (separator : List Nat)
    (v : Nat) :
    v ∈ (scanComponents
      (separatedNeighbors (clauseNeighbors source) separator)
      (remainingVertices (sourceVertices source) separator).length
      (remainingVertices (sourceVertices source) separator)
      [] []).1 ↔
        v ∈ remainingVertices (sourceVertices source) separator := by
  exact scan_seen_exact_finite_graph
    (separatedNeighbors (clauseNeighbors source) separator)
    (remainingVertices (sourceVertices source) separator)
    (separatedNeighbors_closed (clauseNeighbors source)
      (sourceVertices source) separator (clauseNeighbors_closed source)) v

/-!
## Exact component non-overlap

A previously completed component is closed under all graph edges. In a
symmetric graph, a root outside such a closed seen set cannot have any
reachable vertex inside it: otherwise the path could be reversed and
would place the root back in seen. This is the key invariant behind
Python's global skip guard and duplicate-free component enumeration.
-/

def EdgeClosed (neighbors : Nat → List Nat) (seen : List Nat) : Prop :=
  ∀ u ∈ seen, ∀ v ∈ neighbors u, v ∈ seen

theorem edge_closed_reachable
    (neighbors : Nat → List Nat) (seen : List Nat)
    (hClosed : EdgeClosed neighbors seen)
    (root v : Nat) (hRoot : root ∈ seen)
    (hReach : Reachable neighbors root v) :
    v ∈ seen := by
  induction hReach with
  | base => exact hRoot
  | edge u w _ hEdge ih =>
      exact hClosed u ih w hEdge

theorem full_component_edge_closed
    (neighbors : Nat → List Nat) (vertices : List Nat)
    (hUniverse : NeighborWithin neighbors vertices)
    (root : Nat) (hRoot : root ∈ vertices) :
    EdgeClosed neighbors
      (run neighbors vertices.length (start root)).processed := by
  intro u hu v hv
  have hReachU : Reachable neighbors root u :=
    (start_run_exact_reachable neighbors vertices root u
      hUniverse hRoot).mp hu
  exact (start_run_exact_reachable neighbors vertices root v
    hUniverse hRoot).mpr (Reachable.edge u v hReachU hv)

theorem edge_closed_append
    (neighbors : Nat → List Nat) (left right : List Nat)
    (hLeft : EdgeClosed neighbors left)
    (hRight : EdgeClosed neighbors right) :
    EdgeClosed neighbors (left ++ right) := by
  intro u hu v hv
  rcases List.mem_append.mp hu with hL | hR
  · exact List.mem_append.mpr (Or.inl (hLeft u hL v hv))
  · exact List.mem_append.mpr (Or.inr (hRight u hR v hv))

theorem full_component_disjoint_from_closed_seen
    (neighbors : Nat → List Nat) (vertices : List Nat)
    (hUniverse : NeighborWithin neighbors vertices)
    (hSymm : SymmetricOn neighbors vertices)
    (root : Nat) (hRoot : root ∈ vertices)
    (seen : List Nat)
    (hSeenClosed : EdgeClosed neighbors seen)
    (hRootNotSeen : root ∉ seen) :
    ∀ v ∈ (run neighbors vertices.length (start root)).processed,
      v ∉ seen := by
  intro v hv hvSeen
  have hRootV : Reachable neighbors root v :=
    (start_run_exact_reachable neighbors vertices root v
      hUniverse hRoot).mp hv
  have hVRoot : Reachable neighbors v root :=
    reachable_reverse_on neighbors vertices hUniverse hSymm
      root v hRoot hRootV
  exact hRootNotSeen
    (edge_closed_reachable neighbors seen hSeenClosed v root hvSeen hVRoot)

/-- Pairwise non-overlap by list position, even if two component lists
    happen to be syntactically equal. -/
def PairwiseDisjoint : List (List Nat) → Prop
  | [] => True
  | current :: rest =>
      PairwiseDisjoint rest ∧
      ∀ other ∈ rest, ∀ v, v ∈ current → v ∉ other

def ComponentsWithin (seen : List Nat) (components : List (List Nat)) : Prop :=
  ∀ component ∈ components, ∀ v ∈ component, v ∈ seen

def ScanSafe (neighbors : Nat → List Nat)
    (result : List Nat × List (List Nat)) : Prop :=
  EdgeClosed neighbors result.1 ∧
  ComponentsWithin result.1 result.2 ∧
  PairwiseDisjoint result.2

theorem prepend_components_within
    (seen found : List Nat) (components : List (List Nat))
    (hWithin : ComponentsWithin seen components) :
    ComponentsWithin (found ++ seen) (found :: components) := by
  intro component hc v hv
  rcases List.mem_cons.mp hc with hNew | hOld
  · subst component
    exact List.mem_append.mpr (Or.inl hv)
  · exact List.mem_append.mpr
      (Or.inr (hWithin component hOld v hv))

theorem prepend_component_disjoint
    (seen found : List Nat) (components : List (List Nat))
    (hWithin : ComponentsWithin seen components)
    (hPair : PairwiseDisjoint components)
    (hFoundDisjoint : ∀ v ∈ found, v ∉ seen) :
    PairwiseDisjoint (found :: components) := by
  change PairwiseDisjoint components ∧
    (∀ other ∈ components, ∀ v, v ∈ found → v ∉ other)
  refine ⟨hPair, ?_⟩
  intro other hOther v hv hInOther
  exact hFoundDisjoint v hv (hWithin other hOther v hInOther)

/-- The outer scan preserves closed seen membership and pairwise
    disjointness of its recorded components. -/
theorem scan_preserves_partition_safety
    (neighbors : Nat → List Nat) (vertices : List Nat)
    (hUniverse : NeighborWithin neighbors vertices)
    (hSymm : SymmetricOn neighbors vertices)
    (starts : List Nat) :
    ∀ (seen : List Nat) (components : List (List Nat)),
      (∀ v ∈ starts, v ∈ vertices) →
      EdgeClosed neighbors seen →
      ComponentsWithin seen components →
      PairwiseDisjoint components →
      ScanSafe neighbors (scanComponents neighbors vertices.length
        starts seen components) := by
  induction starts with
  | nil =>
      intro seen components _ hSeen hWithin hPair
      exact ⟨hSeen, hWithin, hPair⟩
  | cons root rest ih =>
      intro seen components hStarts hSeen hWithin hPair
      have hRoot : root ∈ vertices :=
        hStarts root (by simp)
      have hRest : ∀ w ∈ rest, w ∈ vertices := by
        intro w hw
        exact hStarts w (by simp [hw])
      by_cases hr : root ∈ seen
      · simpa [scanComponents, hr] using
          ih seen components hRest hSeen hWithin hPair
      · let found := (run neighbors vertices.length (start root)).processed
        have hFoundClosed : EdgeClosed neighbors found :=
          full_component_edge_closed neighbors vertices
            hUniverse root hRoot
        have hDisjoint : ∀ v ∈ found, v ∉ seen :=
          full_component_disjoint_from_closed_seen
            neighbors vertices hUniverse hSymm
            root hRoot seen hSeen hr
        have hNewSeen : EdgeClosed neighbors (found ++ seen) :=
          edge_closed_append neighbors found seen hFoundClosed hSeen
        have hNewWithin :
            ComponentsWithin (found ++ seen) (found :: components) :=
          prepend_components_within seen found components hWithin
        have hNewPair : PairwiseDisjoint (found :: components) :=
          prepend_component_disjoint seen found components
            hWithin hPair hDisjoint
        simpa [scanComponents, hr, found] using
          ih (found ++ seen) (found :: components)
            hRest hNewSeen hNewWithin hNewPair

/-- The entire outer scan records pairwise disjoint components. -/
theorem scan_components_pairwise_disjoint
    (neighbors : Nat → List Nat) (vertices : List Nat)
    (hUniverse : NeighborWithin neighbors vertices)
    (hSymm : SymmetricOn neighbors vertices) :
    PairwiseDisjoint
      (scanComponents neighbors vertices.length vertices [] []).2 := by
  have hSafe := scan_preserves_partition_safety
    neighbors vertices hUniverse hSymm vertices [] []
    (by intro v hv; exact hv)
    (by intro v hv; cases hv)
    (by intro component hc; cases hc)
    (by simp [PairwiseDisjoint])
  exact hSafe.2.2

theorem scan_residual_components_pairwise_disjoint
    (source : Witnora.Concrete.CNF) (separator : List Nat) :
    PairwiseDisjoint (scanComponents
      (separatedNeighbors (clauseNeighbors source) separator)
      (remainingVertices (sourceVertices source) separator).length
      (remainingVertices (sourceVertices source) separator)
      [] []).2 := by
  exact scan_components_pairwise_disjoint
    (separatedNeighbors (clauseNeighbors source) separator)
    (remainingVertices (sourceVertices source) separator)
    (separatedNeighbors_closed (clauseNeighbors source)
      (sourceVertices source) separator (clauseNeighbors_closed source))
    (residual_primal_symmetric_on source separator)

#print axioms Witnora.G14DFSOuterScan.scan_components_pairwise_disjoint
#print axioms Witnora.G14DFSOuterScan.scan_residual_components_pairwise_disjoint

#print axioms Witnora.G14DFSOuterScan.scan_seen_exact_finite_graph
#print axioms Witnora.G14DFSOuterScan.scan_seen_exact_residual_source

#print axioms Witnora.G14DFSOuterScan.scan_seen_monotone
#print axioms Witnora.G14DFSOuterScan.scan_covers_starts
#print axioms Witnora.G14DFSOuterScan.scan_covers_residual_source_variables

end Witnora.G14DFSOuterScan
