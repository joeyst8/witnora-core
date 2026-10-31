import Lean
import Init.Omega
import Witnora.ColoringOptimalityCertificate

/-!
# Executable certificate checker over enumerated finite graph data

All conditions are checked by Boolean iteration over explicit finite
lists; no noncomputable classical Prop-decision oracle is used.
-/

namespace Witnora.ConcreteColorCertificate

open Witnora.ChromaticMinimum
open Witnora.ColoringOptimalityCertificate

def edgeBool {N : Nat} (edges : List (Fin N × Fin N))
    (u v : Fin N) : Bool :=
  edges.contains (u, v) || edges.contains (v, u)

def edgeAdj {N : Nat} (edges : List (Fin N × Fin N))
    (u v : Fin N) : Prop :=
  edgeBool edges u v = true

def optionIndices (k : Nat) : List (Option (Fin k)) :=
  none :: (List.finRange k).map some

def allFin (n : Nat) (p : Fin n → Bool) : Bool :=
  (List.finRange n).all p

def allOptionFin (k : Nat) (p : Option (Fin k) → Bool) : Bool :=
  (optionIndices k).all p

private theorem allFin_sound (n : Nat) (p : Fin n → Bool)
    (h : allFin n p = true) (x : Fin n) : p x = true := by
  exact (List.all_eq_true.mp h) x (List.mem_finRange x)

private theorem allOptionFin_sound (k : Nat)
    (p : Option (Fin k) → Bool)
    (h : allOptionFin k p = true)
    (x : Option (Fin k)) : p x = true := by
  apply (List.all_eq_true.mp h) x
  cases x with
  | none => simp [optionIndices]
  | some i =>
      simp only [optionIndices, List.mem_cons, List.mem_map]
      right
      exact ⟨i, List.mem_finRange i, rfl⟩

/-- Every finite input condition is checked by concrete Boolean loops. -/
def checkCertificate {N k : Nat}
    (edges : List (Fin N × Fin N))
    (paint : Fin N → Fin (k + 1))
    (vertices : Option (Fin k) → Fin N) : Bool :=
  allFin N (fun u => decide (¬ edgeAdj edges u u)) &&
  allFin N (fun u =>
    allFin N (fun v =>
      decide (edgeAdj edges u v → paint u ≠ paint v))) &&
  allOptionFin k (fun a =>
    allOptionFin k (fun b =>
      decide (vertices a = vertices b → a = b))) &&
  allOptionFin k (fun a =>
    allOptionFin k (fun b =>
      decide (a ≠ b → edgeAdj edges (vertices a) (vertices b))))

theorem checked_certificate_sound {N k : Nat}
    (edges : List (Fin N × Fin N))
    (paint : Fin N → Fin (k + 1))
    (vertices : Option (Fin k) → Fin N)
    (hChecked : checkCertificate edges paint vertices = true) :
    ∃ hNoLoops : ∀ u : Fin N, ¬ edgeAdj edges u u,
      chromaticNumber (edgeAdj edges) hNoLoops = k + 1 := by
  have hParts :
      allFin N (fun u => decide (¬ edgeAdj edges u u)) = true ∧
      allFin N (fun u =>
        allFin N (fun v =>
          decide (edgeAdj edges u v → paint u ≠ paint v))) = true ∧
      allOptionFin k (fun a =>
        allOptionFin k (fun b =>
          decide (vertices a = vertices b → a = b))) = true ∧
      allOptionFin k (fun a =>
        allOptionFin k (fun b =>
          decide (a ≠ b → edgeAdj edges (vertices a) (vertices b)))) = true := by
    simpa only [checkCertificate, Bool.and_eq_true] using hChecked
  rcases hParts with ⟨hLoops, hProperCheck, hInjectCheck, hCliqueCheck⟩
  have hNoLoops : ∀ u : Fin N, ¬ edgeAdj edges u u := by
    intro u
    exact of_decide_true (allFin_sound N _ hLoops u)
  have hProper : ∀ u v : Fin N,
      edgeAdj edges u v → paint u ≠ paint v := by
    intro u v
    have hu := allFin_sound N _ hProperCheck u
    exact of_decide_true (allFin_sound N _ hu v)
  have hInject : ∀ a b : Option (Fin k),
      vertices a = vertices b → a = b := by
    intro a b
    have ha := allOptionFin_sound k _ hInjectCheck a
    exact of_decide_true (allOptionFin_sound k _ ha b)
  have hClique : ∀ a b : Option (Fin k),
      a ≠ b → edgeAdj edges (vertices a) (vertices b) := by
    intro a b
    have ha := allOptionFin_sound k _ hCliqueCheck a
    exact of_decide_true (allOptionFin_sound k _ ha b)
  exact ⟨hNoLoops,
    exact_chromatic_of_matching_witnesses
      N k (edgeAdj edges) hNoLoops paint hProper
      vertices hInject hClique⟩

def triangleEdges : List (Fin 3 × Fin 3) :=
  [(0, 1), (0, 2), (1, 2)]

def trianglePaint : Fin 3 → Fin 3 := fun u => u

def triangleClique : Option (Fin 2) → Fin 3
  | none => 0
  | some i => i.succ

theorem triangle_certificate_passes :
    checkCertificate triangleEdges trianglePaint triangleClique = true := by
  decide

theorem triangle_chromatic_exact :
    ∃ hNoLoops : ∀ u : Fin 3, ¬ edgeAdj triangleEdges u u,
      chromaticNumber (edgeAdj triangleEdges) hNoLoops = 3 := by
  exact checked_certificate_sound
    triangleEdges trianglePaint triangleClique triangle_certificate_passes

end Witnora.ConcreteColorCertificate

#print axioms Witnora.ConcreteColorCertificate.checked_certificate_sound
#print axioms Witnora.ConcreteColorCertificate.triangle_certificate_passes
#print axioms Witnora.ConcreteColorCertificate.triangle_chromatic_exact
