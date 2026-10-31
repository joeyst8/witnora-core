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

end Witnora.FinitePigeonhole
