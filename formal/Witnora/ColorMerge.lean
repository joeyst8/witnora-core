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
    by_cases hz : i.val = 0
    · simp [hz]
    · simp [hz]
      omega⟩

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

/-- If cover vertices have distinct labels, and the two vertices
labeled 0 and 1 are nonadjacent, the entire graph is colorable with
one fewer color than the elementary cover-plus-one construction. -/
theorem colorable_after_merging_nonedge
    {V : Type} (Adj : V → V → Prop) (S : V → Prop)
    (n : Nat) (label : V → Fin (n + 2)) (x y : V)
    (hSym : ∀ u v, Adj u v → Adj v u)
    (hNoLoops : ∀ u, ¬ Adj u u)
    (hIndependent : ∀ u v, ¬ S u → ¬ S v → ¬ Adj u v)
    (hInjectOnCover :
      ∀ u v, S u → S v → label u = label v → u = v)
    (hx : S x) (hy : S y)
    (hZero : (label x).val = 0)
    (hOne : (label y).val = 1)
    (hNoPairEdge : ¬ Adj x y) :
    ∃ paint : V → Option (Fin (n + 1)),
      ∀ u v, Adj u v → paint u ≠ paint v := by
  classical
  let compressed : V → Fin (n + 1) :=
    fun u => collapseFirstTwo n (label u)
  have hProperCover :
      ∀ u v, S u → S v → Adj u v → compressed u ≠ compressed v := by
    intro u v hu hv huv heq
    have hCollision :=
      collapseFirstTwo_collision n (label u) (label v) heq
    rcases hCollision with hSame | hForward | hReverse
    · have hVertex := hInjectOnCover u v hu hv hSame
      subst v
      exact hNoLoops u huv
    · rcases hForward with ⟨huZero, hvOne⟩
      have hlu : label u = label x := by
        apply Fin.ext
        omega
      have hlv : label v = label y := by
        apply Fin.ext
        omega
      have hux := hInjectOnCover u x hu hx hlu
      have hvy := hInjectOnCover v y hv hy hlv
      subst u
      subst v
      exact hNoPairEdge huv
    · rcases hReverse with ⟨huOne, hvZero⟩
      have hlu : label u = label y := by
        apply Fin.ext
        omega
      have hlv : label v = label x := by
        apply Fin.ext
        omega
      have huy := hInjectOnCover u y hu hy hlu
      have hvx := hInjectOnCover v x hv hx hlv
      subst u
      subst v
      exact hNoPairEdge (hSym y x huv)
  let paint : V → Option (Fin (n + 1)) :=
    fun u => if S u then some (compressed u) else none
  refine ⟨paint, ?_⟩
  intro u v huv
  by_cases hu : S u
  · by_cases hv : S v
    · simpa [paint, hu, hv] using hProperCover u v hu hv huv
    · simp [paint, hu, hv]
  · by_cases hv : S v
    · simp [paint, hu, hv]
    · exact False.elim ((hIndependent u v hu hv) huv)

end Witnora.ColorMerge
