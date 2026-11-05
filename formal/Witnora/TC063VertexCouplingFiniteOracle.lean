import Witnora.G14DFSOuterScan

/-!
# Finite graph oracle for Python articulation and two-cut outputs

This executable Lean oracle computes residual connected-component counts
using the already proved finite DFS outer scan, independently of Python's
iterative low-link articulation scanner. Generated Lean examples compare
actual Python outputs against these counts and are checked by Lean.

These finite acceptance tests do not constitute a universal Python
refinement proof. The DFS model's exact reachability theorems are in
G14DFSSeenEnqueue and G14DFSOuterScan.
-/

namespace Witnora.TC063VertexCouplingFiniteOracle

open Witnora.G14DFSSeenEnqueue
open Witnora.G14DFSOuterScan

/-- Component count after deleting all listed vertices. -/
def residualComponentCount (vertices : List Nat)
    (neighbors : Nat → List Nat) (blocked : List Nat) : Nat :=
  let rest := remainingVertices vertices blocked
  ((scanComponents (separatedNeighbors neighbors blocked)
      rest.length rest [] []).2).length

/-- Semantic articulation oracle: deletion increases component count. -/
def articulationFlag (vertices : List Nat)
    (neighbors : Nat → List Nat) (v : Nat) : Bool :=
  decide (residualComponentCount vertices neighbors [v] >
    residualComponentCount vertices neighbors [])

/-- Compare claimed Python articulation vertices against every source vertex. -/
def checkArticulations (vertices : List Nat)
    (neighbors : Nat → List Nat) (claimed : List Nat) : Bool :=
  decide claimed.Nodup &&
    claimed.all (fun v => decide (v ∈ vertices)) &&
    vertices.all (fun v =>
      articulationFlag vertices neighbors v == decide (v ∈ claimed))

/-- Lexicographically ordered unordered pairs for a sorted vertex list. -/
def orderedPairs : List Nat → List (Nat × Nat)
  | [] => []
  | v :: rest => rest.map (fun w => (v, w)) ++ orderedPairs rest

/-- Two-vertex cut flag, for a connected starting graph. -/
def twoCutFlag (vertices : List Nat)
    (neighbors : Nat → List Nat) (u v : Nat) : Bool :=
  decide (residualComponentCount vertices neighbors [u, v] > 1)

/-- Independently compare every claimed Python pair with the DFS-based
    connectivity oracle. Intended for connected, articulation-free graphs. -/
def checkTwoCuts (vertices : List Nat)
    (neighbors : Nat → List Nat) (claimed : List (Nat × Nat)) : Bool :=
  let valid := orderedPairs vertices
  decide claimed.Nodup &&
    claimed.all (fun pair => decide (pair ∈ valid)) &&
    valid.all (fun pair =>
      twoCutFlag vertices neighbors pair.1 pair.2 ==
        decide (pair ∈ claimed))

def path3Neighbors (v : Nat) : List Nat :=
  match v with
  | 0 => [1]
  | 1 => [0, 2]
  | 2 => [1]
  | _ => []

example : checkArticulations [0, 1, 2] path3Neighbors [1] = true := by decide

def triangleNeighbors (v : Nat) : List Nat :=
  match v with
  | 0 => [1, 2]
  | 1 => [0, 2]
  | 2 => [0, 1]
  | _ => []

example : checkArticulations [0, 1, 2] triangleNeighbors [] = true := by decide
example : checkTwoCuts [0, 1, 2] triangleNeighbors [] = true := by decide

/-- An out-of-universe name or repeated claimed ID is rejected, even
    if all source-vertex membership comparisons would otherwise pass. -/
example : checkArticulations [0, 1, 2] triangleNeighbors [99] = false := by decide
example : checkArticulations [0, 1, 2] path3Neighbors [1, 1] = false := by decide

def cycle4Neighbors (v : Nat) : List Nat :=
  match v with
  | 0 => [1, 3]
  | 1 => [0, 2]
  | 2 => [1, 3]
  | 3 => [0, 2]
  | _ => []

example : checkTwoCuts [0, 1, 2, 3] cycle4Neighbors
    [(0, 2), (1, 3)] = true := by decide
example : checkTwoCuts [0, 1, 2, 3] cycle4Neighbors
    [(0, 2), (1, 3), (0, 2)] = false := by decide
example : checkTwoCuts [0, 1, 2, 3] cycle4Neighbors
    [(0, 2), (1, 3), (99, 100)] = false := by decide

end Witnora.TC063VertexCouplingFiniteOracle
