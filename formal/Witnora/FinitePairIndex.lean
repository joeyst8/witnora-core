import Lean
import Init.Omega

/-!
# Injective indexing of finite ordered vertex pairs

A pair (u,v) in Fin N × Fin N is represented by the bounded natural
number u*N+v. This is injective because quotient and remainder by N
recover the original coordinates.
-/

namespace Witnora.FinitePairIndex

def pairIndex (N : Nat) (p : Fin N × Fin N) : Fin (N * N) :=
  ⟨p.1.val * N + p.2.val, by
    have ha := p.1.isLt
    have hb := p.2.isLt
    have hMul : (p.1.val + 1) * N ≤ N * N :=
      Nat.mul_le_mul_right N (by omega)
    have hLt : p.1.val * N + p.2.val < (p.1.val + 1) * N := by
      simp [Nat.succ_mul]
      omega
    exact Nat.lt_of_lt_of_le hLt hMul⟩

theorem pairIndex_injective (N : Nat)
    (a b : Fin N × Fin N)
    (heq : pairIndex N a = pairIndex N b) : a = b := by
  have hv := congrArg Fin.val heq
  have hN : 0 < N := Nat.lt_of_le_of_lt (Nat.zero_le a.1.val) a.1.isLt
  have hModA : (a.1.val * N + a.2.val) % N = a.2.val := by
    rw [Nat.mul_add_mod_self_right]
    exact Nat.mod_eq_of_lt a.2.isLt
  have hModB : (b.1.val * N + b.2.val) % N = b.2.val := by
    rw [Nat.mul_add_mod_self_right]
    exact Nat.mod_eq_of_lt b.2.isLt
  have hDivA : (a.1.val * N + a.2.val) / N = a.1.val := by
    rw [Nat.add_comm]
    rw [Nat.add_mul_div_right _ _ hN]
    simp [Nat.div_eq_of_lt a.2.isLt]
  have hDivB : (b.1.val * N + b.2.val) / N = b.1.val := by
    rw [Nat.add_comm]
    rw [Nat.add_mul_div_right _ _ hN]
    simp [Nat.div_eq_of_lt b.2.isLt]
  have hFirst : a.1.val = b.1.val := by
    have hd := congrArg (fun x : Nat => x / N) hv
    simpa [pairIndex, hDivA, hDivB] using hd
  have hSecond : a.2.val = b.2.val := by
    have hm := congrArg (fun x : Nat => x % N) hv
    simpa [pairIndex, hModA, hModB] using hm
  apply Prod.ext
  · apply Fin.ext
    exact hFirst
  · apply Fin.ext
    exact hSecond

end Witnora.FinitePairIndex
