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

#print axioms Witnora.G14DFSPreseen.preseen_never_reprocesses_old
#print axioms Witnora.G14DFSPreseen.preseen_terminates_on_finite_closed_graph

end Witnora.G14DFSPreseen
