import Witnora.ParityCompression

/-!
# Residual CNF under root-offset substitution

Every literal is rewritten to its component root, flipping its polarity
when the variable's parity offset is true. This is an exact semantic
rewriting for arbitrary clauses, including empty clauses. Clause
simplification/deduplication may occur subsequently via a separate
verified canonicalization step.
-/

namespace Witnora.ParityResidual

open Witnora.Concrete
open Witnora.FiniteXor
open Witnora.G5Extraction
open Witnora.ParityCompression

def substituteLiteral (rootOf : Nat → Nat) (offset : Nat → Bool)
    (lit : Literal) : Literal :=
  (rootOf lit.1, lit.2 != offset lit.1)

def substituteCNF (rootOf : Nat → Nat) (offset : Nat → Bool)
    (cnf : CNF) : CNF :=
  cnf.map (fun clause => clause.map (substituteLiteral rootOf offset))

theorem substitute_literal_semantics (rootOf : Nat → Nat)
    (offset : Nat → Bool) (roots : Nat → Bool) (lit : Literal) :
    signedLitTrue (reconstruct rootOf offset roots) lit =
      signedLitTrue roots (substituteLiteral rootOf offset lit) := by
  rcases lit with ⟨v, polarity⟩
  cases hp : polarity <;>
    cases ho : offset v <;>
    cases hr : roots (rootOf v) <;>
    simp [signedLitTrue, reconstruct, substituteLiteral, hp, ho, hr]

/-- Substituting every signed literal is exact for all CNF assignments. -/
theorem residual_semantics (rootOf : Nat → Nat)
    (offset : Nat → Bool) (roots : Nat → Bool) (cnf : CNF) :
    CNFHolds cnf (reconstruct rootOf offset roots) ↔
      CNFHolds (substituteCNF rootOf offset cnf) roots := by
  simp [CNFHolds, substituteCNF, List.all_map, List.any_map,
    substitute_literal_semantics]

/-- Checked source paths plus a literal-wise residual rewrite give an exact
SAT correspondence between the original CNF and compressed residual. -/
theorem source_iff_rewritten_residual
    (cnf : CNF) (rootOf : Nat → Nat) (offset : Nat → Bool)
    (paths : Nat → List (Nat × Bool))
    (hpaths : ValidSourcePaths cnf rootOf offset paths) :
    (∃ a, CNFHolds cnf a) ↔
    (∃ roots, CNFHolds (substituteCNF rootOf offset cnf) roots) := by
  rw [source_iff_root_residual cnf rootOf offset paths hpaths]
  constructor
  · rintro ⟨roots, h⟩
    exact ⟨roots, (residual_semantics rootOf offset roots cnf).mp h⟩
  · rintro ⟨roots, h⟩
    exact ⟨roots, (residual_semantics rootOf offset roots cnf).mpr h⟩

#print axioms Witnora.ParityResidual.residual_semantics
#print axioms Witnora.ParityResidual.source_iff_rewritten_residual

end Witnora.ParityResidual
