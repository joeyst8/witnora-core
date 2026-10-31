import Witnora.SemanticSAF

/-!
# Direct completeness counterexample to current Python G5 extraction

The CNF x1 ∧ ¬x1 is an UNSAT affine component. It has a completely
kernel-checkable XOR representation as two unit-width rows, and belongs to
the checker-admissible SAF(0,2) family. Python's current affine extractor,
however, defaults to min_arity=2 and silently skips these rows.

This disproves completeness of the *current Python certificate producer*
for the supported Lean family; it does NOT refute Lean checker soundness or
prove that no alternative valid cover certificate can exist.
-/

namespace Witnora.TC063UnitCounterexample

open Witnora.Concrete
open Witnora.SignedSerialization
open Witnora.ExactAffineMembership
open Witnora.SemanticSAF

def unitContradiction : CNF :=
  [[(1, true)], [(1, false)]]

def unitRows : List Witnora.G5Trace.Row :=
  [{coefficients := [1], rhs := true},
   {coefficients := [1], rhs := false}]

/-- Both unit equations are *exactly* extracted, not merely implied. -/
theorem unit_rows_exact :
    checkSemanticExactAffine 2 unitContradiction unitRows = true := by
  decide

theorem unit_component_in_certified_family :
    CertifiedAffine 2 unitContradiction :=
  ⟨unitRows, unit_rows_exact⟩

/-- A fully explicit member of the independent certificate-admissible
    family, requiring no separator at all. -/
theorem unit_counterexample_in_saf :
    Family 0 2 [[1], [-1]] := by
  refine ⟨[], by decide, by decide,
    (fun _ => [unitContradiction]), ?_⟩
  intro branch hb
  have hbranch : branch = [] := by
    simpa [Witnora.SeparatorAssignments.enumerate] using hb
  subst branch
  refine ⟨by decide, ?_, ?_⟩
  · simp [Independent]
  · intro component hmem
    have heq : component = unitContradiction := by
      simpa using hmem
    subst component
    exact unit_component_in_certified_family

/-- Independent finite proof that the original signed CNF is UNSAT. -/
theorem unit_counterexample_unsat :
    ¬ ∃ a, signedCNFHolds [[1], [-1]] a := by
  intro ⟨a, ha⟩
  unfold signedCNFHolds at ha
  cases hv : a 1 <;>
    simp [decode, Witnora.FiniteXor.signedLitTrue, hv] at ha

#print axioms Witnora.TC063UnitCounterexample.unit_rows_exact
#print axioms Witnora.TC063UnitCounterexample.unit_counterexample_in_saf
#print axioms Witnora.TC063UnitCounterexample.unit_counterexample_unsat

end Witnora.TC063UnitCounterexample
