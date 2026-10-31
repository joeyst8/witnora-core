import Lean
import Witnora.ConcreteColorCertificate

/-!
# Numeric data adapter for finite graph coloring certificates

Inputs are ordinary Nat pairs and Nat color/clique lists. The checker
rejects invalid lengths and out-of-range entries, decodes the data to
Fin-indexed witness functions, then invokes the kernel-proved concrete
edge-list checker. The vertex and palette sizes are N+1 and K+1.

This is a checked in-memory numeric adapter, not yet a byte parser.
-/

namespace Witnora.NumericColorCertificate

open Witnora.ConcreteColorCertificate
open Witnora.ChromaticMinimum

def decodeEdge (N : Nat) (edge : Nat × Nat) :
    Option (Fin (N + 1) × Fin (N + 1)) :=
  if hu : edge.1 < N + 1 then
    if hv : edge.2 < N + 1 then
      some (⟨edge.1, hu⟩, ⟨edge.2, hv⟩)
    else none
  else none

def decodedEdges (N : Nat) (edges : List (Nat × Nat)) :
    List (Fin (N + 1) × Fin (N + 1)) :=
  edges.filterMap (decodeEdge N)

def optionIndex {K : Nat} : Option (Fin K) → Nat
  | none => 0
  | some i => i.val + 1

/-- Fin.ofNat is total; raw range checks forbid wraparound on accepted data. -/
def decodedPaint (N K : Nat) (colors : List Nat) :
    Fin (N + 1) → Fin (K + 1) :=
  fun i => Fin.ofNat (K + 1) ((colors[i.val]?).getD 0)

def decodedClique (N K : Nat) (clique : List Nat) :
    Option (Fin K) → Fin (N + 1) :=
  fun i => Fin.ofNat (N + 1) ((clique[optionIndex i]?).getD 0)

/-- Explicit length/range checks executed before any certificate acceptance. -/
def numericRangesValid (N K : Nat)
    (edges : List (Nat × Nat))
    (colors clique : List Nat) : Bool :=
  decide (colors.length = N + 1) &&
  decide (clique.length = K + 1) &&
  colors.all (fun color => decide (color < K + 1)) &&
  clique.all (fun vertex => decide (vertex < N + 1)) &&
  edges.all (fun edge =>
    decide (edge.1 < N + 1) && decide (edge.2 < N + 1))

def checkNumeric (N K : Nat)
    (edges : List (Nat × Nat))
    (colors clique : List Nat) : Bool :=
  numericRangesValid N K edges colors clique &&
  checkCertificate (decodedEdges N edges)
    (decodedPaint N K colors) (decodedClique N K clique)

/-- Any passing numeric certificate proves optimality of its decoded graph. -/
theorem checked_numeric_sound
    (N K : Nat) (edges : List (Nat × Nat))
    (colors clique : List Nat)
    (hCheck : checkNumeric N K edges colors clique = true) :
    ∃ hNoLoops : ∀ u : Fin (N + 1),
        ¬ edgeAdj (decodedEdges N edges) u u,
      chromaticNumber (edgeAdj (decodedEdges N edges)) hNoLoops = K + 1 := by
  have hParts :
      numericRangesValid N K edges colors clique = true ∧
      checkCertificate (decodedEdges N edges)
        (decodedPaint N K colors) (decodedClique N K clique) = true := by
    simpa only [checkNumeric, Bool.and_eq_true] using hCheck
  exact checked_certificate_sound
    (decodedEdges N edges)
    (decodedPaint N K colors)
    (decodedClique N K clique)
    hParts.2

def triangleNumericEdges : List (Nat × Nat) :=
  [(0, 1), (0, 2), (1, 2)]
def triangleNumericColors : List Nat := [0, 1, 2]
def triangleNumericClique : List Nat := [0, 1, 2]

theorem numeric_triangle_passes :
    checkNumeric 2 2 triangleNumericEdges
      triangleNumericColors triangleNumericClique = true := by
  decide

theorem numeric_triangle_optimal :
    ∃ hNoLoops : ∀ u : Fin 3,
        ¬ edgeAdj (decodedEdges 2 triangleNumericEdges) u u,
      chromaticNumber (edgeAdj (decodedEdges 2 triangleNumericEdges))
        hNoLoops = 3 := by
  exact checked_numeric_sound 2 2 triangleNumericEdges
    triangleNumericColors triangleNumericClique numeric_triangle_passes

theorem out_of_range_edge_rejected :
    checkNumeric 2 2 ((0, 3) :: triangleNumericEdges)
      triangleNumericColors triangleNumericClique = false := by
  decide

theorem out_of_range_color_rejected :
    checkNumeric 2 2 triangleNumericEdges
      [0, 1, 3] triangleNumericClique = false := by
  decide

theorem missing_clique_entry_rejected :
    checkNumeric 2 2 triangleNumericEdges
      triangleNumericColors [0, 1] = false := by
  decide

theorem repeated_clique_vertex_rejected :
    checkNumeric 2 2 triangleNumericEdges
      triangleNumericColors [0, 0, 2] = false := by
  decide

end Witnora.NumericColorCertificate

#print axioms Witnora.NumericColorCertificate.checked_numeric_sound
#print axioms Witnora.NumericColorCertificate.numeric_triangle_passes
#print axioms Witnora.NumericColorCertificate.numeric_triangle_optimal
#print axioms Witnora.NumericColorCertificate.out_of_range_edge_rejected
#print axioms Witnora.NumericColorCertificate.out_of_range_color_rejected
#print axioms Witnora.NumericColorCertificate.missing_clique_entry_rejected
#print axioms Witnora.NumericColorCertificate.repeated_clique_vertex_rejected
