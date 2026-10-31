import Lean
import Witnora.ChromaticMinimum

/-!
# Clique extremum from bounded indexed clique certificates

A clique certificate is an injective map from Option (Fin k) to
vertices, carrying k+1 pairwise adjacent vertices. The largest size is
defined as the least common upper bound of all such certificates.

The existence of a finite upper bound remains explicit: for Fin N
graphs it will follow from a pigeonhole theorem.
-/

namespace Witnora.CliqueMaximum

open Witnora.ChromaticMinimum

def IndexedClique {N : Nat} (Adj : Fin N → Fin N → Prop)
    (k : Nat) : Prop :=
  ∃ vertices : Option (Fin k) → Fin N,
    (∀ a b, vertices a = vertices b → a = b) ∧
    (∀ a b, a ≠ b → Adj (vertices a) (vertices b))

def CliqueUpperBound {N : Nat}
    (Adj : Fin N → Fin N → Prop) (bound : Nat) : Prop :=
  ∀ k, IndexedClique Adj k → k + 1 ≤ bound

noncomputable def cliqueNumber {N : Nat}
    (Adj : Fin N → Fin N → Prop)
    (hBound : ∃ bound, CliqueUpperBound Adj bound) : Nat :=
  Classical.choose
    (least_nat_witness (CliqueUpperBound Adj) hBound)

theorem cliqueNumber_bounds_every_clique {N : Nat}
    (Adj : Fin N → Fin N → Prop)
    (hBound : ∃ bound, CliqueUpperBound Adj bound)
    (k : Nat) (vertices : Option (Fin k) → Fin N)
    (hInject : ∀ a b, vertices a = vertices b → a = b)
    (hClique : ∀ a b, a ≠ b →
      Adj (vertices a) (vertices b)) :
    k + 1 ≤ cliqueNumber Adj hBound := by
  exact (Classical.choose_spec
    (least_nat_witness (CliqueUpperBound Adj) hBound)).1
      k ⟨vertices, hInject, hClique⟩

theorem cliqueNumber_le_any_upper_bound {N : Nat}
    (Adj : Fin N → Fin N → Prop)
    (hBound : ∃ bound, CliqueUpperBound Adj bound)
    (bound : Nat) (hb : CliqueUpperBound Adj bound) :
    cliqueNumber Adj hBound ≤ bound := by
  exact (Classical.choose_spec
    (least_nat_witness (CliqueUpperBound Adj) hBound)).2 bound hb

end Witnora.CliqueMaximum
