import Witnora.TC063VertexCouplingCheckerSound
import Witnora.CNFSorted

/-!
# Source-CNF-bound two-vertex-cut checker for TC-063

The claimed graph is no longer supplied by Python: source vertices and
primal adjacency are reconstructed from the actual Lean CNF clauses by
the already proved G14 primal-edge definitions. Source vertices are
deduplicated and numerically sorted before pair enumeration, matching
the mathematical variable universe of Python's normalized CNF.

A separate signed-clause wrapper rejects zero literals before decoding.
This binds each accepted pair to the exact provided signed CNF payload,
but not yet to the bytes of an original DIMACS document or a CPython
serialization/refinement theorem.
-/

namespace Witnora.TC063SourceVertexCuts

open Witnora.Concrete
open Witnora.G14DFSSeenEnqueue
open Witnora.TC063VertexCouplingFiniteOracle
open Witnora.TC063VertexCouplingCheckerSound

/-- Deterministic duplicate-free numerical source-variable enumeration. -/
def canonicalSourceVertices (source : CNF) : List Nat :=
  Witnora.CNFSorted.sortBy (fun a b : Nat => decide (a ≤ b))
    (Witnora.CNFCanonical.dedup (sourceVertices source))

theorem mem_canonicalSourceVertices_iff (source : CNF) (v : Nat) :
    v ∈ canonicalSourceVertices source ↔ v ∈ sourceVertices source := by
  unfold canonicalSourceVertices
  rw [Witnora.CNFSorted.mem_sortBy, Witnora.CNFCanonical.mem_dedup]

/-- Every primal neighbor is reconstructed from the source CNF itself. -/
def checkSourceTwoCuts (source : CNF)
    (claimed : List (Nat × Nat)) : Bool :=
  checkTwoCuts (canonicalSourceVertices source)
    (clauseNeighbors source) claimed

/-- Signed clause payload validity; literal zero is not a source variable. -/
def validSignedCNF (raw : List (List Int)) : Bool :=
  raw.all (fun clause => clause.all Witnora.SignedSerialization.validSigned)

/-- The actual signed-source certificate gate. -/
def checkSignedTwoCuts (raw : List (List Int))
    (claimed : List (Nat × Nat)) : Bool :=
  validSignedCNF raw &&
    checkSourceTwoCuts (Witnora.SignedSerialization.decodeCNF raw) claimed

/-- Accepted signed-source certificates guarantee all signed literals
    were nonzero and every claimed pair is a real cut in the exact
    source-derived primal adjacency, under the verified G14 DFS count. -/
theorem checked_signed_pair_is_source_cut
    (raw : List (List Int)) (claimed : List (Nat × Nat))
    (hAccepted : checkSignedTwoCuts raw claimed = true)
    (pair : Nat × Nat) (hClaimed : pair ∈ claimed) :
    residualComponentCount
      (canonicalSourceVertices (Witnora.SignedSerialization.decodeCNF raw))
      (clauseNeighbors (Witnora.SignedSerialization.decodeCNF raw))
      [pair.1, pair.2] > 1 := by
  have hParts :
      validSignedCNF raw = true ∧
      checkSourceTwoCuts (Witnora.SignedSerialization.decodeCNF raw)
        claimed = true := by
    simpa [checkSignedTwoCuts, Bool.and_eq_true] using hAccepted
  exact accepted_pair_is_genuine_cut
    (canonicalSourceVertices (Witnora.SignedSerialization.decodeCNF raw))
    (clauseNeighbors (Witnora.SignedSerialization.decodeCNF raw))
    claimed hParts.2 pair hClaimed

/-- A signed-source certificate accepts exactly the genuine two-vertex cuts:
    every claimed pair is well formed, no pair is repeated, and no real
    cut of the source-derived primal graph can be omitted.  The scope is
    the finite DFS component-count specification, not SAT completeness. -/
theorem checked_signed_source_exact_cuts
    (raw : List (List Int)) (claimed : List (Nat × Nat))
    (hAccepted : checkSignedTwoCuts raw claimed = true) :
    claimed.Nodup ∧
    (∀ pair ∈ claimed,
      pair ∈ orderedPairs
        (canonicalSourceVertices (Witnora.SignedSerialization.decodeCNF raw))) ∧
    (∀ pair ∈ orderedPairs
        (canonicalSourceVertices (Witnora.SignedSerialization.decodeCNF raw)),
      residualComponentCount
        (canonicalSourceVertices (Witnora.SignedSerialization.decodeCNF raw))
        (clauseNeighbors (Witnora.SignedSerialization.decodeCNF raw))
        [pair.1, pair.2] > 1 ↔ pair ∈ claimed) := by
  have hParts :
      validSignedCNF raw = true ∧
      checkSourceTwoCuts (Witnora.SignedSerialization.decodeCNF raw)
        claimed = true := by
    simpa [checkSignedTwoCuts, Bool.and_eq_true] using hAccepted
  have hCore :=
    (checkTwoCuts_acceptance_iff
      (canonicalSourceVertices (Witnora.SignedSerialization.decodeCNF raw))
      (clauseNeighbors (Witnora.SignedSerialization.decodeCNF raw))
      claimed).mp hParts.2
  refine ⟨hCore.1, hCore.2.1, ?_⟩
  intro pair hPair
  constructor
  · intro hCut
    exact accepted_checker_covers_every_cut
      (canonicalSourceVertices (Witnora.SignedSerialization.decodeCNF raw))
      (clauseNeighbors (Witnora.SignedSerialization.decodeCNF raw))
      claimed hParts.2 pair hPair hCut
  · intro hClaimed
    exact checked_signed_pair_is_source_cut raw claimed hAccepted pair hClaimed

/-- Exact signed source edge witness uses the existing G14 theorem. -/
theorem signed_source_primal_adjacency_iff
    (raw : List (List Int)) (u v : Nat) :
    v ∈ clauseNeighbors (Witnora.SignedSerialization.decodeCNF raw) u ↔
      Witnora.G14PrimalEdgeOwnership.SourceEdge
        (Witnora.SignedSerialization.decodeCNF raw) u v ∧ v ≠ u := by
  exact mem_clauseNeighbors_iff
    (Witnora.SignedSerialization.decodeCNF raw) u v

example : checkSignedTwoCuts
    [[1, 2], [2, 3], [3, 4], [1, 4]]
    [(1, 3), (2, 4)] = true := by decide
example : checkSignedTwoCuts
    [[1, 2], [2, 3], [3, 4], [1, 4]]
    [(1, 3)] = false := by decide
example : checkSignedTwoCuts
    [[1, 2], [2, 3], [3, 4], [1, 4]]
    [(1, 3), (2, 4), (99, 100)] = false := by decide
example : checkSignedTwoCuts
    [[0, 1], [1, 2]] [] = false := by decide

#print axioms Witnora.TC063SourceVertexCuts.mem_canonicalSourceVertices_iff
#print axioms Witnora.TC063SourceVertexCuts.checked_signed_pair_is_source_cut
#print axioms Witnora.TC063SourceVertexCuts.checked_signed_source_exact_cuts
#print axioms Witnora.TC063SourceVertexCuts.signed_source_primal_adjacency_iff

end Witnora.TC063SourceVertexCuts
