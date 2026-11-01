import Witnora.G14DFSWorklist

/-!
# Universal finite-fuel termination bound for G14 DFS

The stack's remaining work is paid for by a finite credit account:
one unit per pending stack entry plus one future unit for every outgoing
neighbor of every not-yet-processed vertex. Every nonempty DFS step
decreases this credit by exactly one. Hence the initial credit count
is a sufficient bound for an empty worklist on any finite closed graph.
-/

namespace Witnora.G14DFSFiniteFuel

open Witnora.G14DFSWorklist

/-- Future neighbor-enqueue credit for not-yet-processed vertices. -/
def reserve (neighbors : Nat → List Nat) :
    List Nat → List Nat → Nat
  | [], _ => 0
  | vertex :: rest, processed =>
      (if vertex ∈ processed then 0 else (neighbors vertex).length) +
        reserve neighbors rest processed

/-- Marking a vertex absent from the finite vertices does not change
    the remaining neighbor credits. -/
theorem reserve_add_absent (neighbors : Nat → List Nat)
    (vertices processed : List Nat) (v : Nat)
    (hv : v ∉ vertices) :
    reserve neighbors vertices (v :: processed) =
      reserve neighbors vertices processed := by
  induction vertices with
  | nil => rfl
  | cons head tail ih =>
      have hne : head ≠ v := by
        intro heq
        subst head
        exact hv (by simp)
      have htail : v ∉ tail := by
        intro hm
        exact hv (by simp [hm])
      simp only [reserve]
      have hmem : (head ∈ v :: processed) ↔ head ∈ processed := by
        simp [hne]
      simp [hmem, ih htail]

/-- Marking an unprocessed vertex in a duplicate-free vertices spends
    exactly that vertex's reserved neighbor credit. -/
theorem reserve_add_present (neighbors : Nat → List Nat)
    (vertices processed : List Nat) (v : Nat)
    (hnd : vertices.Nodup) (hv : v ∈ vertices)
    (hunseen : v ∉ processed) :
    reserve neighbors vertices (v :: processed) +
      (neighbors v).length =
    reserve neighbors vertices processed := by
  induction vertices with
  | nil => simp at hv
  | cons head tail ih =>
      have hparts := List.nodup_cons.mp hnd
      rcases List.mem_cons.mp hv with heq | htailmem
      · subst head
        have hrest := reserve_add_absent neighbors tail processed v
          hparts.1
        simp [reserve, hunseen, hrest]
      · have hne : head ≠ v := by
          intro heq
          subst head
          exact hparts.1 htailmem
        have hhead :
            (head ∈ v :: processed) ↔ head ∈ processed := by
          simp [hne]
        have htailEq :=
          ih hparts.2 htailmem hunseen
        simp only [reserve]
        simp [hhead]
        omega

def potential (neighbors : Nat → List Nat)
    (vertices : List Nat) (state : State) : Nat :=
  state.pending.length +
    reserve neighbors vertices state.processed

def PendingWithin (vertices : List Nat) (state : State) : Prop :=
  ∀ v ∈ state.pending, v ∈ vertices

def NeighborWithin (neighbors : Nat → List Nat)
    (vertices : List Nat) : Prop :=
  ∀ v ∈ vertices, ∀ w ∈ neighbors v, w ∈ vertices

theorem step_preserves_pending_within
    (neighbors : Nat → List Nat) (vertices : List Nat)
    (state : State)
    (hneighbor : NeighborWithin neighbors vertices)
    (hstate : PendingWithin vertices state) :
    PendingWithin vertices (step neighbors state) := by
  cases hp : state.pending with
  | nil => simpa [step, hp] using hstate
  | cons vertex rest =>
      have hv : vertex ∈ vertices :=
        hstate vertex (by simp [hp])
      have hrest : ∀ v ∈ rest, v ∈ vertices := by
        intro v hm
        exact hstate v (by simp [hp, hm])
      by_cases hseen : vertex ∈ state.processed
      · simpa [step, hp, hseen, PendingWithin] using hrest
      · simp [step, hp, hseen, PendingWithin]
        intro v hm
        rcases List.mem_append.mp hm with hnew | hold
        · exact hneighbor vertex hv v hnew
        · exact hrest v hold

/-- A nonempty DFS step consumes exactly one unit of total available
    stack-and-neighbor work, for all finite closed adjacency lists. -/
theorem step_spends_one
    (neighbors : Nat → List Nat) (vertices : List Nat)
    (state : State)
    (hnd : vertices.Nodup)
    (hwithin : PendingWithin vertices state)
    (hpop : state.pending ≠ []) :
    potential neighbors vertices (step neighbors state) + 1 =
      potential neighbors vertices state := by
  cases hp : state.pending with
  | nil => exact False.elim (hpop hp)
  | cons vertex rest =>
      have hv : vertex ∈ vertices :=
        hwithin vertex (by simp [hp])
      by_cases hseen : vertex ∈ state.processed
      · simp [potential, step, hp, hseen]
      · have hcredit := reserve_add_present
          neighbors vertices state.processed vertex hnd hv hseen
        simp only [potential, step, hp, hseen, ↓reduceIte,
          List.length_append, List.length_cons]
        omega

theorem run_empty_stays_empty
    (neighbors : Nat → List Nat) (fuel : Nat)
    (state : State) (h : state.pending = []) :
    (run neighbors fuel state).pending = [] := by
  induction fuel generalizing state with
  | zero => exact h
  | succ n ih =>
      have hs : step neighbors state = state := by
        simp [step, h]
      simpa [run, hs] using ih state h

/-- For a finite closed graph, the initial potential is a universally
    sufficient DFS completion budget. No assumed successful run. -/
theorem run_terminates_with_fuel
    (neighbors : Nat → List Nat)
    (vertices : List Nat)
    (hnd : vertices.Nodup)
    (hneighbor : NeighborWithin neighbors vertices)
    (fuel : Nat) (state : State)
    (hwithin : PendingWithin vertices state)
    (hbudget : potential neighbors vertices state ≤ fuel) :
    (run neighbors fuel state).pending = [] := by
  induction fuel generalizing state with
  | zero =>
      have hzero : potential neighbors vertices state = 0 :=
        Nat.eq_zero_of_le_zero hbudget
      have hlen : state.pending.length = 0 := by
        have h := Nat.add_eq_zero_iff.mp hzero
        exact h.1
      have hp : state.pending = [] := List.length_eq_zero.mp hlen
      simpa [run] using hp
  | succ n ih =>
      by_cases hp : state.pending = []
      · exact run_empty_stays_empty neighbors (n + 1) state hp
      · have hstep := step_spends_one neighbors vertices state
          hnd hwithin hp
        have hwithin' := step_preserves_pending_within
          neighbors vertices state hneighbor hwithin
        have hbudget' :
            potential neighbors vertices (step neighbors state) ≤ n := by
          omega
        change (run neighbors n (step neighbors state)).pending = []
        exact ih (step neighbors state) hwithin' hbudget'

/-- Starting from one valid root, the explicit bound needs only the
    finite vertices and the number of adjacency entries it contains. -/
theorem start_terminates
    (neighbors : Nat → List Nat) (vertices : List Nat)
    (hnd : vertices.Nodup)
    (hneighbor : NeighborWithin neighbors vertices)
    (root : Nat) (hroot : root ∈ vertices) :
    (run neighbors
      (potential neighbors vertices (start root))
      (start root)).pending = [] := by
  apply run_terminates_with_fuel
    neighbors vertices hnd hneighbor
  · intro v hv
    simpa [start] using hroot
  · exact Nat.le_refl _

/-- A fully completed DFS therefore produces an edge-closed component
    within a computable universal finite work budget. -/
theorem start_component_closed
    (neighbors : Nat → List Nat) (vertices : List Nat)
    (hnd : vertices.Nodup)
    (hneighbor : NeighborWithin neighbors vertices)
    (root : Nat) (hroot : root ∈ vertices) :
    ∀ v ∈ (run neighbors
      (potential neighbors vertices (start root))
      (start root)).processed,
      ∀ w ∈ neighbors v,
      w ∈ (run neighbors
        (potential neighbors vertices (start root))
        (start root)).processed := by
  exact exhausted_worklist_is_edge_closed
    neighbors (potential neighbors vertices (start root)) root
    (start_terminates neighbors vertices hnd hneighbor root hroot)

/-- Finite cyclic graph termination without a guessed fuel number. -/
example :
    (run triangle (potential triangle [1, 2, 3] (start 1))
      (start 1)).pending = [] := by
  apply start_terminates triangle [1, 2, 3]
  · decide
  · intro v hv w hw
    simp at hv
    rcases hv with rfl | rfl | rfl <;> simp [triangle] at hw ⊢ <;>
      aesop
  · decide

#print axioms Witnora.G14DFSFiniteFuel.run_terminates_with_fuel
#print axioms Witnora.G14DFSFiniteFuel.start_component_closed

end Witnora.G14DFSFiniteFuel
