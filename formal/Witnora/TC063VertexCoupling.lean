import Witnora.G14DFSSeenEnqueue

/-!
# TC-063: two-vertex cuts by one deletion plus articulation

This module gives graph semantics to the experimental vertex-coupling
heuristic. Reachability is an inductively defined path relation over the
actual adjacency lists, excluding deleted vertices.

For a graph connected after every single-vertex deletion, removing {u,v}
disconnects it exactly when v is an articulation of the residual graph
after removing u. A generic scan that reports precisely such residual
articulations is therefore sound and complete for size-two graph cuts.

This does NOT establish that the existing Python iterative articulation
scanner implements the abstract scan contract. Nor does a graph separator
establish affine residuals, SAT, or any complexity-class result.
-/

namespace Witnora.TC063VertexCoupling

/-- An adjacency-list walk that never visits a blocked vertex. -/
inductive PathAvoiding (neighbors : Nat → List Nat)
    (blocked : List Nat) : Nat → Nat → Prop
  | here (v : Nat) (hv : v ∉ blocked) :
      PathAvoiding neighbors blocked v v
  | step (u v w : Nat) (hu : u ∉ blocked)
      (hedge : v ∈ neighbors u)
      (htail : PathAvoiding neighbors blocked v w) :
      PathAvoiding neighbors blocked u w

/-- Connectivity of the remaining source vertices by explicit paths. -/
def ConnectedAfter (vertices : List Nat)
    (neighbors : Nat → List Nat) (blocked : List Nat) : Prop :=
  ∀ u ∈ vertices, u ∉ blocked →
    ∀ v ∈ vertices, v ∉ blocked →
      PathAvoiding neighbors blocked u v

/-- Graph connectivity and connectivity after every single deletion. -/
def BiconnectedOn (vertices : List Nat)
    (neighbors : Nat → List Nat) : Prop :=
  ConnectedAfter vertices neighbors [] ∧
  ∀ u ∈ vertices, ConnectedAfter vertices neighbors [u]

/-- A genuine two-variable graph cut, with distinct listed vertices. -/
def PairSeparates (vertices : List Nat)
    (neighbors : Nat → List Nat) (u v : Nat) : Prop :=
  u ∈ vertices ∧ v ∈ vertices ∧ u ≠ v ∧
    ¬ ConnectedAfter vertices neighbors [u, v]

/-- The second vertex becomes an articulation after the first is deleted.
    The adjacency and remaining-vertex semantics are shared with PairSeparates. -/
def ResidualArticulation (vertices : List Nat)
    (neighbors : Nat → List Nat) (u v : Nat) : Prop :=
  ConnectedAfter vertices neighbors [u] ∧
    ¬ ConnectedAfter vertices neighbors [u, v]

/-- Universal graph identity behind the new candidate generator. -/
theorem pair_separates_iff_residual_articulation
    (vertices : List Nat) (neighbors : Nat → List Nat)
    (hBi : BiconnectedOn vertices neighbors) (u v : Nat) :
    PairSeparates vertices neighbors u v ↔
      u ∈ vertices ∧ v ∈ vertices ∧ u ≠ v ∧
        ResidualArticulation vertices neighbors u v := by
  constructor
  · intro h
    rcases h with ⟨hu, hv, hne, hCut⟩
    exact ⟨hu, hv, hne, hBi.2 u hu, hCut⟩
  · intro h
    rcases h with ⟨hu, hv, hne, _, hCut⟩
    exact ⟨hu, hv, hne, hCut⟩

/-- Explicit interface for the unverified Python DFS refinement obligation:
    each reported ordered pair must coincide with the residual articulation
    predicate on distinct known vertices. -/
def ExactResidualScan (vertices : List Nat)
    (neighbors : Nat → List Nat) (scan : Nat → Nat → Prop) : Prop :=
  ∀ u v, u ∈ vertices → v ∈ vertices → u ≠ v →
    (scan u v ↔ ResidualArticulation vertices neighbors u v)

/-- Assuming an exact residual-articulation scan, every true two-vertex
    separator appears in the scan (in this orientation). -/
theorem exact_scan_covers_every_pair_cut
    (vertices : List Nat) (neighbors : Nat → List Nat)
    (scan : Nat → Nat → Prop)
    (hBi : BiconnectedOn vertices neighbors)
    (hScan : ExactResidualScan vertices neighbors scan)
    (u v : Nat) (hCut : PairSeparates vertices neighbors u v) :
    scan u v := by
  have hArt :=
    (pair_separates_iff_residual_articulation
      vertices neighbors hBi u v).mp hCut
  exact (hScan u v hArt.1 hArt.2.1 hArt.2.2.1).mpr hArt.2.2.2

/-- An exact scanner never creates a spurious two-vertex graph cut. -/
theorem exact_scan_is_sound_for_pair_cut
    (vertices : List Nat) (neighbors : Nat → List Nat)
    (scan : Nat → Nat → Prop)
    (hScan : ExactResidualScan vertices neighbors scan)
    (u v : Nat)
    (hu : u ∈ vertices) (hv : v ∈ vertices)
    (hne : u ≠ v) (hEmitted : scan u v) :
    PairSeparates vertices neighbors u v := by
  have hArt : ResidualArticulation vertices neighbors u v :=
    (hScan u v hu hv hne).mp hEmitted
  exact ⟨hu, hv, hne, hArt.2⟩

#print axioms Witnora.TC063VertexCoupling.pair_separates_iff_residual_articulation
#print axioms Witnora.TC063VertexCoupling.exact_scan_covers_every_pair_cut
#print axioms Witnora.TC063VertexCoupling.exact_scan_is_sound_for_pair_cut

end Witnora.TC063VertexCoupling
