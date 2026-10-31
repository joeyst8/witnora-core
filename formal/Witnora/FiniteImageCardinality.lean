import Lean
import Init.Omega
import Witnora.ColorMerge

/-!
# Cardinality of a finite injectively labeled type

Every injection A → Fin m can be compressed to a bijection A ↔ Fin k
for some k ≤ m. The construction removes unused labels one at a time.
-/

namespace Witnora.FiniteImageCardinality

open Witnora.ColorMerge

theorem compress_injective_labels {A : Type} :
    ∀ (m : Nat) (label : A → Fin m),
      (∀ x y, label x = label y → x = y) →
      ∃ k, k ≤ m ∧
        ∃ rank : A → Fin k,
          (∀ x y, rank x = rank y → x = y) ∧
          (∀ i : Fin k, ∃ x, rank x = i) := by
  intro m
  induction m with
  | zero =>
    intro label hinj
    refine ⟨0, Nat.le_refl 0, label, hinj, ?_⟩
    intro i
    have hi := i.isLt
    omega
  | succ n ih =>
    intro label hinj
    classical
    by_cases hMissing : ∃ p : Fin (n + 1), ∀ x : A, label x ≠ p
    · obtain ⟨p, hUnused⟩ := hMissing
      let last : Fin (n + 1) := ⟨n, by omega⟩
      let g : A → Fin (n + 1) :=
        fun x => swapFin p last (label x)
      have hSwapP : swapFin p last p = last := by
        simp [swapFin]
      have hNotLast : ∀ x, g x ≠ last := by
        intro x heq
        have hEq : swapFin p last (label x) =
            swapFin p last p := by
          simpa [g, hSwapP] using heq
        exact hUnused x
          (swapFin_injective p last (label x) p hEq)
      let smaller : A → Fin n :=
        fun x => ⟨(g x).val, by
          have hi := (g x).isLt
          have hn : (g x).val ≠ n := by
            intro hv
            apply hNotLast x
            apply Fin.ext
            exact hv
          omega⟩
      have hSmallerInject :
          ∀ x y, smaller x = smaller y → x = y := by
        intro x y heq
        have hv := congrArg Fin.val heq
        have hg : g x = g y := by
          apply Fin.ext
          exact hv
        apply hinj
        exact swapFin_injective p last (label x) (label y) hg
      obtain ⟨k, hkn, rank, hRankInject, hRankSurject⟩ :=
        ih smaller hSmallerInject
      exact ⟨k, by omega, rank, hRankInject, hRankSurject⟩
    · refine ⟨n + 1, Nat.le_refl _, label, hinj, ?_⟩
      intro i
      by_cases hExists : ∃ x, label x = i
      · exact hExists
      · have hUnused : ∀ x : A, label x ≠ i := by
          intro x heq
          exact hExists ⟨x, heq⟩
        exact False.elim (hMissing ⟨i, hUnused⟩)

end Witnora.FiniteImageCardinality
