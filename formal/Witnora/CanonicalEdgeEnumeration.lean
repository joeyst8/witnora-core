import Lean
import Init.Omega
import Witnora.FinitePairIndex
import Witnora.FiniteImageCardinality
import Witnora.EdgeEndpointCover

/-!
# A canonical certificate for every finite simple graph

Canonical undirected edges are adjacent pairs (u,v) with u < v.
Their finite pair indices are injective; compressing those indices
gives a bijective enumeration with no duplicates.
-/

namespace Witnora.CanonicalEdgeEnumeration

open Witnora.FinitePairIndex
open Witnora.FiniteImageCardinality
open Witnora.EdgeEndpointCover

def CanonicalEdge (N : Nat) (Adj : Fin N → Fin N → Prop) :=
  {p : Fin N × Fin N // p.1.val < p.2.val ∧ Adj p.1 p.2}

noncomputable def canonical_edge_enumeration
    (N : Nat) (Adj : Fin N → Fin N → Prop)
    (hSym : ∀ u v, Adj u v → Adj v u)
    (hNoLoops : ∀ u, ¬ Adj u u) :
    Σ m, EdgeEnumeration N m Adj := by
  classical
  let encode : CanonicalEdge N Adj → Fin (N * N) :=
    fun p => pairIndex N p.val
  have hEncode : ∀ a b, encode a = encode b → a = b := by
    intro a b heq
    apply Subtype.ext
    exact pairIndex_injective N a.val b.val heq
  have hCompressed :=
    compress_injective_labels (N * N) encode hEncode
  let m := Classical.choose hCompressed
  have hm := Classical.choose_spec hCompressed
  let rank := Classical.choose hm.2
  have hRankInject := (Classical.choose_spec hm.2).1
  have hRankSurject := (Classical.choose_spec hm.2).2
  let rep : Fin m → CanonicalEdge N Adj :=
    fun i => Classical.choose (hRankSurject i)
  have hRep : ∀ i, rank (rep i) = i := by
    intro i
    exact Classical.choose_spec (hRankSurject i)
  have hRound : ∀ p : CanonicalEdge N Adj, rep (rank p) = p := by
    intro p
    exact hRankInject (rep (rank p)) p (hRep (rank p))
  let edge : Fin m → Fin N × Fin N := fun i => (rep i).val
  have hOrder : ∀ i, (edge i).1.val < (edge i).2.val := by
    intro i
    exact (rep i).property.1
  have hSound : ∀ i, Adj (edge i).1 (edge i).2 := by
    intro i
    exact (rep i).property.2
  have hComplete : ∀ u v, Adj u v →
      ∃ i, SameUndirectedEdge (edge i) (u, v) := by
    intro u v huv
    have hDifferent : u ≠ v := by
      intro heq
      subst v
      exact hNoLoops u huv
    by_cases huvLt : u.val < v.val
    · let p : CanonicalEdge N Adj := ⟨(u, v), huvLt, huv⟩
      refine ⟨rank p, Or.inl ?_⟩
      change (rep (rank p)).val = (u, v)
      rw [hRound]
    · have hvuLt : v.val < u.val := by
        have hu := u.isLt
        have hv := v.isLt
        have hValNe : u.val ≠ v.val := by
          intro heq
          exact hDifferent (Fin.ext heq)
        omega
      let p : CanonicalEdge N Adj := ⟨(v, u), hvuLt, hSym u v huv⟩
      refine ⟨rank p, Or.inr ?_⟩
      change (rep (rank p)).val = (v, u)
      rw [hRound]
  have hUnique : ∀ i j, SameUndirectedEdge (edge i) (edge j) →
      i = j := by
    intro i j h
    rcases h with hDirect | hReverse
    · have hRepEq : rep i = rep j := Subtype.ext hDirect
      calc
        i = rank (rep i) := (hRep i).symm
        _ = rank (rep j) := congrArg rank hRepEq
        _ = j := hRep j
    · have hi := hOrder i
      have hj := hOrder j
      have hFirst : (edge i).1 = (edge j).2 :=
        congrArg Prod.fst hReverse
      have hSecond : (edge i).2 = (edge j).1 :=
        congrArg Prod.snd hReverse
      have hFirstVal := congrArg Fin.val hFirst
      have hSecondVal := congrArg Fin.val hSecond
      omega
  exact ⟨m, ⟨edge, hSound, hComplete, hUnique⟩⟩

end Witnora.CanonicalEdgeEnumeration
