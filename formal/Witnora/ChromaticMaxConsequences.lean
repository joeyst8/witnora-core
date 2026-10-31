import Lean

/-!
# Arithmetic consequences of a chromatic bound

This file kernel-checks the two maximum equalities from the hypotheses
`omega <= chi` and `chi <= max tau omega`. The graph-theoretic derivation
of that latter main bound is NOT formalized here. Neither hypothesis is
introduced as an axiom: both are explicit parameters of the theorems.
No `sorry`, unsafe code, or unproved declarations are used.
-/

namespace Witnora.ChromaticMaxConsequences

theorem max_cover_chromatic
    (tau omega chi : Nat)
    (hClique : omega ≤ chi)
    (hCoverBound : chi ≤ max tau omega) :
    max tau omega = max tau chi := by
  apply Nat.le_antisymm
  · apply Nat.max_le.mpr
    · exact le_max_left tau chi
    · exact Nat.le_trans hClique (le_max_right tau chi)
  · apply Nat.max_le.mpr
    · exact le_max_left tau omega
    · exact hCoverBound

theorem max_edges_chromatic
    (edges tau omega chi : Nat)
    (hCoverEdges : tau ≤ edges)
    (hClique : omega ≤ chi)
    (hCoverBound : chi ≤ max tau omega) :
    max edges omega = max edges chi := by
  have hLift : max tau omega ≤ max edges omega := by
    apply Nat.max_le.mpr
    · exact Nat.le_trans hCoverEdges (le_max_left edges omega)
    · exact le_max_right edges omega
  have hBound : chi ≤ max edges omega :=
    Nat.le_trans hCoverBound hLift
  exact max_cover_chromatic edges omega chi hClique hBound

end Witnora.ChromaticMaxConsequences
