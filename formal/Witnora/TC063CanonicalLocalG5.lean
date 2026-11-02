import Witnora.G5ExecutableTotality
import Witnora.ExactAffineMembership
import Witnora.SparseBridge

/-!
# TC-063 local G5 completeness for canonical certified affine witnesses

No UNSAT test or model search is included. Exact semantic affine membership,
a checked canonical sparse representation and a finite complete variable
schedule yield a production-accepted shared-DAG G5 proof for any UNSAT CNF.

This is an important *subcase* of TC063LocalCertificateBridge.LocalCheckedG5Complete.
The remaining general case must construct an equivalent canonical witness
from an arbitrary CertifiedAffine witness, without silently assuming it.
-/

namespace Witnora.TC063CanonicalLocalG5

open Witnora.Concrete
open Witnora.G5Trace
open Witnora.G5Extraction
open Witnora.G5Certificate
open Witnora.SparseBridge
open Witnora.ExactAffineMembership

/-- Every variable appearing in a canonical support is below its bound. -/
theorem canonicalSupport_mem_lt
    (bound : Nat) (coeff : List Nat) (v : Nat)
    (hmem : v ∈ canonicalSupport bound coeff) : v < bound := by
  induction bound with
  | zero =>
      simp [canonicalSupport] at hmem
  | succ n ih =>
      change v ∈ canonicalSupport n coeff ++
        (if decide (n ∈ coeff) then [n] else []) at hmem
      rcases List.mem_append.mp hmem with hprev | hlast
      · exact Nat.lt_trans (ih hprev) (Nat.lt_succ_self n)
      · by_cases hn : n ∈ coeff
        · simp [hn] at hlast
          subst v
          exact Nat.lt_succ_self n
        · simp [hn] at hlast

/-- The full bounded variable range is automatically a complete schedule
    for every row accepted by the canonical sparse representation gate. -/
theorem canonicalRows_range_covered
    (bound : Nat) (rows : List Row)
    (hcanonical : checkCanonicalRows bound rows = true) :
    Witnora.G5InitialSupportCoverage.Covered
      (List.range bound) rows := by
  intro row hr v hv
  have hrow : checkCanonicalRow bound row = true :=
    List.all_eq_true.mp hcanonical row hr
  have hcoeff : row.coefficients =
      canonicalSupport bound row.coefficients := by
    simpa [checkCanonicalRow] using hrow
  have hcanon : v ∈ canonicalSupport bound row.coefficients := by
    rw [← hcoeff]
    exact hv
  exact List.mem_range.mpr
    (canonicalSupport_mem_lt bound row.coefficients v hcanon)

/-- An UNSAT, semantically exact affine source with a canonical source-row
    witness necessarily admits a checked G5 DAG contradiction. In
    particular, successful execution of the source pivot scheduler is not
    an additional hypothesis. -/
theorem canonical_certified_unsat_has_closed_g5
    (r bound : Nat) (cnf : CNF) (rows : List Row)
    (hexact : checkSemanticExactAffine r cnf rows = true)
    (hcanonical : checkCanonicalRows bound rows = true)
    (hunsat : ¬ ∃ a : Nat → Bool, CNFHolds cnf a) :
    ∃ steps : List Witnora.G5Dag.XorRef,
      checkG5Closed bound cnf rows steps = true := by
  have hcoverage := canonicalRows_range_covered bound rows hcanonical
  have hvars : ∀ v ∈ List.range bound, v < bound := by
    intro v hv
    exact List.mem_range.mp hv
  have hequiv : ∀ a : Nat → Bool,
      CNFHolds cnf a ↔
        (∀ row ∈ rows, RowHolds bound row a) := by
    intro a
    have hsource := checkSemanticExactAffine_sound r cnf rows
      hexact a
    constructor
    · intro h row hr
      have hp := (hsource.mp h) row hr
      have heq := checkCanonicalRows_sound bound rows
        hcanonical row hr a
      exact heq.trans hp
    · intro h
      apply hsource.mpr
      intro row hr
      have heq := checkCanonicalRows_sound bound rows
        hcanonical row hr a
      exact heq.symm.trans (h row hr)
  obtain ⟨outcome, _, haccepts⟩ :=
    Witnora.G5ExecutableTotality.cnf_unsat_has_checked_certificate_of_equivalence
      rows bound (List.range bound) (fun a => CNFHolds cnf a)
      hcoverage hvars hequiv hunsat
  obtain ⟨state, _, hdag⟩ :=
    Witnora.G5IndexedOperationEmitter.accepts_has_checked_dag
      rows outcome.operations haccepts
  have hsplit := hexact
  simp [checkSemanticExactAffine] at hsplit
  have hinit : checkInitialRows cnf rows = true :=
    hsplit.1.2
  refine ⟨state.dag.steps, ?_⟩
  simp [checkG5Closed, hinit, hcanonical, hdag]

#print axioms Witnora.TC063CanonicalLocalG5.canonicalSupport_mem_lt
#print axioms Witnora.TC063CanonicalLocalG5.canonicalRows_range_covered
#print axioms Witnora.TC063CanonicalLocalG5.canonical_certified_unsat_has_closed_g5

end Witnora.TC063CanonicalLocalG5
