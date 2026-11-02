import Witnora.G14DFSFiniteFuel

/-!
# G14: seen-at-enqueue worklist safety

The prior DFS worklist model marks vertices when *popped*. Python's
`_components_after_removing` instead marks vertices when *pushed*.
This finite functional model begins the refinement bridge by proving that
seen and pending never gain duplicate vertices, and that every pending
vertex is marked seen. Exact output equality with Python and a universal
termination bound for this second model remain open.
-/

namespace Witnora.G14DFSSeenEnqueue

structure State where
  pending : List Nat
  seen : List Nat
  processed : List Nat
  deriving DecidableEq, Repr

def start (root : Nat) : State :=
  ⟨[root], [root], []⟩

/-- Python appends previously unseen neighbors to the stack and
    marks them seen at enqueue time. -/
def enqueue (v : Nat) (state : State) : State :=
  if v ∈ state.seen then state else
    { state with
      pending := v :: state.pending
      seen := v :: state.seen }

/-- Visit neighbors left to right, preserving the Python LIFO effect. -/
def enqueueAll : List Nat → State → State
  | [], state => state
  | v :: rest, state => enqueueAll rest (enqueue v state)

def step (neighbors : Nat → List Nat) (state : State) : State :=
  match state.pending with
  | [] => state
  | vertex :: rest =>
      enqueueAll (neighbors vertex)
        { state with pending := rest, processed := vertex :: state.processed }

def run (neighbors : Nat → List Nat) : Nat → State → State
  | 0, state => state
  | fuel + 1, state => run neighbors fuel (step neighbors state)

/-- The crucial seen-at-enqueue state invariant. -/
def Safe (state : State) : Prop :=
  state.seen.Nodup ∧
  state.pending.Nodup ∧
  (∀ v ∈ state.pending, v ∈ state.seen)

theorem start_safe (root : Nat) : Safe (start root) := by
  simp [Safe, start]

theorem enqueue_preserves_safe (v : Nat) (state : State)
    (h : Safe state) : Safe (enqueue v state) := by
  rcases h with ⟨hseen, hpending, hsubset⟩
  by_cases hv : v ∈ state.seen
  · simpa [Safe, enqueue, hv] using
      (show Safe state from ⟨hseen, hpending, hsubset⟩)
  · have hnotpending : v ∉ state.pending := by
      intro hmem
      exact hv (hsubset v hmem)
    refine ⟨?_, ?_, ?_⟩
    · simpa [enqueue, hv] using
        (List.nodup_cons.mpr ⟨hv, hseen⟩)
    · simpa [enqueue, hv] using
        (List.nodup_cons.mpr ⟨hnotpending, hpending⟩)
    · intro x hx
      have hx' : x = v ∨ x ∈ state.pending := by
        simpa [enqueue, hv] using hx
      rcases hx' with rfl | hmem
      · simp [enqueue, hv]
      · simp [enqueue, hv, hsubset x hmem]

theorem enqueueAll_preserves_safe (neighbors : List Nat)
    (state : State) (h : Safe state) :
    Safe (enqueueAll neighbors state) := by
  induction neighbors generalizing state with
  | nil =>
      simpa [enqueueAll] using h
  | cons v rest ih =>
      simpa [enqueueAll] using
        ih (enqueue v state) (enqueue_preserves_safe v state h)

theorem step_preserves_safe (neighbors : Nat → List Nat)
    (state : State) (h : Safe state) :
    Safe (step neighbors state) := by
  cases hp : state.pending with
  | nil =>
      simpa [step, hp] using h
  | cons vertex rest =>
      rcases h with ⟨hseen, hpending, hsubset⟩
      have hpn : (vertex :: rest).Nodup := by
        simpa [hp] using hpending
      have hrest : rest.Nodup :=
        (List.nodup_cons.mp hpn).2
      have hsubrest : ∀ v ∈ rest, v ∈ state.seen := by
        intro v hv
        exact hsubset v (by simp [hp, hv])
      have hnext : Safe
          { state with pending := rest, processed := vertex :: state.processed } :=
        ⟨hseen, hrest, hsubrest⟩
      simpa [step, hp] using
        enqueueAll_preserves_safe (neighbors vertex)
          { state with pending := rest, processed := vertex :: state.processed }
          hnext

theorem run_preserves_safe (neighbors : Nat → List Nat)
    (fuel : Nat) (state : State) (h : Safe state) :
    Safe (run neighbors fuel state) := by
  induction fuel generalizing state with
  | zero => simpa [run] using h
  | succ n ih =>
      simpa [run] using
        ih (step neighbors state) (step_preserves_safe neighbors state h)

theorem start_run_safe (neighbors : Nat → List Nat)
    (fuel root : Nat) :
    Safe (run neighbors fuel (start root)) :=
  run_preserves_safe neighbors fuel (start root) (start_safe root)


/--
The stronger Python-specific invariant: processed vertices are unique,
the pending frontier is disjoint from processed vertices, and every
processed vertex remains in seen.
-/
def StrongSafe (state : State) : Prop :=
  Safe state ∧
  state.processed.Nodup ∧
  (∀ v ∈ state.pending, v ∉ state.processed) ∧
  (∀ v ∈ state.processed, v ∈ state.seen)

theorem start_strong_safe (root : Nat) :
    StrongSafe (start root) := by
  simp [StrongSafe, Safe, start]

theorem enqueue_preserves_strong_safe (v : Nat)
    (state : State) (h : StrongSafe state) :
    StrongSafe (enqueue v state) := by
  rcases h with ⟨hsafe, hproc, hdisjoint, hprocSeen⟩
  by_cases hv : v ∈ state.seen
  · simpa [StrongSafe, enqueue, hv] using
      (show StrongSafe state from
        ⟨hsafe, hproc, hdisjoint, hprocSeen⟩)
  · refine ⟨enqueue_preserves_safe v state hsafe, ?_, ?_, ?_⟩
    · simpa [enqueue, hv] using hproc
    · intro x hx hxp
      have hxpOld : x ∈ state.processed := by
        simpa [enqueue, hv] using hxp
      have hx' : x = v ∨ x ∈ state.pending := by
        simpa [enqueue, hv] using hx
      rcases hx' with hEq | hOld
      · subst x
        exact hv (hprocSeen v hxpOld)
      · exact hdisjoint x hOld hxpOld
    · intro x hx
      have hxOld : x ∈ state.processed := by
        simpa [enqueue, hv] using hx
      have hmem : x ∈ v :: state.seen :=
        List.mem_cons_of_mem _ (hprocSeen x hxOld)
      simpa [enqueue, hv] using hmem

theorem enqueueAll_preserves_strong_safe
    (neighbors : List Nat) (state : State)
    (h : StrongSafe state) :
    StrongSafe (enqueueAll neighbors state) := by
  induction neighbors generalizing state with
  | nil => simpa [enqueueAll] using h
  | cons v rest ih =>
      simpa [enqueueAll] using
        ih (enqueue v state)
          (enqueue_preserves_strong_safe v state h)

theorem step_preserves_strong_safe
    (neighbors : Nat → List Nat) (state : State)
    (h : StrongSafe state) :
    StrongSafe (step neighbors state) := by
  cases hp : state.pending with
  | nil => simpa [step, hp] using h
  | cons vertex rest =>
      rcases h with ⟨hsafe, hproc, hdisjoint, hprocSeen⟩
      rcases hsafe with ⟨hseen, hpending, hsubset⟩
      have hpn : (vertex :: rest).Nodup := by
        simpa [hp] using hpending
      have hrest : rest.Nodup := (List.nodup_cons.mp hpn).2
      have hvertexRest : vertex ∉ rest :=
        (List.nodup_cons.mp hpn).1
      have hvertexOld : vertex ∉ state.processed :=
        hdisjoint vertex (by simp [hp])
      let next : State :=
        { state with pending := rest, processed := vertex :: state.processed }
      have hnext : StrongSafe next := by
        refine ⟨?_, ?_, ?_, ?_⟩
        · refine ⟨hseen, hrest, ?_⟩
          intro x hx
          have hxRest : x ∈ rest := by
            simpa [next] using hx
          exact hsubset x (by simp [hp, hxRest])
        · exact List.nodup_cons.mpr ⟨hvertexOld, hproc⟩
        · intro x hx hxp
          have hxRest : x ∈ rest := by
            simpa [next] using hx
          rcases List.mem_cons.mp hxp with hEq | hOld
          · subst x
            exact hvertexRest hxRest
          · exact hdisjoint x (by simp [hp, hxRest]) hOld
        · intro x hxp
          rcases List.mem_cons.mp hxp with hEq | hOld
          · subst x
            exact hsubset vertex (by simp [hp])
          · exact hprocSeen x hOld
      simpa [step, hp, next] using
        enqueueAll_preserves_strong_safe (neighbors vertex) next hnext

theorem run_preserves_strong_safe
    (neighbors : Nat → List Nat) (fuel : Nat)
    (state : State) (h : StrongSafe state) :
    StrongSafe (run neighbors fuel state) := by
  induction fuel generalizing state with
  | zero => simpa [run] using h
  | succ n ih =>
      simpa [run] using ih (step neighbors state)
        (step_preserves_strong_safe neighbors state h)

theorem start_run_strong_safe (neighbors : Nat → List Nat)
    (fuel root : Nat) :
    StrongSafe (run neighbors fuel (start root)) :=
  run_preserves_strong_safe neighbors fuel (start root)
    (start_strong_safe root)


/-- A marked vertex is either pending or already processed.
    The equality is the work-credit invariant for seen-at-enqueue DFS. -/
def Balance (state : State) : Prop :=
  state.seen.length = state.pending.length + state.processed.length

theorem start_balance (root : Nat) : Balance (start root) := by
  simp [Balance, start]

theorem enqueue_preserves_balance (v : Nat) (state : State)
    (h : Balance state) : Balance (enqueue v state) := by
  unfold Balance at h ⊢
  by_cases hv : v ∈ state.seen
  · simpa [enqueue, hv] using h
  · simp [enqueue, hv]
    omega

theorem enqueueAll_preserves_balance (neighbors : List Nat)
    (state : State) (h : Balance state) :
    Balance (enqueueAll neighbors state) := by
  induction neighbors generalizing state with
  | nil => simpa [enqueueAll] using h
  | cons v rest ih =>
      simpa [enqueueAll] using
        ih (enqueue v state) (enqueue_preserves_balance v state h)

theorem step_preserves_balance (neighbors : Nat → List Nat)
    (state : State) (h : Balance state) :
    Balance (step neighbors state) := by
  cases hp : state.pending with
  | nil => simpa [step, hp] using h
  | cons vertex rest =>
      have hnext : Balance
          { state with pending := rest, processed := vertex :: state.processed } := by
        unfold Balance at h ⊢
        simp [hp] at h
        simp
        omega
      simpa [step, hp] using
        enqueueAll_preserves_balance (neighbors vertex)
          { state with pending := rest, processed := vertex :: state.processed }
          hnext

theorem run_preserves_balance (neighbors : Nat → List Nat)
    (fuel : Nat) (state : State) (h : Balance state) :
    Balance (run neighbors fuel state) := by
  induction fuel generalizing state with
  | zero => simpa [run] using h
  | succ n ih =>
      simpa [run] using
        ih (step neighbors state) (step_preserves_balance neighbors state h)

theorem enqueueAll_processed (neighbors : List Nat) (state : State) :
    (enqueueAll neighbors state).processed = state.processed := by
  induction neighbors generalizing state with
  | nil => rfl
  | cons v rest ih =>
      have hsingle : (enqueue v state).processed = state.processed := by
        by_cases hv : v ∈ state.seen
        · simp [enqueue, hv]
        · simp [enqueue, hv]
      simpa [enqueueAll, hsingle] using ih (enqueue v state)

theorem nonempty_step_processes_one (neighbors : Nat → List Nat)
    (state : State) (h : state.pending ≠ []) :
    (step neighbors state).processed.length =
      state.processed.length + 1 := by
  cases hp : state.pending with
  | nil => exact False.elim (h hp)
  | cons vertex rest =>
      simp [step, hp, enqueueAll_processed]

theorem run_empty_stays_empty (neighbors : Nat → List Nat)
    (fuel : Nat) (state : State) (h : state.pending = []) :
    (run neighbors fuel state).pending = [] := by
  induction fuel generalizing state with
  | zero => simpa [run] using h
  | succ n ih =>
      have hs : step neighbors state = state := by
        simp [step, h]
      simpa [run, hs] using ih state h

/-- Each step either finishes the traversal or spends one distinct
    processing credit. This statement has no graph-size assumptions. -/
theorem run_progress (neighbors : Nat → List Nat)
    (fuel : Nat) (state : State) :
    (run neighbors fuel state).pending = [] ∨
    state.processed.length + fuel ≤
      (run neighbors fuel state).processed.length := by
  induction fuel generalizing state with
  | zero =>
      exact Or.inr (by simp [run])
  | succ n ih =>
      by_cases hp : state.pending = []
      · exact Or.inl (by
          simpa [run, step, hp] using
            run_empty_stays_empty neighbors n state hp)
      · have hstep := nonempty_step_processes_one neighbors state hp
        rcases ih (step neighbors state) with hfinished | hcount
        · exact Or.inl (by simpa [run] using hfinished)
        · exact Or.inr (by
            change state.processed.length + (n + 1) ≤
              (run neighbors n (step neighbors state)).processed.length
            omega)

/--
A finite upper bound on visited vertices supplies enough run fuel.
To apply this to an actual graph, one still needs the closure lemma
proving that `seen` stays within the graph's finite vertex list.
-/
theorem run_terminates_under_seen_cap (neighbors : Nat → List Nat)
    (cap : Nat) (state : State)
    (hBalance : Balance state)
    (hCap : (run neighbors cap state).seen.length ≤ cap)
    (hNoProcessed : state.processed = []) :
    (run neighbors cap state).pending = [] := by
  rcases run_progress neighbors cap state with hDone | hCount
  · exact hDone
  · have hFinal := run_preserves_balance neighbors cap state hBalance
    have hZero : state.processed.length = 0 := by
      simp [hNoProcessed]
    have hPendingZero :
        (run neighbors cap state).pending.length = 0 := by
      unfold Balance at hFinal
      omega
    exact List.length_eq_zero.mp hPendingZero

theorem start_terminates_under_seen_cap (neighbors : Nat → List Nat)
    (cap root : Nat)
    (hCap : (run neighbors cap (start root)).seen.length ≤ cap) :
    (run neighbors cap (start root)).pending = [] := by
  exact run_terminates_under_seen_cap neighbors cap (start root)
    (start_balance root) hCap (by rfl)


/-- A duplicate-free list contained in another list cannot be longer.
    Local proof keeps the theorem independent of later Lean versions. -/
theorem nodup_subset_length (xs ys : List Nat)
    (hNodup : xs.Nodup)
    (hSubset : ∀ x, x ∈ xs → x ∈ ys) :
    xs.length ≤ ys.length := by
  induction xs generalizing ys with
  | nil => simp
  | cons x rest ih =>
      have hparts := List.nodup_cons.mp hNodup
      have hMem : x ∈ ys :=
        hSubset x (by simp)
      have hRest : ∀ z, z ∈ rest → z ∈ ys.erase x := by
        intro z hz
        have hNe : z ≠ x := by
          intro heq
          subst z
          exact hparts.1 hz
        apply (List.mem_erase_of_ne hNe).mpr
        exact hSubset z (by simp [hz])
      have hShort := ih (ys.erase x) hparts.2 hRest
      have hErase := List.length_erase_of_mem hMem
      have hPos : 0 < ys.length := by
        cases ys with
        | nil => simp at hMem
        | cons y tail => simp
      simp only [List.length_cons]
      omega

def SeenWithin (vertices : List Nat) (state : State) : Prop :=
  ∀ v ∈ state.seen, v ∈ vertices

def NeighborWithin (neighbors : Nat → List Nat)
    (vertices : List Nat) : Prop :=
  ∀ v ∈ vertices, ∀ w ∈ neighbors v, w ∈ vertices

theorem start_seen_within (vertices : List Nat)
    (root : Nat) (hRoot : root ∈ vertices) :
    SeenWithin vertices (start root) := by
  intro v hv
  have heq : v = root := by
    simpa [start] using hv
  subst v
  exact hRoot

theorem enqueue_preserves_seen_within
    (vertices : List Nat) (v : Nat) (state : State)
    (hV : v ∈ vertices) (h : SeenWithin vertices state) :
    SeenWithin vertices (enqueue v state) := by
  by_cases hv : v ∈ state.seen
  · simpa [SeenWithin, enqueue, hv] using h
  · intro x hx
    have hx' : x = v ∨ x ∈ state.seen := by
      simpa [enqueue, hv] using hx
    rcases hx' with hEq | hOld
    · subst x
      exact hV
    · exact h x hOld

theorem enqueueAll_preserves_seen_within
    (vertices : List Nat) (newNeighbors : List Nat)
    (state : State) :
    (∀ v ∈ newNeighbors, v ∈ vertices) →
    SeenWithin vertices state →
    SeenWithin vertices (enqueueAll newNeighbors state) := by
  induction newNeighbors generalizing state with
  | nil =>
      intro _ h
      simpa [enqueueAll] using h
  | cons v rest ih =>
      intro hWithin h
      have hv : v ∈ vertices :=
        hWithin v (by simp)
      have hRest : ∀ w ∈ rest, w ∈ vertices := by
        intro w hw
        exact hWithin w (by simp [hw])
      simpa [enqueueAll] using
        ih (enqueue v state) hRest
          (enqueue_preserves_seen_within vertices v state hv h)

theorem step_preserves_seen_within
    (neighbors : Nat → List Nat) (vertices : List Nat)
    (state : State)
    (hNeighbor : NeighborWithin neighbors vertices)
    (hStrong : StrongSafe state)
    (hWithin : SeenWithin vertices state) :
    SeenWithin vertices (step neighbors state) := by
  cases hp : state.pending with
  | nil => simpa [step, hp] using hWithin
  | cons vertex rest =>
      have hPending : vertex ∈ state.seen :=
        hStrong.1.2.2 vertex (by simp [hp])
      have hV : vertex ∈ vertices := hWithin vertex hPending
      have hNext : SeenWithin vertices
          { state with pending := rest, processed := vertex :: state.processed } := by
        simpa [SeenWithin] using hWithin
      simpa [step, hp] using
        enqueueAll_preserves_seen_within
          vertices (neighbors vertex)
          { state with pending := rest, processed := vertex :: state.processed }
          (hNeighbor vertex hV) hNext

theorem run_preserves_seen_within
    (neighbors : Nat → List Nat) (vertices : List Nat)
    (fuel : Nat) (state : State)
    (hNeighbor : NeighborWithin neighbors vertices)
    (hStrong : StrongSafe state)
    (hWithin : SeenWithin vertices state) :
    SeenWithin vertices (run neighbors fuel state) := by
  induction fuel generalizing state with
  | zero => simpa [run] using hWithin
  | succ n ih =>
      simpa [run] using ih (step neighbors state)
        (step_preserves_strong_safe neighbors state hStrong)
        (step_preserves_seen_within neighbors vertices state
          hNeighbor hStrong hWithin)

/--
Universal finite termination of the Python-style seen-at-enqueue model.
Under a finite list of vertices closed under all adjacency entries,
the whole traversal finishes in at most `vertices.length` pops.
This is a bound for the Lean model, not yet CPython execution refinement.
-/
theorem start_terminates_on_finite_closed_graph
    (neighbors : Nat → List Nat) (vertices : List Nat)
    (root : Nat)
    (hNeighbor : NeighborWithin neighbors vertices)
    (hRoot : root ∈ vertices) :
    (run neighbors vertices.length (start root)).pending = [] := by
  have hStrong :=
    start_run_strong_safe neighbors vertices.length root
  have hWithin :=
    run_preserves_seen_within neighbors vertices vertices.length
      (start root) hNeighbor (start_strong_safe root)
      (start_seen_within vertices root hRoot)
  have hBound :
      (run neighbors vertices.length (start root)).seen.length ≤
        vertices.length :=
    nodup_subset_length
      (run neighbors vertices.length (start root)).seen vertices
      hStrong.1.1 hWithin
  exact start_terminates_under_seen_cap
    neighbors vertices.length root hBound

/-!
## Reachability soundness

The visited-set discipline is not enough to identify the correct component:
we also need to show that a vertex may only enter the seen set by following
a genuine adjacency edge from a previously reachable vertex. This section
proves that direction, for arbitrary finite or infinite adjacency functions.
-/

/-- Ordinary directed graph reachability, starting from the DFS root. -/
inductive Reachable (neighbors : Nat → List Nat) (root : Nat) : Nat → Prop where
  | base : Reachable neighbors root root
  | edge (u v : Nat) :
      Reachable neighbors root u →
      v ∈ neighbors u →
      Reachable neighbors root v

def SeenReachable (neighbors : Nat → List Nat) (root : Nat)
    (state : State) : Prop :=
  ∀ v ∈ state.seen, Reachable neighbors root v

theorem start_seen_reachable (neighbors : Nat → List Nat) (root : Nat) :
    SeenReachable neighbors root (start root) := by
  intro v hv
  have heq : v = root := by simpa [start] using hv
  subst v
  exact Reachable.base

theorem enqueue_preserves_seen_reachable
    (neighbors : Nat → List Nat) (root v : Nat) (state : State)
    (hV : Reachable neighbors root v)
    (h : SeenReachable neighbors root state) :
    SeenReachable neighbors root (enqueue v state) := by
  by_cases hv : v ∈ state.seen
  · simpa [SeenReachable, enqueue, hv] using h
  · intro x hx
    have hx' : x = v ∨ x ∈ state.seen := by
      simpa [enqueue, hv] using hx
    rcases hx' with hEq | hOld
    · subst x
      exact hV
    · exact h x hOld

theorem enqueueAll_preserves_seen_reachable
    (neighbors : Nat → List Nat) (root : Nat)
    (newNeighbors : List Nat) (state : State)
    (hNeighbors : ∀ v ∈ newNeighbors, Reachable neighbors root v)
    (h : SeenReachable neighbors root state) :
    SeenReachable neighbors root (enqueueAll newNeighbors state) := by
  induction newNeighbors generalizing state with
  | nil =>
      simpa [enqueueAll] using h
  | cons v rest ih =>
      have hv : Reachable neighbors root v :=
        hNeighbors v (by simp)
      have hRest : ∀ w ∈ rest, Reachable neighbors root w := by
        intro w hw
        exact hNeighbors w (by simp [hw])
      simpa [enqueueAll] using
        ih (enqueue v state) hRest
          (enqueue_preserves_seen_reachable neighbors root v state hv h)

theorem step_preserves_seen_reachable
    (neighbors : Nat → List Nat) (root : Nat) (state : State)
    (hStrong : StrongSafe state)
    (h : SeenReachable neighbors root state) :
    SeenReachable neighbors root (step neighbors state) := by
  cases hp : state.pending with
  | nil => simpa [step, hp] using h
  | cons vertex rest =>
      have hPending : vertex ∈ state.seen :=
        hStrong.1.2.2 vertex (by simp [hp])
      have hVertex : Reachable neighbors root vertex :=
        h vertex hPending
      have hNext : SeenReachable neighbors root
          { state with pending := rest, processed := vertex :: state.processed } := by
        simpa [SeenReachable] using h
      have hNeighbors :
          ∀ v ∈ neighbors vertex, Reachable neighbors root v := by
        intro v hv
        exact Reachable.edge vertex v hVertex hv
      simpa [step, hp] using
        enqueueAll_preserves_seen_reachable neighbors root
          (neighbors vertex)
          { state with pending := rest, processed := vertex :: state.processed }
          hNeighbors hNext

theorem run_preserves_seen_reachable
    (neighbors : Nat → List Nat) (root fuel : Nat)
    (state : State)
    (hStrong : StrongSafe state)
    (h : SeenReachable neighbors root state) :
    SeenReachable neighbors root (run neighbors fuel state) := by
  induction fuel generalizing state with
  | zero => simpa [run] using h
  | succ n ih =>
      simpa [run] using
        ih (step neighbors state)
          (step_preserves_strong_safe neighbors state hStrong)
          (step_preserves_seen_reachable neighbors root state hStrong h)

theorem start_run_seen_reachable
    (neighbors : Nat → List Nat) (root fuel : Nat) :
    SeenReachable neighbors root (run neighbors fuel (start root)) := by
  exact run_preserves_seen_reachable neighbors root fuel (start root)
    (start_strong_safe root) (start_seen_reachable neighbors root)

theorem start_run_processed_reachable
    (neighbors : Nat → List Nat) (root fuel v : Nat)
    (hProcessed : v ∈ (run neighbors fuel (start root)).processed) :
    Reachable neighbors root v := by
  have hSeen := (start_run_strong_safe neighbors fuel root).2.2.2
  exact start_run_seen_reachable neighbors root fuel v (hSeen v hProcessed)

#print axioms Witnora.G14DFSSeenEnqueue.start_run_seen_reachable
#print axioms Witnora.G14DFSSeenEnqueue.start_run_processed_reachable

/-- Even a repeated neighbor appears only once on the initial frontier. -/
example :
    (enqueueAll [2, 2, 3, 2] (start 1)).seen.Nodup := by
  exact (enqueueAll_preserves_safe [2, 2, 3, 2]
    (start 1) (start_safe 1)).1

#print axioms Witnora.G14DFSSeenEnqueue.enqueue_preserves_safe
#print axioms Witnora.G14DFSSeenEnqueue.step_preserves_safe
#print axioms Witnora.G14DFSSeenEnqueue.run_preserves_safe
#print axioms Witnora.G14DFSSeenEnqueue.run_preserves_strong_safe
#print axioms Witnora.G14DFSSeenEnqueue.start_terminates_under_seen_cap
#print axioms Witnora.G14DFSSeenEnqueue.start_terminates_on_finite_closed_graph

end Witnora.G14DFSSeenEnqueue
