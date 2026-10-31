import Lean
import Init.Omega
import Witnora.ColoringOptimalityCertificate

/-!
# Concrete finite-edge-list coloring optimality checker

Unlike the abstract witness theorem, this module computes a Boolean check
over a supplied finite edge list and explicit Fin-indexed color/clique maps.
The check must establish looplessness, proper coloring, clique injection,
and every pairwise adjacency in the clique.

A passing result is sound for the exact adjacency relation derived from
the provided edge list. It is not yet a parser for serialized Python arrays.
-/

namespace Witnora.ConcreteColorCertificate

open Witnora.ChromaticMinimum
open Witnora.ColoringOptimalityCertificate

/-- Undirected edge membership is derived from concrete pairs. -/
def edgeAdj {N : Nat} (edges : List (Fin N × Fin N))
    (u v : Fin N) : Prop :=
  (u, v) ∈ edges ∨ (v, u) ∈ edges

/-- Finite Boolean certificate check, with no trusted extremal parameters. -/
def checkCertificate {N k : Nat}
    (edges : List (Fin N × Fin N))
    (paint : Fin N → Fin (k + 1))
    (vertices : Option (Fin k) → Fin N) : Bool :=
  decide (
    (∀ u : Fin N, ¬ edgeAdj edges u u) ∧
    (∀ u v : Fin N, edgeAdj edges u v → paint u ≠ paint v) ∧
    (∀ a b : Option (Fin k), vertices a = vertices b → a = b) ∧
    (∀ a b : Option (Fin k), a ≠ b →
      edgeAdj edges (vertices a) (vertices b)))

/-- A successful concrete check produces a proven exact chromatic number. -/
theorem checked_certificate_sound {N k : Nat}
    (edges : List (Fin N × Fin N))
    (paint : Fin N → Fin (k + 1))
    (vertices : Option (Fin k) → Fin N)
    (hChecked : checkCertificate edges paint vertices = true) :
    ∃ hNoLoops : ∀ u : Fin N, ¬ edgeAdj edges u u,
      chromaticNumber (edgeAdj edges) hNoLoops = k + 1 := by
  have hFacts :
      (∀ u : Fin N, ¬ edgeAdj edges u u) ∧
      (∀ u v : Fin N, edgeAdj edges u v → paint u ≠ paint v) ∧
      (∀ a b : Option (Fin k), vertices a = vertices b → a = b) ∧
      (∀ a b : Option (Fin k), a ≠ b →
        edgeAdj edges (vertices a) (vertices b)) := by
    simpa [checkCertificate] using hChecked
  rcases hFacts with ⟨hNoLoops, hProper, hInject, hClique⟩
  exact ⟨hNoLoops,
    exact_chromatic_of_matching_witnesses
      N k (edgeAdj edges) hNoLoops
      paint hProper vertices hInject hClique⟩

/-- A fully concrete triangle graph, given by three undirected edges. -/
def triangleEdges : List (Fin 3 × Fin 3) :=
  [(0, 1), (0, 2), (1, 2)]

/-- Explicit three-color assignment. -/
def trianglePaint : Fin 3 → Fin 3 := fun u => u

/-- Explicit three-vertex clique enumeration. -/
def triangleClique : Option (Fin 2) → Fin 3
  | none => 0
  | some i => i.succ

/-- The data check executes, not just the abstract implication. -/
theorem triangle_certificate_passes :
    checkCertificate triangleEdges trianglePaint triangleClique = true := by
  decide

/-- An actual checked example of chromatic optimality. -/
theorem triangle_chromatic_exact :
    ∃ hNoLoops : ∀ u : Fin 3, ¬ edgeAdj triangleEdges u u,
      chromaticNumber (edgeAdj triangleEdges) hNoLoops = 3 := by
  exact checked_certificate_sound
    triangleEdges trianglePaint triangleClique triangle_certificate_passes

end Witnora.ConcreteColorCertificate

#print axioms Witnora.ConcreteColorCertificate.checked_certificate_sound
#print axioms Witnora.ConcreteColorCertificate.triangle_certificate_passes
#print axioms Witnora.ConcreteColorCertificate.triangle_chromatic_exact
