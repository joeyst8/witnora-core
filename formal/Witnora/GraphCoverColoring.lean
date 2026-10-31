import Lean

/-!
# Constructive graph-coloring lemmas

A graph is represented by an adjacency relation. The set S is a vertex
cover precisely when its complement is independent. These lemmas certify
the coloring-extension step used in the chromatic maximum-bound argument.

This is a structural step, NOT yet a proof of the full cardinal inequality.
-/

namespace Witnora.GraphCoverColoring

theorem color_independent_complement
    {V : Type} (Adj : V → V → Prop) (S : V → Prop)
    (color : V → Nat) (fresh : Nat)
    (hIndependent : ∀ u v, ¬ S u → ¬ S v → ¬ Adj u v)
    (hProperOnCover :
      ∀ u v, S u → S v → Adj u v → color u ≠ color v)
    (hFresh : ∀ u, S u → color u ≠ fresh) :
    ∃ extended : V → Nat,
      (∀ u, S u → extended u = color u) ∧
      (∀ u, ¬ S u → extended u = fresh) ∧
      (∀ u v, Adj u v → extended u ≠ extended v) := by
  classical
  let extended : V → Nat := fun u => if S u then color u else fresh
  refine ⟨extended, ?_, ?_, ?_⟩
  · intro u hu
    simp [extended, hu]
  · intro u hu
    simp [extended, hu]
  · intro u v huv
    by_cases hu : S u
    · by_cases hv : S v
      · simpa [extended, hu, hv] using hProperOnCover u v hu hv huv
      · simpa [extended, hu, hv] using hFresh u hu
    · by_cases hv : S v
      · intro heq
        have h : fresh = color v := by
          simpa [extended, hu, hv] using heq
        exact (hFresh v hv) h.symm
      · exact False.elim ((hIndependent u v hu hv) huv)

/-- If every vertex outside the cover can reuse the unique color of a
non-neighbor inside it, no fresh color is necessary. -/
theorem reuse_cover_colors
    {V : Type} (Adj : V → V → Prop) (S : V → Prop)
    (color : V → Nat) (pick : V → V)
    (hSym : ∀ u v, Adj u v → Adj v u)
    (hIndependent : ∀ u v, ¬ S u → ¬ S v → ¬ Adj u v)
    (hProperOnCover :
      ∀ u v, S u → S v → Adj u v → color u ≠ color v)
    (hUniqueOnCover :
      ∀ u v, S u → S v → color u = color v → u = v)
    (hPickInside : ∀ u, ¬ S u → S (pick u))
    (hPickNonneighbor : ∀ u, ¬ S u → ¬ Adj u (pick u)) :
    ∃ extended : V → Nat,
      (∀ u, S u → extended u = color u) ∧
      (∀ u v, Adj u v → extended u ≠ extended v) := by
  classical
  let extended : V → Nat :=
    fun u => if S u then color u else color (pick u)
  refine ⟨extended, ?_, ?_⟩
  · intro u hu
    simp [extended, hu]
  · intro u v huv
    by_cases hu : S u
    · by_cases hv : S v
      · simpa [extended, hu, hv] using hProperOnCover u v hu hv huv
      · intro heq
        have hEq : color u = color (pick v) := by
          simpa [extended, hu, hv] using heq
        have hVertex : u = pick v :=
          hUniqueOnCover u (pick v) hu (hPickInside v hv) hEq
        have hEdge : Adj v (pick v) := by
          simpa [hVertex] using hSym u v huv
        exact (hPickNonneighbor v hv) hEdge
    · by_cases hv : S v
      · intro heq
        have hEq : color (pick u) = color v := by
          simpa [extended, hu, hv] using heq
        have hVertex : pick u = v :=
          hUniqueOnCover (pick u) v (hPickInside u hu) hv hEq
        have hEdge : Adj u (pick u) := by
          simpa [hVertex] using huv
        exact (hPickNonneighbor u hu) hEdge
      · exact False.elim ((hIndependent u v hu hv) huv)

end Witnora.GraphCoverColoring
