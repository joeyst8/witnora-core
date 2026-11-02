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
      simpa [enqueue, hv] using hprocSeen x hxOld

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
          exact hsubset x (by simp [hp, hx])
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

/-- Even a repeated neighbor appears only once on the initial frontier. -/
example :
    (enqueueAll [2, 2, 3, 2] (start 1)).seen.Nodup := by
  exact (enqueueAll_preserves_safe [2, 2, 3, 2]
    (start 1) (start_safe 1)).1

#print axioms Witnora.G14DFSSeenEnqueue.enqueue_preserves_safe
#print axioms Witnora.G14DFSSeenEnqueue.step_preserves_safe
#print axioms Witnora.G14DFSSeenEnqueue.run_preserves_safe
#print axioms Witnora.G14DFSSeenEnqueue.run_preserves_strong_safe

end Witnora.G14DFSSeenEnqueue
