import Lean
import Init.Omega

/-!
# Constructive finite palette compression

Collapse palette labels 0 and 1 into one label, shift all labels 2+
down by one, and prove this is the *only* new collision. This is a
concrete finite-map step toward the chromatic maximum bound.
-/

namespace Witnora.ColorMerge

def collapseFirstTwo (n : Nat) (i : Fin (n + 2)) : Fin (n + 1) :=
  ⟨if i.val = 0 then 0 else i.val - 1, by
    have hi := i.isLt
    split_ifs <;> omega⟩

theorem collapseFirstTwo_collision (n : Nat)
    (a b : Fin (n + 2))
    (h : collapseFirstTwo n a = collapseFirstTwo n b) :
    a = b ∨
      (a.val = 0 ∧ b.val = 1) ∨
      (a.val = 1 ∧ b.val = 0) := by
  have ha := a.isLt
  have hb := b.isLt
  have hval := congrArg Fin.val h
  change (if a.val = 0 then 0 else a.val - 1) =
    (if b.val = 0 then 0 else b.val - 1) at hval
  by_cases ha0 : a.val = 0
  · by_cases hb0 : b.val = 0
    · left
      apply Fin.ext
      omega
    · right
      left
      constructor
      · exact ha0
      · simp [ha0, hb0] at hval
        omega
  · by_cases hb0 : b.val = 0
    · right
      right
      constructor
      · simp [ha0, hb0] at hval
        omega
      · exact hb0
    · left
      apply Fin.ext
      simp [ha0, hb0] at hval
      omega

end Witnora.ColorMerge
