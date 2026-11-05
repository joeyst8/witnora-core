import Witnora.TC063CanonicalBound

/-!
# Bound-independent sparse G5 source-CNF contradiction checker

The old checkG5Closed validates canonical support by recursively scanning
every numeric ID less than the supplied bound.  That is not efficient in
the bit-length of sparse, high-numbered input variable names.

This new checker needs only source-bound CNF-to-XOR extraction evidence,
duplicate-free initial sparse supports, and an accepted indexed DAG
contradiction.  Its *proof* chooses a finite max-ID bound to reuse the
verified sparseParity/DAG semantics; the *executable checker* has no bound
parameter and never invokes canonicalSupport, sparseParity or xorFold.
-/

namespace Witnora.TC063SparseDirectChecker

open Witnora.Concrete
open Witnora.G5Trace
open Witnora.G5Dag
open Witnora.G5Extraction
open Witnora.SparseBridge
open Witnora.SparseParity
open Witnora.Extraction
open Witnora.TC063CanonicalBound
open Witnora.TC063CanonicalAffineBridge
open Witnora.SemanticSAF

/-- Certificate verifier whose work depends on row/certificate structure,
    not on the numerical maximum variable ID. -/
def checkSparseG5
    (cnf : CNF) (rows : List Row) (steps : List XorRef) : Bool :=
  rows.all (fun row => decide row.coefficients.Nodup) &&
    checkInitialRows cnf rows &&
    checkDagContradiction rows steps

/-- Any duplicate-free, bounded list has exactly the same sparse-parity
    and XOR-list-parity semantics, no sorting scan required. -/
theorem sparseParity_eq_parityVars_of_nodup_bounded
    (bound : Nat) (coeff : List Nat)
    (hNodup : coeff.Nodup)
    (hBound : ∀ v ∈ coeff, v < bound)
    (a : Nat → Bool) :
    sparseParity bound coeff a = parityVars coeff a := by
  calc
    sparseParity bound coeff a =
        parityVars (canonicalSupport bound coeff) a :=
      sparseParity_canonicalSupport bound coeff a
    _ = parityVars coeff a :=
      parityVars_perm
        (canonicalSupport_perm_of_bounded bound coeff hNodup hBound) a

/-- A source-bound sparse checker result is UNSAT-sound for all variable
    IDs, with no runtime numeric-bound enumeration. -/
theorem checkSparseG5_unsat
    (cnf : CNF) (rows : List Row) (steps : List XorRef)
    (h : checkSparseG5 cnf rows steps = true) :
    ¬ ∃ a : Nat → Bool, CNFHolds cnf a := by
  have hp := h
  simp [checkSparseG5] at hp
  have hNo : ∀ row ∈ rows, row.coefficients.Nodup := hp.1.1
  have hExtraction : checkInitialRows cnf rows = true := hp.1.2
  have hDag : checkDagContradiction rows steps = true := hp.2
  have hBridge :
      ∀ row ∈ rows, ∀ a : Nat → Bool,
        sparseParity (boundForRows rows) row.coefficients a =
          parityVars row.coefficients a := by
    intro row hr a
    exact sparseParity_eq_parityVars_of_nodup_bounded
      (boundForRows rows) row.coefficients
      (hNo row hr) (rows_bounded_boundForRows rows row hr) a
  have hG5 : Witnora.G5Verified.checkG5 cnf rows steps = true := by
    simp [Witnora.G5Verified.checkG5, hExtraction, hDag]
  exact Witnora.G5Verified.checkG5_unsat_of_sparse_bridge
    (boundForRows rows) cnf rows steps hBridge hG5

/-- Any accepted original bound-dependent closed certificate is also
    accepted by the new bound-independent sparse checker. -/
theorem closedG5_implies_sparseG5
    (bound : Nat) (cnf : CNF) (rows : List Row)
    (steps : List XorRef)
    (hClosed : checkG5Closed bound cnf rows steps = true) :
    checkSparseG5 cnf rows steps = true := by
  have hp := hClosed
  simp [checkG5Closed] at hp
  have hInitial : checkInitialRows cnf rows = true := hp.1.1
  have hCanonical : checkCanonicalRows bound rows = true := hp.1.2
  have hDag : checkDagContradiction rows steps = true := hp.2
  have hNo : rows.all (fun row => decide row.coefficients.Nodup) = true := by
    apply List.all_eq_true.mpr
    intro row hr
    have hc := List.all_eq_true.mp hCanonical row hr
    have heq : row.coefficients =
        canonicalSupport bound row.coefficients := by
      simpa [checkCanonicalRow, checkCanonicalRows] using hc
    have hn : row.coefficients.Nodup := by
      rw [heq]
      exact canonicalSupport_nodup bound row.coefficients
    simpa using hn
  simp [checkSparseG5, hNo, hInitial, hDag]

/-- Restricted-family affine UNSAT completeness transfers to the fast
    certificate-only checker without a max-variable bound input. -/
theorem certifiedAffine_unsat_has_sparseG5
    (r : Nat) (cnf : CNF)
    (hCertified : CertifiedAffine r cnf)
    (hUnsat : ¬ ∃ a : Nat → Bool, CNFHolds cnf a) :
    ∃ (rows : List Row) (steps : List XorRef),
      checkSparseG5 cnf rows steps = true := by
  obtain ⟨bound, rows, steps, hClosed⟩ :=
    canonical_affine_unsat_has_g5_certificate
      r cnf (certifiedAffine_has_canonicalWitness r cnf hCertified) hUnsat
  exact ⟨rows, steps,
    closedG5_implies_sparseG5 bound cnf rows steps hClosed⟩

/-- An adversarial high variable ID: the checker does not scan [0, 1048576).
    The certificate contains only two source rows and one XOR reference. -/
example :
    checkSparseG5
      [[(1048576, true)], [(1048576, false)]]
      [⟨[1048576], true⟩, ⟨[1048576], false⟩]
      [(0, 1)] = true := by decide

#print axioms Witnora.TC063SparseDirectChecker.checkSparseG5_unsat
#print axioms Witnora.TC063SparseDirectChecker.closedG5_implies_sparseG5
#print axioms Witnora.TC063SparseDirectChecker.certifiedAffine_unsat_has_sparseG5

end Witnora.TC063SparseDirectChecker
