import Witnora.TC063CompletenessReduction
import Witnora.G5ExecutableTotality

/-!
# TC-063 certified affine component to executable closed G5 certificate

For an UNSAT component with a semantically exact extracted affine row
system, canonical sparse support, and an in-range complete variable
schedule, the already-proved total G5 indexed emitter produces a checked
DAG contradiction.  The unchanged source-bound checkG5Closed accepts
that trace.  No preexisting trace, final contradiction, or scheduler
success is assumed.

The only remaining family-level bridge is constructing an equivalent
canonical sparse-row witness from every CertifiedAffine component.
-/

namespace Witnora.TC063CanonicalAffineBridge

open Witnora.Concrete
open Witnora.G5Trace
open Witnora.G5Extraction
open Witnora.G5Certificate
open Witnora.G5InitialSupportCoverage
open Witnora.G5IndexedOperationEmitter
open Witnora.SparseBridge
open Witnora.ExactAffineMembership
open Witnora.SemanticSAF
open Witnora.TC063CompletenessReduction
open Witnora.TC063Direct

/-- A source-CNF checker-accepted exact affine representation, plus
    canonical sparse row support and a complete bounded pivot schedule. -/
def CanonicalAffineWitness (r : Nat) (cnf : CNF) : Prop :=
  ∃ (bound : Nat) (rows : List Row) (variables : List Nat),
    checkSemanticExactAffine r cnf rows = true ∧
    checkCanonicalRows bound rows = true ∧
    Covered variables rows ∧
    (∀ v ∈ variables, v < bound)

/-- The CNF-to-sparse model bridge follows from existing semantic-affine
    extraction correctness and the canonical-support parity theorem. -/
theorem semantic_affine_iff_sparse_rows_of_canonical
    (r : Nat) (cnf : CNF) (rows : List Row) (bound : Nat)
    (hSemantic : checkSemanticExactAffine r cnf rows = true)
    (hCanonical : checkCanonicalRows bound rows = true)
    (a : Nat → Bool) :
    CNFHolds cnf a ↔
      ∀ row ∈ rows, RowHolds bound row a := by
  rw [checkSemanticExactAffine_sound r cnf rows hSemantic a]
  constructor
  · intro hParity row hr
    have hEq := checkCanonicalRows_sound bound rows
      hCanonical row hr a
    change Witnora.SparseParity.sparseParity bound row.coefficients a =
      row.rhs
    exact hEq.trans (hParity row hr)
  · intro hRows row hr
    have hEq := checkCanonicalRows_sound bound rows
      hCanonical row hr a
    have hSparse :
        Witnora.SparseParity.sparseParity bound row.coefficients a =
          row.rhs := hRows row hr
    exact hEq.symm.trans hSparse

/-- All existential outputs are derived: a successful indexed G5 run,
    its accepted DAG, and the actual closed source-CNF checker result. -/
theorem unsat_exact_affine_has_closed_g5_certificate
    (r : Nat) (cnf : CNF) (rows : List Row)
    (bound : Nat) (variables : List Nat)
    (hSemantic : checkSemanticExactAffine r cnf rows = true)
    (hCanonical : checkCanonicalRows bound rows = true)
    (hCoverage : Covered variables rows)
    (hInRange : ∀ v ∈ variables, v < bound)
    (hUnsat : ¬ ∃ a : Nat → Bool, CNFHolds cnf a) :
    ∃ steps : List Witnora.G5Dag.XorRef,
      checkG5Closed bound cnf rows steps = true := by
  have hExtraction :
      ∀ a : Nat → Bool,
        CNFHolds cnf a ↔
          ∀ row ∈ rows, RowHolds bound row a := by
    intro a
    exact semantic_affine_iff_sparse_rows_of_canonical
      r cnf rows bound hSemantic hCanonical a
  obtain ⟨outcome, _, hAccepted⟩ :=
    Witnora.G5ExecutableTotality.cnf_unsat_has_checked_certificate_of_equivalence
      rows bound variables (fun a => CNFHolds cnf a)
      hCoverage hInRange hExtraction hUnsat
  obtain ⟨result, _, hDag⟩ :=
    accepts_has_checked_dag rows outcome.operations hAccepted
  have hInitial : checkInitialRows cnf rows = true := by
    unfold checkSemanticExactAffine at hSemantic
    simp at hSemantic
    exact hSemantic.1.2
  refine ⟨result.dag.steps, ?_⟩
  simp [checkG5Closed, hInitial, hCanonical, hDag]

/-- Every UNSAT canonical affine component admits a checker-accepted
    closed G5 certificate, without an existential execution assumption. -/
theorem canonical_affine_unsat_has_g5_certificate
    (r : Nat) (cnf : CNF)
    (hCanonical : CanonicalAffineWitness r cnf)
    (hUnsat : ¬ ∃ a : Nat → Bool, CNFHolds cnf a) :
    ∃ (bound : Nat) (rows : List Row)
      (steps : List Witnora.G5Dag.XorRef),
        checkG5Closed bound cnf rows steps = true := by
  obtain ⟨bound, rows, variables, hSemantic, hRows, hCover, hRange⟩ :=
    hCanonical
  obtain ⟨steps, hCert⟩ :=
    unsat_exact_affine_has_closed_g5_certificate
      r cnf rows bound variables
      hSemantic hRows hCover hRange hUnsat
  exact ⟨bound, rows, steps, hCert⟩

/-- The remaining family-level implication has only a canonical-witness
    normalization premise.  All G5 totality and G14 branch completeness
    are then supplied by the existing checked mathematical constructions. -/
theorem affine_g5_complete_of_canonical_witness
    (r : Nat)
    (hNormalize : ∀ cnf, CertifiedAffine r cnf →
      CanonicalAffineWitness r cnf) :
    AffineG5Complete r := by
  intro cnf hCertified hUnsat
  exact canonical_affine_unsat_has_g5_certificate
    r cnf (hNormalize cnf hCertified) hUnsat

theorem tc063_family_complete_of_canonical_witness
    (c r : Nat)
    (hNormalize : ∀ cnf, CertifiedAffine r cnf →
      CanonicalAffineWitness r cnf) :
    UnsatCoverComplete c (Family c r) := by
  exact affine_g5_complete_implies_tc063_cover_complete c r
    (affine_g5_complete_of_canonical_witness r hNormalize)

#print axioms Witnora.TC063CanonicalAffineBridge.unsat_exact_affine_has_closed_g5_certificate
#print axioms Witnora.TC063CanonicalAffineBridge.affine_g5_complete_of_canonical_witness
#print axioms Witnora.TC063CanonicalAffineBridge.tc063_family_complete_of_canonical_witness

end Witnora.TC063CanonicalAffineBridge
