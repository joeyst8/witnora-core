import Lean
import Init.Omega
import Witnora.ColoringOptimalityCertificate

/-!
# Executable finite-edge-list coloring optimality certificate

All graph conditions are checked by structurally recursive Boolean
enumeration over Fin N and Option (Fin k), not classical Prop decisions.
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

/-- Total Boolean quantifier over Fin n. -/
def allFin : (n : Nat) → (Fin n → Bool) → Bool
  | 0, _ => true
  | n + 1, p => p 0 && allFin n (fun i => p i.succ)

private theorem allFin_sound :
    ∀ n (p : Fin n → Bool),
      allFin n p = true → ∀ x : Fin n, p x = true := by
  intro n
  induction n with
  | zero =>
      intro p h x
      exact x.elim0
  | succ n ih =>
      intro p h x
      have hParts :
          p 0 = true ∧ allFin n (fun i => p i.succ) = true := by
        simpa only [allFin, Bool.and_eq_true] using h
      refine Fin.cases ?_ ?_ x
      · exact hParts.1
      · intro i
        exact ih (fun i => p i.succ) hParts.2 i

def allOptionFin (k : Nat) (p : Option (Fin k) → Bool) : Bool :=
  p none && allFin k (fun i => p (some i))

private theorem allOptionFin_sound (k : Nat)
    (p : Option (Fin k) → Bool)
    (h : allOptionFin k p = true)
    (x : Option (Fin k)) : p x = true := by
  have hParts :
      p none = true ∧ allFin k (fun i => p (some i)) = true := by
    simpa only [allOptionFin, Bool.and_eq_true] using h
  cases x with
  | none => exact hParts.1
  | some i => exact allFin_sound k _ hParts.2 i

/-- Four complete finite checks for a proposed coloring and clique. -/
def checkCertificate {N k : Nat}
    (edges : List (Fin N × Fin N))
    (paint : Fin N → Fin (k + 1))
    (vertices : Option (Fin k) → Fin N) : Bool :=
  allFin N (fun u => decide (edgeBool edges u u = false)) &&
  allFin N (fun u =>
    allFin N (fun v =>
      decide (edgeBool edges u v = true → paint u ≠ paint v))) &&
  allOptionFin k (fun a =>
    allOptionFin k (fun b =>
      decide (vertices a = vertices b → a = b))) &&
  allOptionFin k (fun a =>
    allOptionFin k (fun b =>
      decide (a ≠ b → edgeBool edges (vertices a) (vertices b) = true)))

theorem checked_certificate_sound {N k : Nat}
    (edges : List (Fin N × Fin N))
    (paint : Fin N → Fin (k + 1))
    (vertices : Option (Fin k) → Fin N)
    (hChecked : checkCertificate edges paint vertices = true) :
    ∃ hNoLoops : ∀ u : Fin N, ¬ edgeAdj edges u u,
      chromaticNumber (edgeAdj edges) hNoLoops = k + 1 := by
  have hParts :
      ((allFin N (fun u => decide (edgeBool edges u u = false)) = true ∧
      allFin N (fun u =>
        allFin N (fun v =>
          decide (edgeBool edges u v = true → paint u ≠ paint v))) = true) ∧
      allOptionFin k (fun a =>
        allOptionFin k (fun b =>
          decide (vertices a = vertices b → a = b))) = true) ∧
      allOptionFin k (fun a =>
        allOptionFin k (fun b =>
          decide (a ≠ b →
            edgeBool edges (vertices a) (vertices b) = true))) = true := by
    simpa only [checkCertificate, Bool.and_eq_true] using hChecked
  rcases hParts with ⟨⟨⟨hLoops, hProperCheck⟩, hInjectCheck⟩, hCliqueCheck⟩
  have hNoLoops : ∀ u : Fin N, ¬ edgeAdj edges u u := by
    intro u hAdj
    have hFalse : edgeBool edges u u = false :=
      of_decide_eq_true (allFin_sound N _ hLoops u)
    simp [edgeAdj, hFalse] at hAdj
  have hProper : ∀ u v : Fin N,
      edgeAdj edges u v → paint u ≠ paint v := by
    intro u v hAdj
    have hu := allFin_sound N _ hProperCheck u
    have hv := allFin_sound N _ hu v
    exact (of_decide_eq_true hv) hAdj
  have hInject : ∀ a b : Option (Fin k),
      vertices a = vertices b → a = b := by
    intro a b
    have ha := allOptionFin_sound k _ hInjectCheck a
    exact of_decide_eq_true (allOptionFin_sound k _ ha b)
  have hClique : ∀ a b : Option (Fin k),
      a ≠ b → edgeAdj edges (vertices a) (vertices b) := by
    intro a b
    change a ≠ b → edgeBool edges (vertices a) (vertices b) = true
    have ha := allOptionFin_sound k _ hCliqueCheck a
    exact of_decide_eq_true (allOptionFin_sound k _ ha b)
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
