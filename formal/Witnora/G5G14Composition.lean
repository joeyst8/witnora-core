import Witnora.Separator
import Witnora.SparseBridge
import Witnora.SignedSerialization

/-!
# G5/G14 composition boundary

This theorem combines the G14 separator-coverage theorem with *closed,
checkable* G5 UNSAT certificates for one residual component of each
separator branch.

It deliberately takes three bridge contracts as explicit hypotheses:
* a model of the original CNF maps to a decomposed separator model;
* each selected residual component's model maps to its certified CNF;
* every separator branch supplies an accepted G5 certificate.

These bridge contracts are NOT proved for the Python G14 implementation
here. In particular, this is not a completed TC-063 theorem.
-/

universe u v w

namespace Witnora.G5G14Composition

open Witnora.G5Extraction

variable {S : Type u} {I : Type v} {R : I → Type w}

/-- Every original model would yield a G14 decomposition model, but a
closed G5 proof refutes a selected residual component on every branch.
No exhaustive SAT check or separate row-correctness hypothesis is used. -/
theorem original_unsat_of_checked_g5_branch_cover
    (original : Witnora.Concrete.CNF)
    (F : S → ((i : I) → R i) → Prop)
    (C : S → (i : I) → R i → Prop)
    (hdecomposes : Witnora.Separator.Decomposes F C)
    (horiginal : (∃ a, CNFHolds original a) → ∃ s b, F s b)
    (selected : S → I)
    (residualCNF : S → Witnora.Concrete.CNF)
    (toAssignment : (s : S) → R (selected s) → Nat → Bool)
    (bound : S → Nat)
    (rows : S → List Witnora.G5Trace.Row)
    (steps : S → List Witnora.G5Dag.XorRef)
    (hresidual : ∀ s x, C s (selected s) x →
      CNFHolds (residualCNF s) (toAssignment s x))
    (hcert : ∀ s, Witnora.SparseBridge.checkG5Closed
      (bound s) (residualCNF s) (rows s) (steps s) = true) :
    ¬ ∃ a, CNFHolds original a := by
  have hcover : ∀ s, ∃ i, ∀ x, ¬ C s i x := by
    intro s
    refine ⟨selected s, ?_⟩
    intro x hx
    have hunsat := Witnora.SparseBridge.checkG5Closed_unsat
      (bound s) (residualCNF s) (rows s) (steps s) (hcert s)
    exact hunsat ⟨toAssignment s x, hresidual s x hx⟩
  have hdecomposedUnsat : ¬ ∃ s b, F s b :=
    (Witnora.Separator.unsat_iff_cover F C hdecomposes).mpr hcover
  intro hsat
  exact hdecomposedUnsat (horiginal hsat)


/-- Signed-source end-to-end G14 cover soundness, still conditional on
    the explicitly supplied decomposition and residual-model bridges.
    No Python parser correctness or arbitrary-instance completeness is claimed. -/
theorem signed_source_unsat_of_checked_g5_branch_cover
    (raw : List (List Int))
    (F : S → ((i : I) → R i) → Prop)
    (C : S → (i : I) → R i → Prop)
    (hdecomposes : Witnora.Separator.Decomposes F C)
    (hsource : (∃ a, Witnora.SignedSerialization.signedCNFHolds raw a) →
      ∃ s b, F s b)
    (selected : S → I)
    (residualCNF : S → Witnora.Concrete.CNF)
    (toAssignment : (s : S) → R (selected s) → Nat → Bool)
    (bound : S → Nat)
    (rows : S → List Witnora.G5Trace.Row)
    (steps : S → List Witnora.G5Dag.XorRef)
    (hresidual : ∀ s x, C s (selected s) x →
      CNFHolds (residualCNF s) (toAssignment s x))
    (hcert : ∀ s, Witnora.SparseBridge.checkG5Closed
      (bound s) (residualCNF s) (rows s) (steps s) = true) :
    ¬ ∃ a, Witnora.SignedSerialization.signedCNFHolds raw a := by
  have hbridge : (∃ a, CNFHolds
      (Witnora.SignedSerialization.decodeCNF raw) a) → ∃ s b, F s b := by
    intro ⟨a, ha⟩
    exact hsource ⟨a,
      (Witnora.SignedSerialization.signedCNFHolds_iff raw a).mpr ha⟩
  have hun := original_unsat_of_checked_g5_branch_cover
    (Witnora.SignedSerialization.decodeCNF raw) F C hdecomposes
    hbridge selected residualCNF toAssignment bound rows steps
    hresidual hcert
  intro ⟨a, ha⟩
  exact hun ⟨a,
    (Witnora.SignedSerialization.signedCNFHolds_iff raw a).mp ha⟩

#print axioms Witnora.G5G14Composition.signed_source_unsat_of_checked_g5_branch_cover

#print axioms Witnora.G5G14Composition.original_unsat_of_checked_g5_branch_cover

end Witnora.G5G14Composition
