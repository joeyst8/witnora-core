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

/-- A clique cover together with one outside vertex adjacent to every
cover vertex forms a larger clique. -/
theorem clique_extension
    {V : Type} (Adj : V → V → Prop) (S : V → Prop) (outside : V)
    (hSym : ∀ u v, Adj u v → Adj v u)
    (hCoverClique :
      ∀ u v, S u → S v → u ≠ v → Adj u v)
    (hOutside : ¬ S outside)
    (hAllNeighbors : ∀ u, S u → Adj outside u) :
    ∀ u v, (S u ∨ u = outside) → (S v ∨ v = outside) →
      u ≠ v → Adj u v := by
  intro u v hu hv hne
  rcases hu with hsu | hue
  · rcases hv with hsv | hve
    · exact hCoverClique u v hsu hsv hne
    · subst v
      exact hSym outside u (hAllNeighbors u hsu)
  · rcases hv with hsv | hve
    · subst u
      exact hAllNeighbors v hsv
    · exact False.elim (hne (hue.trans hve.symm))

/-- A cover labeled injectively by k colors gives a proper coloring
with Option (Fin k), i.e. one additional distinguished color. -/
theorem colorable_with_cover_plus_one
    {V : Type} (Adj : V → V → Prop) (S : V → Prop) (k : Nat)
    (label : V → Fin k)
    (hNoLoops : ∀ u, ¬ Adj u u)
    (hIndependent : ∀ u v, ¬ S u → ¬ S v → ¬ Adj u v)
    (hInjectOnCover :
      ∀ u v, S u → S v → label u = label v → u = v) :
    ∃ paint : V → Option (Fin k),
      ∀ u v, Adj u v → paint u ≠ paint v := by
  classical
  let paint : V → Option (Fin k) :=
    fun u => if S u then some (label u) else none
  refine ⟨paint, ?_⟩
  intro u v huv
  by_cases hu : S u
  · by_cases hv : S v
    · have hDistinct : label u ≠ label v := by
        intro heq
        have hVertex := hInjectOnCover u v hu hv heq
        subst v
        exact hNoLoops u huv
      simpa [paint, hu, hv] using hDistinct
    · simp [paint, hu, hv]
  · by_cases hv : S v
    · simp [paint, hu, hv]
    · exact False.elim ((hIndependent u v hu hv) huv)

/-- A recoloring whose only collisions are a chosen nonadjacent cover
pair remains proper on the cover. This is the local color-merging step. -/
theorem merge_nonadjacent_cover_pair
    {V : Type} (Adj : V → V → Prop) (S : V → Prop)
    (merged : V → Nat) (x y : V)
    (hSym : ∀ u v, Adj u v → Adj v u)
    (hNoLoops : ∀ u, ¬ Adj u u)
    (hNoPairEdge : ¬ Adj x y)
    (hCollisions :
      ∀ u v, S u → S v → merged u = merged v →
        u = v ∨ (u = x ∧ v = y) ∨ (u = y ∧ v = x)) :
    ∀ u v, S u → S v → Adj u v → merged u ≠ merged v := by
  intro u v hu hv huv heq
  rcases hCollisions u v hu hv heq with hSame | hPair | hReverse
  · subst v
    exact hNoLoops u huv
  · rcases hPair with ⟨hux, hvy⟩
    subst u
    subst v
    exact hNoPairEdge huv
  · rcases hReverse with ⟨huy, hvx⟩
    subst u
    subst v
    exact hNoPairEdge (hSym y x huv)

/-- A clique vertex cover labeled injectively by k colors yields a
dichotomy: either the graph is k-colorable, or the cover extends to a
larger clique by one outside vertex. -/
theorem clique_cover_color_or_extend
    {V : Type} (Adj : V → V → Prop) (S : V → Prop)
    (k : Nat) (label : V → Fin k)
    (hSym : ∀ u v, Adj u v → Adj v u)
    (hNoLoops : ∀ u, ¬ Adj u u)
    (hIndependent : ∀ u v, ¬ S u → ¬ S v → ¬ Adj u v)
    (hInjectOnCover :
      ∀ u v, S u → S v → label u = label v → u = v)
    (hCoverClique :
      ∀ u v, S u → S v → u ≠ v → Adj u v) :
    (∃ paint : V → Fin k,
      ∀ u v, Adj u v → paint u ≠ paint v) ∨
    (∃ outside : V, ¬ S outside ∧
      ∀ u v, (S u ∨ u = outside) → (S v ∨ v = outside) →
        u ≠ v → Adj u v) := by
  classical
  by_cases hUniversal :
      ∃ outside, ¬ S outside ∧ ∀ u, S u → Adj outside u
  · right
    obtain ⟨outside, hOutside, hAll⟩ := hUniversal
    exact ⟨outside, hOutside,
      clique_extension Adj S outside hSym hCoverClique hOutside hAll⟩
  · left
    have hWitness : ∀ u, ¬ S u → ∃ v, S v ∧ ¬ Adj u v := by
      intro u hu
      by_cases hExists : ∃ v, S v ∧ ¬ Adj u v
      · exact hExists
      · have hAll : ∀ v, S v → Adj u v := by
          intro v hv
          by_cases hEdge : Adj u v
          · exact hEdge
          · exact False.elim (hExists ⟨v, hv, hEdge⟩)
        exact False.elim (hUniversal ⟨u, hu, hAll⟩)
    let pick : V → V :=
      fun u => if h : ¬ S u then Classical.choose (hWitness u h) else u
    have hPickInside : ∀ u, ¬ S u → S (pick u) := by
      intro u hu
      simpa [pick, hu] using (Classical.choose_spec (hWitness u hu)).1
    have hPickNonneighbor : ∀ u, ¬ S u → ¬ Adj u (pick u) := by
      intro u hu
      simpa [pick, hu] using (Classical.choose_spec (hWitness u hu)).2
    let paint : V → Fin k :=
      fun u => if S u then label u else label (pick u)
    refine ⟨paint, ?_⟩
    intro u v huv
    by_cases hu : S u
    · by_cases hv : S v
      · have hVertex : u ≠ v := by
          intro heq
          subst v
          exact hNoLoops u huv
        have hDistinct : label u ≠ label v := by
          intro heq
          exact hVertex (hInjectOnCover u v hu hv heq)
        simpa [paint, hu, hv] using hDistinct
      · intro heq
        have hEq : label u = label (pick v) := by
          simpa [paint, hu, hv] using heq
        have hVertex : u = pick v :=
          hInjectOnCover u (pick v) hu (hPickInside v hv) hEq
        have hEdge : Adj v (pick v) := by
          simpa [hVertex] using hSym u v huv
        exact (hPickNonneighbor v hv) hEdge
    · by_cases hv : S v
      · intro heq
        have hEq : label (pick u) = label v := by
          simpa [paint, hu, hv] using heq
        have hVertex : pick u = v :=
          hInjectOnCover (pick u) v (hPickInside u hu) hv hEq
        have hEdge : Adj u (pick u) := by
          simpa [hVertex] using huv
        exact (hPickNonneighbor u hu) hEdge
      · exact False.elim ((hIndependent u v hu hv) huv)

end Witnora.GraphCoverColoring
