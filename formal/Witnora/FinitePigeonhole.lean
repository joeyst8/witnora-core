import Lean
import Init.Omega
import Witnora.ColorMerge

/-!
# Finite pigeonhole principle without Mathlib

An injective map Fin m → Fin n implies m ≤ n.
-/

namespace Witnora.FinitePigeonhole

open Witnora.ColorMerge

theorem fin_injective_card_le :
    ∀ (m n : Nat) (f : Fin m → Fin n),
      (∀ a b, f a = f b → a = b) → m ≤ n := by
  intro m n
  induction n generalizing m with
  | zero =>
    intro f hf
    cases m with
    | zero => omega
    | succ m =>
      have z : Fin (m + 1) := ⟨0, by omega⟩
      have impossible := (f z).isLt
      omega
  | succ n ih =>
    cases m with
    | zero =>
      intro f hf
      omega
    | succ m =>
      intro f hf
      let sourceLast : Fin (m + 1) := ⟨m, by omega⟩
      let targetLast : Fin (n + 1) := ⟨n, by omega⟩
      let g : Fin (m + 1) → Fin (n + 1) :=
        fun i => swapFin (f sourceLast) targetLast (f i)
      have hgInject : ∀ a b, g a = g b → a = b := by
        intro a b heq
        apply hf
        exact swapFin_injective (f sourceLast) targetLast (f a) (f b) heq
      have hgLast : g sourceLast = targetLast := by
        simp [g, swapFin]
      have hNotLast : ∀ i : Fin m, g (Fin.castSucc i) ≠ targetLast := by
        intro i heq
        have hSource : Fin.castSucc i = sourceLast :=
          hgInject (Fin.castSucc i) sourceLast (by rw [hgLast]; exact heq)
        have hv := congrArg Fin.val hSource
        have hi := i.isLt
        dsimp [sourceLast] at hv
        omega
      let lower : Fin m → Fin n := fun i =>
        ⟨(g (Fin.castSucc i)).val, by
          have hi := (g (Fin.castSucc i)).isLt
          have hNotVal : (g (Fin.castSucc i)).val ≠ n := by
            intro hv
            exact hNotLast i (Fin.ext hv)
          omega⟩
      have hLowerInject : ∀ a b, lower a = lower b → a = b := by
        intro a b heq
        have hVal := congrArg Fin.val heq
        have hG : g (Fin.castSucc a) = g (Fin.castSucc b) := by
          apply Fin.ext
          exact hVal
        have hCast := hgInject (Fin.castSucc a) (Fin.castSucc b) hG
        apply Fin.ext
        have hVals := congrArg Fin.val hCast
        exact hVals
      have hSmall : m ≤ n := ih m lower hLowerInject
      omega

/-- Encode each of k+1 positions as an optional k-position. -/
def finToOption (k : Nat) (i : Fin (k + 1)) : Option (Fin k) :=
  if h : i.val = 0 then none
  else some ⟨i.val - 1, by
    have hi := i.isLt
    omega⟩

theorem finToOption_injective (k : Nat)
    (a b : Fin (k + 1))
    (h : finToOption k a = finToOption k b) : a = b := by
  by_cases ha : a.val = 0
  · by_cases hb : b.val = 0
    · apply Fin.ext
      omega
    · simp [finToOption, ha, hb] at h
  · by_cases hb : b.val = 0
    · simp [finToOption, ha, hb] at h
    · have hVals : a.val - 1 = b.val - 1 := by
        have h' := congrArg (Option.map Fin.val) h
        simpa [finToOption, ha, hb] using h'
      apply Fin.ext
      omega

/-- Every indexed clique in a graph on Fin N has at most N vertices. -/
theorem indexed_clique_size_le_vertices
    (N : Nat) (Adj : Fin N → Fin N → Prop)
    (k : Nat) (vertices : Option (Fin k) → Fin N)
    (hInject : ∀ a b, vertices a = vertices b → a = b) :
    k + 1 ≤ N := by
  let f : Fin (k + 1) → Fin N :=
    fun i => vertices (finToOption k i)
  have hf : ∀ a b, f a = f b → a = b := by
    intro a b heq
    have hOption : finToOption k a = finToOption k b :=
      hInject (finToOption k a) (finToOption k b) heq
    exact finToOption_injective k a b hOption
  exact fin_injective_card_le (k + 1) N f hf

end Witnora.FinitePigeonhole
