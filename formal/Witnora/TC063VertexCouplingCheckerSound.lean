import Witnora.TC063VertexCouplingFiniteOracle

/-!
# TC-063: sound, complete, fail-closed finite graph candidate checker

Unlike the experimental Python low-link candidate generator, this small
Lean checker treats claimed articulation vertices and two-vertex cuts as
untrusted input. It requires each claim to be in the source universe,
requires a duplicate-free claim list, and exhaustively checks every
possible source vertex or ordered pair against the independent verified
DFS component-count computation.

The theorems below give unconditional acceptance contracts relative to
that executable DFS oracle. They do NOT prove that Python always emits
accepted results, nor that arbitrary CNFs have small affine separators.
-/

namespace Witnora.TC063VertexCouplingCheckerSound

open Witnora.TC063VertexCouplingFiniteOracle

theorem checkArticulations_acceptance_iff
    (vertices : List Nat) (neighbors : Nat → List Nat)
    (claimed : List Nat) :
    checkArticulations vertices neighbors claimed = true ↔
      claimed.Nodup ∧
      (∀ v ∈ claimed, v ∈ vertices) ∧
      (∀ v ∈ vertices,
        articulationFlag vertices neighbors v = decide (v ∈ claimed)) := by
  simp [checkArticulations, List.all_eq_true]

theorem checkTwoCuts_acceptance_iff
    (vertices : List Nat) (neighbors : Nat → List Nat)
    (claimed : List (Nat × Nat)) :
    checkTwoCuts vertices neighbors claimed = true ↔
      claimed.Nodup ∧
      (∀ pair ∈ claimed, pair ∈ orderedPairs vertices) ∧
      (∀ pair ∈ orderedPairs vertices,
        twoCutFlag vertices neighbors pair.1 pair.2 =
          decide (pair ∈ claimed)) := by
  simp [checkTwoCuts, List.all_eq_true]

/-- Every emitted pair of an accepted candidate certificate really
    separates the remaining vertices into at least two DFS components. -/
theorem accepted_pair_is_genuine_cut
    (vertices : List Nat) (neighbors : Nat → List Nat)
    (claimed : List (Nat × Nat))
    (hAccept : checkTwoCuts vertices neighbors claimed = true)
    (pair : Nat × Nat) (hClaim : pair ∈ claimed) :
    residualComponentCount vertices neighbors [pair.1, pair.2] > 1 := by
  obtain ⟨_, hValid, hExact⟩ :=
    (checkTwoCuts_acceptance_iff vertices neighbors claimed).mp hAccept
  have hEq := hExact pair (hValid pair hClaim)
  have hTrue : twoCutFlag vertices neighbors pair.1 pair.2 = true := by
    simpa [hClaim] using hEq
  simpa [twoCutFlag] using hTrue

/-- The accepted list has no missing genuine two-vertex graph cuts. -/
theorem accepted_checker_covers_every_cut
    (vertices : List Nat) (neighbors : Nat → List Nat)
    (claimed : List (Nat × Nat))
    (hAccept : checkTwoCuts vertices neighbors claimed = true)
    (pair : Nat × Nat)
    (hPair : pair ∈ orderedPairs vertices)
    (hCut : residualComponentCount vertices neighbors
      [pair.1, pair.2] > 1) :
    pair ∈ claimed := by
  obtain ⟨_, _, hExact⟩ :=
    (checkTwoCuts_acceptance_iff vertices neighbors claimed).mp hAccept
  have hEq := hExact pair hPair
  have hTrue : decide (pair ∈ claimed) = true := by
    rw [← hEq]
    simp [twoCutFlag, hCut]
  exact of_decide_true hTrue

#print axioms Witnora.TC063VertexCouplingCheckerSound.checkTwoCuts_acceptance_iff
#print axioms Witnora.TC063VertexCouplingCheckerSound.accepted_pair_is_genuine_cut
#print axioms Witnora.TC063VertexCouplingCheckerSound.accepted_checker_covers_every_cut

end Witnora.TC063VertexCouplingCheckerSound
