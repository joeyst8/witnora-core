import Witnora.G14DFSLabelCheck

/-!
# Universal DFS worklist and neighbor-expansion safety

Model an explicit finite-fuel DFS worklist with a processed set. Every
processed vertex has all its outgoing neighbors either already processed
or still pending. No processed vertex is inserted twice. When the
worklist empties, every edge out of the visited component stays inside.

The proof covers all finite adjacency lists and all step budgets.
A sufficient *universal termination bound*, and correspondence to
Python's exact seen-at-enqueue traversal, remain separate obligations.
-/

namespace Witnora.G14DFSWorklist

structure State where
  pending : List Nat
  processed : List Nat
  deriving DecidableEq, Repr

def start (root : Nat) : State :=
  ⟨[root], []⟩

/-- A vertex is expanded only once; its neighbors enter the stack. -/
def step (neighbors : Nat → List Nat) (state : State) : State :=
  match state.pending with
  | [] => state
  | vertex :: rest =>
      if vertex ∈ state.processed then
        ⟨rest, state.processed⟩
      else
        ⟨neighbors vertex ++ rest, vertex :: state.processed⟩

def run (neighbors : Nat → List Nat) : Nat → State → State
  | 0, state => state
  | fuel + 1, state => run neighbors fuel (step neighbors state)

/-- No neighbor of a fully processed vertex is forgotten: it is either
    processed already or is waiting on the worklist. -/
def NeighborsAccounted (neighbors : Nat → List Nat)
    (state : State) : Prop :=
  ∀ vertex ∈ state.processed, ∀ neighbor ∈ neighbors vertex,
    neighbor ∈ state.processed ∨ neighbor ∈ state.pending

theorem start_accounted (neighbors : Nat → List Nat) (root : Nat) :
    NeighborsAccounted neighbors (start root) := by
  intro vertex hv
  simp [start] at hv

/-- Every DFS step preserves the neighbor-accounting invariant, even
    when a vertex is popped more than once. -/
theorem step_preserves_accounting
    (neighbors : Nat → List Nat) (state : State)
    (h : NeighborsAccounted neighbors state) :
    NeighborsAccounted neighbors (step neighbors state) := by
  cases hp : state.pending with
  | nil =>
      simpa [step, hp] using h
  | cons vertex rest =>
      by_cases hseen : vertex ∈ state.processed
      · simp only [step, hp, hseen, ↓reduceIte]
        intro u hu w hw
        rcases h u hu w hw with hdone | hpending
        · exact Or.inl hdone
        · have hc : w = vertex ∨ w ∈ rest := by
            simpa [hp] using hpending
          rcases hc with rfl | hrest
          · exact Or.inl hseen
          · exact Or.inr hrest
      · simp only [step, hp, hseen, ↓reduceIte]
        intro u hu w hw
        rcases List.mem_cons.mp hu with heq | hold
        · subst u
          exact Or.inr (List.mem_append.mpr (Or.inl hw))
        · rcases h u hold w hw with hdone | hpending
          · exact Or.inl (List.mem_cons_of_mem _ hdone)
          · have hc : w = vertex ∨ w ∈ rest := by
              simpa [hp] using hpending
            rcases hc with rfl | hrest
            · exact Or.inl (by simp)
            · exact Or.inr (List.mem_append.mpr (Or.inr hrest))

/-- Every finite prefix of DFS, regardless of its length, preserves
    the same invariant. -/
theorem run_preserves_accounting
    (neighbors : Nat → List Nat) (fuel : Nat) (state : State)
    (h : NeighborsAccounted neighbors state) :
    NeighborsAccounted neighbors (run neighbors fuel state) := by
  induction fuel generalizing state with
  | zero => exact h
  | succ n ih =>
      exact ih (step neighbors state)
        (step_preserves_accounting neighbors state h)

/-- DFS never appends a previously processed vertex to the processed
    set, so its visited list remains duplicate-free. -/
theorem step_preserves_nodup
    (neighbors : Nat → List Nat) (state : State)
    (h : state.processed.Nodup) :
    (step neighbors state).processed.Nodup := by
  cases hp : state.pending with
  | nil => simpa [step, hp] using h
  | cons vertex rest =>
      by_cases hv : vertex ∈ state.processed
      · simpa [step, hp, hv] using h
      · simpa [step, hp, hv] using
          (List.nodup_cons.mpr ⟨hv, h⟩)

theorem run_preserves_nodup
    (neighbors : Nat → List Nat) (fuel : Nat) (state : State)
    (h : state.processed.Nodup) :
    (run neighbors fuel state).processed.Nodup := by
  induction fuel generalizing state with
  | zero => exact h
  | succ n ih =>
      exact ih (step neighbors state)
        (step_preserves_nodup neighbors state h)

/-- An exhausted worklist certifies that every outgoing edge from a
    processed vertex remains within the processed component. -/
theorem exhausted_worklist_is_edge_closed
    (neighbors : Nat → List Nat) (fuel root : Nat)
    (hfinished : (run neighbors fuel (start root)).pending = []) :
    ∀ vertex ∈ (run neighbors fuel (start root)).processed,
      ∀ neighbor ∈ neighbors vertex,
        neighbor ∈ (run neighbors fuel (start root)).processed := by
  have h := run_preserves_accounting neighbors fuel (start root)
    (start_accounted neighbors root)
  intro vertex hv neighbor hn
  rcases h vertex hv neighbor hn with hdone | hpending
  · exact hdone
  · rw [hfinished] at hpending
    cases hpending

/-- Concrete triangle DFS terminates and has no unprocessed edge. -/
def triangle : Nat → List Nat
  | 1 => [2, 3]
  | 2 => [1, 3]
  | 3 => [1, 2]
  | _ => []

example : (run triangle 20 (start 1)).pending = [] := by decide

example : (run triangle 20 (start 1)).processed.Nodup := by
  exact run_preserves_nodup triangle 20 (start 1) (by decide)

#print axioms Witnora.G14DFSWorklist.step_preserves_accounting
#print axioms Witnora.G14DFSWorklist.run_preserves_accounting
#print axioms Witnora.G14DFSWorklist.exhausted_worklist_is_edge_closed

end Witnora.G14DFSWorklist
