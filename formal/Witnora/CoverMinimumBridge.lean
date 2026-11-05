import Lean
import Init.Omega
import Witnora.ConcreteGraphBound
import Witnora.VertexCoverMinimum

/-!
# From exact vertex-cover certificates to the numerical graph bound

This removes the externally supplied cover size for all minimum covers
of size at least 2. The 0 and 1 cases are treated separately.
-/

namespace Witnora.CoverMinimumBridge

open Witnora.ConcreteGraphBound
open Witnora.ChromaticMinimum
open Witnora.VertexCoverMinimum

theorem graph_bound_from_cover_certificate
    (N k : Nat) (Adj : Fin N → Fin N → Prop)
    (hSym : ∀ u v, Adj u v → Adj v u)
    (hNoLoops : ∀ u, ¬ Adj u u)
    (hCertificate : CoverCertificate Adj k)
    (hk : 2 ≤ k) :
    chromaticNumber Adj hNoLoops ≤ max k (finiteCliqueNumber N Adj) := by
  classical
  obtain ⟨n, rfl⟩ : ∃ n, k = n + 2 := ⟨k - 2, by omega⟩
  obtain ⟨S, label, hCover, hInject, hSurject⟩ := hCertificate
  let totalLabel : Fin N → Fin (n + 2) :=
    fun u => if h : S u then label ⟨u, h⟩ else ⟨0, by omega⟩
  have hIndependent :
      ∀ u v, ¬ S u → ¬ S v → ¬ Adj u v := by
    intro u v hu hv hedge
    rcases hCover u v hedge with hSu | hSv
    · exact hu hSu
    · exact hv hSv
  have hTotalInject :
      ∀ u v, S u → S v → totalLabel u = totalLabel v → u = v := by
    intro u v hu hv heq
    have hEq : label ⟨u, hu⟩ = label ⟨v, hv⟩ := by
      simpa only [totalLabel, dif_pos hu, dif_pos hv] using heq
    have hSub := hInject ⟨u, hu⟩ ⟨v, hv⟩ hEq
    exact congrArg Subtype.val hSub
  have hTotalSurject :
      ∀ i : Fin (n + 2), ∃ u, S u ∧ totalLabel u = i := by
    intro i
    obtain ⟨u, hu⟩ := hSurject i
    refine ⟨u.val, u.property, ?_⟩
    simpa [totalLabel, u.property] using hu
  exact finite_graph_chromatic_max_bound
    N n Adj S totalLabel hSym hNoLoops
    hIndependent hTotalInject hTotalSurject

theorem graph_bound_if_min_cover_at_least_two
    (N : Nat) (Adj : Fin N → Fin N → Prop)
    (hSym : ∀ u v, Adj u v → Adj v u)
    (hNoLoops : ∀ u, ¬ Adj u u)
    (hCoverLarge : 2 ≤ vertexCoverNumber Adj) :
    chromaticNumber Adj hNoLoops ≤
      max (vertexCoverNumber Adj) (finiteCliqueNumber N Adj) := by
  exact graph_bound_from_cover_certificate
    N (vertexCoverNumber Adj) Adj hSym hNoLoops
      (vertexCoverNumber_certificate Adj) hCoverLarge

end Witnora.CoverMinimumBridge
