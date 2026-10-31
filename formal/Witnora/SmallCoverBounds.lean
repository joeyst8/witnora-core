import Lean
import Init.Omega
import Witnora.CoverMinimumBridge

/-!
# Boundary cases for small minimum vertex covers
-/

namespace Witnora.SmallCoverBounds

open Witnora.ChromaticMinimum
open Witnora.VertexCoverMinimum
open Witnora.ConcreteGraphBound
open Witnora.CliqueMaximum

theorem zero_cover_bound
    (N : Nat) (Adj : Fin N → Fin N → Prop)
    (hNoLoops : ∀ u, ¬ Adj u u)
    (hCert : CoverCertificate Adj 0) :
    chromaticNumber Adj hNoLoops ≤
      max 0 (finiteCliqueNumber N Adj) := by
  classical
  obtain ⟨S, label, hCover, hInject, hSurject⟩ := hCert
  have hEmpty : ∀ u, ¬ S u := by
    intro u hu
    have impossible := (label ⟨u, hu⟩).isLt
    omega
  have hNoEdges : ∀ u v, ¬ Adj u v := by
    intro u v huv
    rcases hCover u v huv with hu | hv
    · exact hEmpty u hu
    · exact hEmpty v hv
  cases N with
  | zero =>
    have hColor : Colorable Adj 0 := by
      refine ⟨fun u => u, ?_⟩
      intro u v huv heq
      exact hNoLoops u huv
    have hChi : chromaticNumber Adj hNoLoops ≤ 0 :=
      chromaticNumber_minimal Adj hNoLoops 0 hColor
    exact Nat.le_trans hChi (Nat.le_max_left 0 (finiteCliqueNumber 0 Adj))
  | succ n =>
    have hColor : Colorable Adj 1 := by
      refine ⟨fun _ => ⟨0, by omega⟩, ?_⟩
      intro u v huv
      exact False.elim (hNoEdges u v huv)
    have hChi : chromaticNumber Adj hNoLoops ≤ 1 :=
      chromaticNumber_minimal Adj hNoLoops 1 hColor
    let vertex : Fin (n + 1) := ⟨0, by omega⟩
    let vertices : Option (Fin 0) → Fin (n + 1) := fun _ => vertex
    have hOptionUnique : ∀ a b : Option (Fin 0), a = b := by
      intro a b
      cases a with
      | none =>
        cases b with
        | none => rfl
        | some i =>
          have hi := i.isLt
          omega
      | some i =>
        have hi := i.isLt
        omega
    have hInject : ∀ a b, vertices a = vertices b → a = b := by
      intro a b _
      exact hOptionUnique a b
    have hClique : ∀ a b, a ≠ b →
        Adj (vertices a) (vertices b) := by
      intro a b hne
      exact False.elim (hne (hOptionUnique a b))
    have hOmega : 1 ≤ finiteCliqueNumber (n + 1) Adj :=
      cliqueNumber_bounds_every_clique Adj
        (finite_cliques_bounded (n + 1) Adj)
        0 vertices hInject hClique
    exact Nat.le_trans hChi
      (Nat.le_trans hOmega (Nat.le_max_right 0 (finiteCliqueNumber (n + 1) Adj)))

end Witnora.SmallCoverBounds
