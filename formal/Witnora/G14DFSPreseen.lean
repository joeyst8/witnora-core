import Witnora.G14DFSOuterScan

/-!
# G14 DFS with Python-style pre-marked global seen state

Python's outer component loop carries a single mutable `seen` set across
separate roots. To begin a formal refinement, this module introduces
the same mark-at-enqueue DFS state initialized with all prior seen
vertices, and a fresh root added to the stack.

These invariants establish that previously marked vertices are never
processed again and that the pre-marked traversal still terminates for
every finite adjacency-closed graph. Exact equality with the fresh-root
component list and CPython's mutable/set/sorting implementation remain
additional proof obligations.
-/

namespace Witnora.G14DFSPreseen

open Witnora.G14DFSSeenEnqueue
open Witnora.G14DFSOuterScan

def startWithSeen (oldSeen : List Nat) (root : Nat) : State :=
  { pending := [root], seen := root :: oldSeen, processed := [] }

/-- Previously marked vertices remain marked, and neither pending nor
    processed may contain an earlier component's vertex. -/
def OldSeenSafe (oldSeen : List Nat) (state : State) : Prop :=
  (∀ v ∈ oldSeen, v ∈ state.seen) ∧
  (∀ v ∈ state.pending, v ∉ oldSeen) ∧
  (∀ v ∈ state.processed, v ∉ oldSeen)

theorem startWithSeen_strong_safe
    (oldSeen : List Nat) (root : Nat)
    (hNodup : oldSeen.Nodup) (hFresh : root ∉ oldSeen) :
    StrongSafe (startWithSeen oldSeen root) := by
  simp [StrongSafe, Safe, startWithSeen, hNodup, hFresh]

theorem startWithSeen_old_safe
    (oldSeen : List Nat) (root : Nat)
    (hFresh : root ∉ oldSeen) :
    OldSeenSafe oldSeen (startWithSeen oldSeen root) := by
  refine ⟨?_, ?_, ?_⟩
  · intro v hv
    simp [startWithSeen, hv]
  · intro v hv
    have heq : v = root := by simpa [startWithSeen] using hv
    subst v
    exact hFresh
  · intro v hv
    simp [startWithSeen] at hv

theorem enqueue_preserves_old_safe
    (oldSeen : List Nat) (v : Nat) (state : State)
    (h : OldSeenSafe oldSeen state) :
    OldSeenSafe oldSeen (enqueue v state) := by
  by_cases hv : v ∈ state.seen
  · simpa [OldSeenSafe, enqueue, hv] using h
  · rcases h with ⟨hMarked, hPending, hProcessed⟩
    have hVFresh : v ∉ oldSeen := by
      intro hOld
      exact hv (hMarked v hOld)
    refine ⟨?_, ?_, ?_⟩
    · intro x hx
      have hInSeen := hMarked x hx
      simp [enqueue, hv, hInSeen]
    · intro x hx
      have hParts : x = v ∨ x ∈ state.pending := by
        simpa [enqueue, hv] using hx
      rcases hParts with rfl | hOld
      · exact hVFresh
      · exact hPending x hOld
    · intro x hx
      have hOld : x ∈ state.processed := by
        simpa [enqueue, hv] using hx
      exact hProcessed x hOld

theorem enqueueAll_preserves_old_safe
    (oldSeen newNeighbors : List Nat) (state : State)
    (h : OldSeenSafe oldSeen state) :
    OldSeenSafe oldSeen (enqueueAll newNeighbors state) := by
  induction newNeighbors generalizing state with
  | nil => simpa [enqueueAll] using h
  | cons v rest ih =>
      simpa [enqueueAll] using
        ih (enqueue v state)
          (enqueue_preserves_old_safe oldSeen v state h)

theorem step_preserves_old_safe
    (oldSeen : List Nat) (neighbors : Nat → List Nat)
    (state : State) (h : OldSeenSafe oldSeen state) :
    OldSeenSafe oldSeen (step neighbors state) := by
  cases hp : state.pending with
  | nil => simpa [step, hp] using h
  | cons vertex rest =>
      rcases h with ⟨hMarked, hPending, hProcessed⟩
      have hVertexFresh : vertex ∉ oldSeen :=
        hPending vertex (by simp [hp])
      let next : State :=
        { state with pending := rest, processed := vertex :: state.processed }
      have hNext : OldSeenSafe oldSeen next := by
        refine ⟨?_, ?_, ?_⟩
        · intro x hx
          exact hMarked x hx
        · intro x hx
          have hRest : x ∈ rest := by simpa [next] using hx
          exact hPending x (by simp [hp, hRest])
        · intro x hx
          have hParts : x = vertex ∨ x ∈ state.processed := by
            simpa [next] using hx
          rcases hParts with rfl | hOld
          · exact hVertexFresh
          · exact hProcessed x hOld
      simpa [step, hp, next] using
        enqueueAll_preserves_old_safe oldSeen (neighbors vertex) next hNext

theorem run_preserves_old_safe
    (oldSeen : List Nat) (neighbors : Nat → List Nat)
    (fuel : Nat) (state : State)
    (h : OldSeenSafe oldSeen state) :
    OldSeenSafe oldSeen (run neighbors fuel state) := by
  induction fuel generalizing state with
  | zero => simpa [run] using h
  | succ n ih =>
      simpa [run] using ih (step neighbors state)
        (step_preserves_old_safe oldSeen neighbors state h)

theorem preseen_never_reprocesses_old
    (oldSeen : List Nat) (neighbors : Nat → List Nat)
    (root fuel v : Nat) (hFresh : root ∉ oldSeen)
    (hProcessed :
      v ∈ (run neighbors fuel (startWithSeen oldSeen root)).processed) :
    v ∉ oldSeen := by
  have hOld := run_preserves_old_safe oldSeen neighbors fuel
    (startWithSeen oldSeen root)
    (startWithSeen_old_safe oldSeen root hFresh)
  exact hOld.2.2 v hProcessed

theorem startWithSeen_within
    (vertices oldSeen : List Nat) (root : Nat)
    (hOldWithin : ∀ v ∈ oldSeen, v ∈ vertices)
    (hRoot : root ∈ vertices) :
    SeenWithin vertices (startWithSeen oldSeen root) := by
  intro v hv
  have hCases : v = root ∨ v ∈ oldSeen := by
    simpa [startWithSeen] using hv
  rcases hCases with rfl | hOld
  · exact hRoot
  · exact hOldWithin v hOld

/-- Unlike the fresh-root balance theorem, this proof does not count
    old seen vertices as pending work. New processed vertices are unique
    and contained in the finite graph, so |vertices|+1 fuel must suffice. -/
theorem preseen_terminates_on_finite_closed_graph
    (neighbors : Nat → List Nat) (vertices oldSeen : List Nat)
    (root : Nat)
    (hNeighbor : NeighborWithin neighbors vertices)
    (hRoot : root ∈ vertices)
    (hOldWithin : ∀ v ∈ oldSeen, v ∈ vertices)
    (hOldNodup : oldSeen.Nodup)
    (hFresh : root ∉ oldSeen) :
    (run neighbors (vertices.length + 1)
      (startWithSeen oldSeen root)).pending = [] := by
  let state := run neighbors (vertices.length + 1)
    (startWithSeen oldSeen root)
  have hStrong : StrongSafe state :=
    run_preserves_strong_safe neighbors (vertices.length + 1)
      (startWithSeen oldSeen root)
      (startWithSeen_strong_safe oldSeen root hOldNodup hFresh)
  have hSeenWithin : SeenWithin vertices state :=
    run_preserves_seen_within neighbors vertices
      (vertices.length + 1) (startWithSeen oldSeen root)
      hNeighbor (startWithSeen_strong_safe oldSeen root hOldNodup hFresh)
      (startWithSeen_within vertices oldSeen root hOldWithin hRoot)
  have hBound : state.processed.length ≤ vertices.length :=
    nodup_subset_length state.processed vertices hStrong.2.1
      (by
        intro v hv
        exact hSeenWithin v (hStrong.2.2.2 v hv))
  rcases run_progress neighbors (vertices.length + 1)
      (startWithSeen oldSeen root) with hDone | hCount
  · exact hDone
  · have hEmptyStart :
        (startWithSeen oldSeen root).processed.length = 0 := by
        rfl
    change (startWithSeen oldSeen root).processed.length +
      (vertices.length + 1) ≤ state.processed.length at hCount
    omega

/-!
## Exact pre-marked versus fresh-root traversal refinement

This is a lockstep simulation: the global pending and processed lists
equal their fresh-root counterparts on every step, while global seen
equals fresh seen appended with the previously completed components.
Closure and symmetry ensure no reachable new vertex belongs to that old
set, so every enqueue makes the same decision. No assumption about the
number or representation order of old vertices is needed.
-/

/-- Global and freshState states have identical active work, with the old
    component set only added to the global seen membership list. -/
def StateExtends (oldSeen : List Nat)
    (freshState global : State) : Prop :=
  global.pending = freshState.pending ∧
  global.processed = freshState.processed ∧
  global.seen = freshState.seen ++ oldSeen

theorem startWithSeen_extends (oldSeen : List Nat) (root : Nat) :
    StateExtends oldSeen (start root) (startWithSeen oldSeen root) := by
  simp [StateExtends, start, startWithSeen]

theorem enqueue_extends
    (oldSeen : List Nat) (v : Nat) (freshState global : State)
    (hFresh : v ∉ oldSeen)
    (hExt : StateExtends oldSeen freshState global) :
    StateExtends oldSeen (enqueue v freshState) (enqueue v global) := by
  rcases hExt with ⟨hPending, hProcessed, hSeen⟩
  have hMem : v ∈ global.seen ↔ v ∈ freshState.seen := by
    rw [hSeen, List.mem_append]
    simp [hFresh]
  by_cases hv : v ∈ freshState.seen
  · have hg : v ∈ global.seen := hMem.mpr hv
    simp [StateExtends, enqueue, hv, hg, hFresh,
      hPending, hProcessed, hSeen]
  · have hg : v ∉ global.seen := by
      intro h
      exact hv (hMem.mp h)
    simp [StateExtends, enqueue, hv, hg, hFresh,
      hPending, hProcessed, hSeen]

theorem enqueueAll_extends
    (oldSeen newNeighbors : List Nat) (freshState global : State)
    (hFresh : ∀ v ∈ newNeighbors, v ∉ oldSeen)
    (hExt : StateExtends oldSeen freshState global) :
    StateExtends oldSeen
      (enqueueAll newNeighbors freshState) (enqueueAll newNeighbors global) := by
  induction newNeighbors generalizing freshState global with
  | nil => simpa [enqueueAll] using hExt
  | cons v rest ih =>
      have hv : v ∉ oldSeen := hFresh v (by simp)
      have hRest : ∀ w ∈ rest, w ∉ oldSeen := by
        intro w hw
        exact hFresh w (by simp [hw])
      simpa [enqueueAll] using
        ih (enqueue v freshState) (enqueue v global) hRest
          (enqueue_extends oldSeen v freshState global hv hExt)

theorem step_extends
    (oldSeen : List Nat) (neighbors : Nat → List Nat)
    (freshState global : State)
    (hExt : StateExtends oldSeen freshState global)
    (hFresh : ∀ u ∈ freshState.pending, ∀ v ∈ neighbors u, v ∉ oldSeen) :
    StateExtends oldSeen (step neighbors freshState) (step neighbors global) := by
  rcases hExt with ⟨hPending, hProcessed, hSeen⟩
  cases hp : freshState.pending with
  | nil =>
      have hg : global.pending = [] := hPending.trans hp
      simpa [step, hp, hg] using
        (show StateExtends oldSeen freshState global from
          ⟨hPending, hProcessed, hSeen⟩)
  | cons vertex rest =>
      have hg : global.pending = vertex :: rest := hPending.trans hp
      let localNext : State :=
        { freshState with pending := rest, processed := vertex :: freshState.processed }
      let globalNext : State :=
        { global with pending := rest, processed := vertex :: global.processed }
      have hNext : StateExtends oldSeen localNext globalNext := by
        refine ⟨?_, ?_, ?_⟩
        · simp [localNext, globalNext]
        · simpa [localNext, globalNext] using
            congrArg (fun xs : List Nat => vertex :: xs) hProcessed
        · simpa [localNext, globalNext] using hSeen
      have hNeighbors : ∀ v ∈ neighbors vertex, v ∉ oldSeen :=
        hFresh vertex (by simp [hp])
      simpa [step, hp, hg, localNext, globalNext] using
        enqueueAll_extends oldSeen (neighbors vertex)
          localNext globalNext hNeighbors hNext

/-- Previously completed, edge-closed components contain no vertex
    reachable from a fresh root outside them, in an undirected graph. -/
theorem reachable_avoids_preseen
    (neighbors : Nat → List Nat) (vertices oldSeen : List Nat)
    (hUniverse : NeighborWithin neighbors vertices)
    (hSymm : Witnora.G14DFSSeenEnqueue.SymmetricOn neighbors vertices)
    (hOldClosed : Witnora.G14DFSOuterScan.EdgeClosed neighbors oldSeen)
    (root v : Nat) (hRoot : root ∈ vertices)
    (hFresh : root ∉ oldSeen)
    (hReach : Reachable neighbors root v) :
    v ∉ oldSeen := by
  intro hv
  have hBack : Reachable neighbors v root :=
    reachable_reverse_on neighbors vertices hUniverse hSymm
      root v hRoot hReach
  exact hFresh
    (Witnora.G14DFSOuterScan.edge_closed_reachable
      neighbors oldSeen hOldClosed v root hv hBack)

/-- One DFS step is identical in active work under global old-seen
    marking, provided the freshState state was generated from the fresh root. -/
theorem step_extends_closed_preseen
    (neighbors : Nat → List Nat) (vertices oldSeen : List Nat)
    (hUniverse : NeighborWithin neighbors vertices)
    (hSymm : SymmetricOn neighbors vertices)
    (hOldClosed : Witnora.G14DFSOuterScan.EdgeClosed neighbors oldSeen)
    (root : Nat) (hRoot : root ∈ vertices)
    (hFreshRoot : root ∉ oldSeen)
    (freshState global : State)
    (hExt : StateExtends oldSeen freshState global)
    (hStrong : StrongSafe freshState)
    (hReach : SeenReachable neighbors root freshState) :
    StateExtends oldSeen
      (step neighbors freshState) (step neighbors global) := by
  apply step_extends oldSeen neighbors freshState global hExt
  intro u hu v hv
  have hUSeen : u ∈ freshState.seen := hStrong.1.2.2 u hu
  have hUReach : Reachable neighbors root u := hReach u hUSeen
  have hVReach : Reachable neighbors root v :=
    Reachable.edge u v hUReach hv
  exact reachable_avoids_preseen neighbors vertices oldSeen
    hUniverse hSymm hOldClosed root v hRoot hFreshRoot hVReach

theorem run_extends_closed_preseen
    (neighbors : Nat → List Nat) (vertices oldSeen : List Nat)
    (hUniverse : NeighborWithin neighbors vertices)
    (hSymm : SymmetricOn neighbors vertices)
    (hOldClosed : Witnora.G14DFSOuterScan.EdgeClosed neighbors oldSeen)
    (root : Nat) (hRoot : root ∈ vertices)
    (hFreshRoot : root ∉ oldSeen)
    (fuel : Nat) (freshState global : State)
    (hExt : StateExtends oldSeen freshState global)
    (hStrong : StrongSafe freshState)
    (hReach : SeenReachable neighbors root freshState) :
    StateExtends oldSeen
      (run neighbors fuel freshState) (run neighbors fuel global) := by
  induction fuel generalizing freshState global with
  | zero => simpa [run] using hExt
  | succ n ih =>
      have hStep := step_extends_closed_preseen
        neighbors vertices oldSeen hUniverse hSymm hOldClosed
        root hRoot hFreshRoot freshState global hExt hStrong hReach
      simpa [run] using
        ih (step neighbors freshState) (step neighbors global) hStep
          (step_preserves_strong_safe neighbors freshState hStrong)
          (step_preserves_seen_reachable neighbors root freshState hStrong hReach)

/-- Strong model-level bridge: for every fuel value, the global preseen
    DFS has exactly the fresh-root processed *list*, not just the same
    reachable set. Its intermediate stack contents also agree. -/
theorem preseen_processes_same_component
    (neighbors : Nat → List Nat) (vertices oldSeen : List Nat)
    (hUniverse : NeighborWithin neighbors vertices)
    (hSymm : SymmetricOn neighbors vertices)
    (hOldClosed : Witnora.G14DFSOuterScan.EdgeClosed neighbors oldSeen)
    (root : Nat) (hRoot : root ∈ vertices)
    (hFresh : root ∉ oldSeen)
    (fuel : Nat) :
    (run neighbors fuel (startWithSeen oldSeen root)).processed =
      (run neighbors fuel (start root)).processed := by
  have hExt := run_extends_closed_preseen
    neighbors vertices oldSeen hUniverse hSymm hOldClosed
    root hRoot hFresh fuel (start root) (startWithSeen oldSeen root)
    (startWithSeen_extends oldSeen root)
    (start_strong_safe root)
    (start_seen_reachable neighbors root)
  exact hExt.2.1

/-- The shared-seen Python-style traversal and fresh-root model return
    the same ordered processing list for any residual primal graph. -/
theorem residual_preseen_processes_same_component
    (source : Witnora.Concrete.CNF) (separator oldSeen : List Nat)
    (root fuel : Nat)
    (hRoot : root ∈ remainingVertices (sourceVertices source) separator)
    (hOldClosed :
      Witnora.G14DFSOuterScan.EdgeClosed
        (separatedNeighbors (clauseNeighbors source) separator) oldSeen)
    (hFresh : root ∉ oldSeen) :
    (run (separatedNeighbors (clauseNeighbors source) separator)
      fuel (startWithSeen oldSeen root)).processed =
    (run (separatedNeighbors (clauseNeighbors source) separator)
      fuel (start root)).processed := by
  exact preseen_processes_same_component
    (separatedNeighbors (clauseNeighbors source) separator)
    (remainingVertices (sourceVertices source) separator)
    oldSeen
    (separatedNeighbors_closed (clauseNeighbors source)
      (sourceVertices source) separator (clauseNeighbors_closed source))
    (residual_primal_symmetric_on source separator)
    hOldClosed root hRoot hFresh fuel

/-!
## Entire shared-seen outer-loop simulation

The functional reference scan uses a fresh-root DFS for each unseen
vertex. The Python-style scan below carries earlier seen entries into
each new DFS. The pointwise lockstep theorem composes across every outer
scan iteration, because completed components remain edge-closed.
Both models therefore produce the exact same ordered list of component
lists and the same final global seen list. Sorting and numeric component
IDs can be applied after this equality without changing it.
-/

/-- Mathematical counterpart of Python's shared-seen outer component
    loop. Unlike `scanComponents`, each inner run starts with the
    previously collected global seen entries. -/
def scanComponentsShared (neighbors : Nat → List Nat) (fuel : Nat) :
    List Nat → List Nat → List (List Nat) → List Nat × List (List Nat)
  | [], seen, components => (seen, components)
  | root :: rest, seen, components =>
      if root ∈ seen then
        scanComponentsShared neighbors fuel rest seen components
      else
        let found := (run neighbors fuel (startWithSeen seen root)).processed
        scanComponentsShared neighbors fuel rest
          (found ++ seen) (found :: components)

/-- Exact list-level refinement of the complete shared-seen outer scan
    to the previously verified fresh-root model. -/
theorem shared_scan_eq_fresh_scan
    (neighbors : Nat → List Nat) (vertices : List Nat)
    (hUniverse : NeighborWithin neighbors vertices)
    (hSymm : SymmetricOn neighbors vertices)
    (starts : List Nat) :
    ∀ (seen : List Nat) (components : List (List Nat)),
      (∀ root ∈ starts, root ∈ vertices) →
      EdgeClosed neighbors seen →
      scanComponentsShared neighbors vertices.length
        starts seen components =
      scanComponents neighbors vertices.length
        starts seen components := by
  induction starts with
  | nil =>
      intro seen components _ _
      rfl
  | cons root rest ih =>
      intro seen components hStarts hSeenClosed
      have hRoot : root ∈ vertices :=
        hStarts root (by simp)
      have hRest : ∀ w ∈ rest, w ∈ vertices := by
        intro w hw
        exact hStarts w (by simp [hw])
      by_cases hr : root ∈ seen
      · simpa [scanComponentsShared, scanComponents, hr] using
          ih seen components hRest hSeenClosed
      · let found := (run neighbors vertices.length (start root)).processed
        have hFoundEq :
            (run neighbors vertices.length
              (startWithSeen seen root)).processed = found :=
          preseen_processes_same_component
            neighbors vertices seen hUniverse hSymm hSeenClosed
            root hRoot hr vertices.length
        have hFoundClosed : EdgeClosed neighbors found :=
          full_component_edge_closed neighbors vertices
            hUniverse root hRoot
        have hNewClosed : EdgeClosed neighbors (found ++ seen) :=
          edge_closed_append neighbors found seen hFoundClosed hSeenClosed
        calc
          scanComponentsShared neighbors vertices.length
              (root :: rest) seen components =
            scanComponentsShared neighbors vertices.length
              rest (found ++ seen) (found :: components) := by
                simp [scanComponentsShared, hr, hFoundEq, found]
          _ = scanComponents neighbors vertices.length
              rest (found ++ seen) (found :: components) :=
            ih (found ++ seen) (found :: components) hRest hNewClosed
          _ = scanComponents neighbors vertices.length
              (root :: rest) seen components := by
                simp [scanComponents, hr, found]

/-- Applied to any source CNF and separator, the Python-style shared
    seen model produces exactly the verified mathematical outer scan
    result: both final global seen and component lists match. -/
theorem residual_shared_scan_eq_fresh_scan
    (source : Witnora.Concrete.CNF) (separator : List Nat) :
    scanComponentsShared
      (separatedNeighbors (clauseNeighbors source) separator)
      (remainingVertices (sourceVertices source) separator).length
      (remainingVertices (sourceVertices source) separator)
      [] [] =
    scanComponents
      (separatedNeighbors (clauseNeighbors source) separator)
      (remainingVertices (sourceVertices source) separator).length
      (remainingVertices (sourceVertices source) separator)
      [] [] := by
  exact shared_scan_eq_fresh_scan
    (separatedNeighbors (clauseNeighbors source) separator)
    (remainingVertices (sourceVertices source) separator)
    (separatedNeighbors_closed (clauseNeighbors source)
      (sourceVertices source) separator (clauseNeighbors_closed source))
    (residual_primal_symmetric_on source separator)
    (remainingVertices (sourceVertices source) separator)
    [] []
    (by intro root hRoot; exact hRoot)
    (by intro u hu; cases hu)

#print axioms Witnora.G14DFSPreseen.shared_scan_eq_fresh_scan
#print axioms Witnora.G14DFSPreseen.residual_shared_scan_eq_fresh_scan

#print axioms Witnora.G14DFSPreseen.preseen_processes_same_component
#print axioms Witnora.G14DFSPreseen.residual_preseen_processes_same_component

#print axioms Witnora.G14DFSPreseen.preseen_never_reprocesses_old
#print axioms Witnora.G14DFSPreseen.preseen_terminates_on_finite_closed_graph

end Witnora.G14DFSPreseen
