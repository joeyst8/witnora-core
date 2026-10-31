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
      exact hNoEdges u v huv
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

theorem one_cover_bound
    (N : Nat) (Adj : Fin N → Fin N → Prop)
    (hSym : ∀ u v, Adj u v → Adj v u)
    (hNoLoops : ∀ u, ¬ Adj u u)
    (hCert : CoverCertificate Adj 1) :
    chromaticNumber Adj hNoLoops ≤
      max 1 (finiteCliqueNumber N Adj) := by
  classical
  obtain ⟨S, label, hCover, hInject, hSurject⟩ := hCert
  have hUniqueCover : ∀ u v, S u → S v → u = v := by
    intro u v hu hv
    have hEq : label ⟨u, hu⟩ = label ⟨v, hv⟩ := by
      apply Fin.ext
      have huVal := (label ⟨u, hu⟩).isLt
      have hvVal := (label ⟨v, hv⟩).isLt
      omega
    exact congrArg Subtype.val (hInject ⟨u, hu⟩ ⟨v, hv⟩ hEq)
  have hIndependent :
      ∀ u v, ¬ S u → ¬ S v → ¬ Adj u v := by
    intro u v hu hv hedge
    rcases hCover u v hedge with hSu | hSv
    · exact hu hSu
    · exact hv hSv
  let total : Fin N → Fin 1 := fun _ => ⟨0, by omega⟩
  have hTotalInject :
      ∀ u v, S u → S v → total u = total v → u = v := by
    intro u v hu hv heq
    exact hUniqueCover u v hu hv
  have hCoverClique :
      ∀ u v, S u → S v → u ≠ v → Adj u v := by
    intro u v hu hv hne
    exact False.elim (hne (hUniqueCover u v hu hv))
  obtain ⟨extra, hExtraProper⟩ :=
    Witnora.GraphCoverColoring.colorable_with_cover_plus_one
      Adj S 1 total hNoLoops hIndependent hTotalInject
  have hChi2 : chromaticNumber Adj hNoLoops ≤ 2 := by
    apply chromaticNumber_minimal Adj hNoLoops 2
    refine ⟨fun u => Witnora.CoverDichotomy.optionToFin 0 (extra u), ?_⟩
    intro u v huv heq
    exact hExtraProper u v huv
      (Witnora.CoverDichotomy.optionToFin_injective 0
        (extra u) (extra v) heq)
  rcases Witnora.GraphCoverColoring.clique_cover_color_or_extend
      Adj S 1 total hSym hNoLoops hIndependent
      hTotalInject hCoverClique with
    ⟨paint, hPaint⟩ | ⟨outside, hOutside, hExtendedClique⟩
  · have hChi1 : chromaticNumber Adj hNoLoops ≤ 1 :=
      chromaticNumber_minimal Adj hNoLoops 1 ⟨paint, hPaint⟩
    exact Nat.le_trans hChi1
      (Nat.le_max_left 1 (finiteCliqueNumber N Adj))
  · obtain ⟨covered, hCovered, hLabelCovered⟩ :=
      hSurject (⟨0, by omega⟩ : Fin 1)
    let rep : Fin N := covered.val
    have hRepInside : S rep := covered.property
    let vertices : Option (Fin 1) → Fin N
      | none => outside
      | some _ => rep
    have hInject : ∀ a b, vertices a = vertices b → a = b := by
      intro a b heq
      cases a with
      | none =>
        cases b with
        | none => rfl
        | some j =>
          have hEq : outside = rep := heq
          have hInside : S outside := by
            rw [hEq]
            exact hRepInside
          exact False.elim (hOutside hInside)
      | some i =>
        cases b with
        | none =>
          have hEq : rep = outside := heq
          have hInside : S outside := by
            rw [← hEq]
            exact hRepInside
          exact False.elim (hOutside hInside)
        | some j =>
          have hij : i = j := by
            apply Fin.ext
            have hi := i.isLt
            have hj := j.isLt
            omega
          exact congrArg Option.some hij
    have hClique : ∀ a b, a ≠ b →
        Adj (vertices a) (vertices b) := by
      intro a b hne
      have ha : S (vertices a) ∨ vertices a = outside := by
        cases a with
        | none => exact Or.inr rfl
        | some i => exact Or.inl hRepInside
      have hb : S (vertices b) ∨ vertices b = outside := by
        cases b with
        | none => exact Or.inr rfl
        | some i => exact Or.inl hRepInside
      have hDistinct : vertices a ≠ vertices b := by
        intro heq
        exact hne (hInject a b heq)
      exact hExtendedClique (vertices a) (vertices b) ha hb hDistinct
    have hOmega2 : 2 ≤ finiteCliqueNumber N Adj :=
      cliqueNumber_bounds_every_clique Adj
        (finite_cliques_bounded N Adj)
        1 vertices hInject hClique
    exact Nat.le_trans hChi2
      (Nat.le_trans hOmega2
        (Nat.le_max_right 1 (finiteCliqueNumber N Adj)))

end Witnora.SmallCoverBounds
