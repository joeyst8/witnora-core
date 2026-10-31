import Lean
import Witnora.ChromaticMinimum

/-!
# Minimum vertex cover for finite graphs

An exact k-vertex cover is certified by a predicate S and a bijective
labeling of the subtype of covered vertices with Fin k. This handles
empty covers without requiring a function from all graph vertices to Fin 0.
-/

namespace Witnora.VertexCoverMinimum

open Witnora.ChromaticMinimum

def IsVertexCover {N : Nat} (Adj : Fin N → Fin N → Prop)
    (S : Fin N → Prop) : Prop :=
  ∀ u v, Adj u v → S u ∨ S v

def CoverCertificate {N : Nat} (Adj : Fin N → Fin N → Prop)
    (k : Nat) : Prop :=
  ∃ S : Fin N → Prop,
    ∃ label : {u : Fin N // S u} → Fin k,
      IsVertexCover Adj S ∧
      (∀ u v, label u = label v → u = v) ∧
      (∀ i : Fin k, ∃ u, label u = i)

theorem cover_certificate_exists {N : Nat}
    (Adj : Fin N → Fin N → Prop) :
    ∃ k, CoverCertificate Adj k := by
  refine ⟨N, ?_⟩
  refine ⟨fun _ => True, fun u => u.val, ?_, ?_, ?_⟩
  · intro u v huv
    exact Or.inl True.intro
  · intro u v heq
    apply Subtype.ext
    exact heq
  · intro i
    exact ⟨⟨i, True.intro⟩, rfl⟩

noncomputable def vertexCoverNumber {N : Nat}
    (Adj : Fin N → Fin N → Prop) : Nat :=
  Classical.choose
    (least_nat_witness (CoverCertificate Adj)
      (cover_certificate_exists Adj))

theorem vertexCoverNumber_certificate {N : Nat}
    (Adj : Fin N → Fin N → Prop) :
    CoverCertificate Adj (vertexCoverNumber Adj) := by
  exact (Classical.choose_spec
    (least_nat_witness (CoverCertificate Adj)
      (cover_certificate_exists Adj))).1

theorem vertexCoverNumber_minimal {N : Nat}
    (Adj : Fin N → Fin N → Prop)
    (k : Nat) (hCover : CoverCertificate Adj k) :
    vertexCoverNumber Adj ≤ k := by
  exact (Classical.choose_spec
    (least_nat_witness (CoverCertificate Adj)
      (cover_certificate_exists Adj))).2 k hCover

end Witnora.VertexCoverMinimum
