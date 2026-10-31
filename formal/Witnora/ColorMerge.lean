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

/-- Swap two labels, leaving all other labels unchanged. -/
def swapFin {k : Nat} (a b z : Fin k) : Fin k :=
  if z = a then b else if z = b then a else z

theorem swapFin_involutive {k : Nat} (a b z : Fin k) :
    swapFin a b (swapFin a b z) = z := by
  by_cases hab : a = b
  · subst b
    by_cases hza : z = a
    · simp [swapFin, hza]
    · simp [swapFin, hza]
  · by_cases hza : z = a
    · subst z
      simp [swapFin, hab, Ne.symm hab]
    · by_cases hzb : z = b
      · subst z
        simp [swapFin, hab, Ne.symm hab]
      · simp [swapFin, hza, hzb]

theorem swapFin_injective {k : Nat} (a b : Fin k) :
    ∀ x y, swapFin a b x = swapFin a b y → x = y := by
  intro x y h
  have h' := congrArg (swapFin a b) h
  simpa [swapFin_involutive] using h'

/-- Any two distinct palette labels can be moved to positions 0 and 1
by an injective relabeling. -/
theorem normalize_pair (n : Nat) (a b : Fin (n + 2)) (hab : a ≠ b) :
    ∃ relabel : Fin (n + 2) → Fin (n + 2),
      (∀ x y, relabel x = relabel y → x = y) ∧
      (relabel a).val = 0 ∧
      (relabel b).val = 1 := by
  let zero : Fin (n + 2) := ⟨0, by omega⟩
  let one : Fin (n + 2) := ⟨1, by omega⟩
  let first := swapFin a zero
  let b' := first b
  have hFirstA : first a = zero := by
    simp [first, swapFin]
  have hBNotZero : b' ≠ zero := by
    intro hb'
    have hEq : first b = first a := by
      simpa [b', hFirstA] using hb'
    exact hab ((swapFin_injective a zero) hEq).symm
  let second := swapFin b' one
  let relabel := fun z => second (first z)
  have hSecondZero : second zero = zero := by
    have hZeroNotOne : zero ≠ one := by
      intro h
      have hv := congrArg Fin.val h
      dsimp [zero, one] at hv
      omega
    simp [second, swapFin, Ne.symm hBNotZero, hZeroNotOne]
  refine ⟨relabel, ?_, ?_, ?_⟩
  · intro x y heq
    exact (swapFin_injective a zero)
      ((swapFin_injective b' one) heq)
  · change (second (first a)).val = 0
    rw [hFirstA, hSecondZero]
    rfl
  · change (second b').val = 1
    change one.val = 1
    rfl

end Witnora.ColorMerge
