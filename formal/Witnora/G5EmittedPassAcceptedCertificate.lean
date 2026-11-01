import Witnora.G5PivotPassIndependentReplay

/-!
# Production certificate acceptance for emitted pivot passes

When a successful generated finite pivot pass yields a genuine
contradiction in its proof-carrying DAG, its exact emitted source
operations are accepted by the existing G5 checker. Under the explicit
CNF-to-input-row extraction contract, the original CNF is unsatisfiable.

This closes certificate acceptance for generated passes; it does not
assert that every UNSAT input automatically generates a contradiction.
-/

namespace Witnora.G5EmittedPassAcceptedCertificate

open Witnora.G5Trace
open Witnora.G5Dag
open Witnora.G5IndexedOperationEmitter
open Witnora.G5EmittedPivotPass
open Witnora.G5VerifiedDagEmitter
open Witnora.G5Certificate

/-- A generated pass from the real input state is exactly the production
    source run for its emitted operation list. -/
theorem emitPass_source_run
    (initial : List Row) (v pivotSlot : Nat)
    (targets : List Nat) (result : SourceState initial)
    (operations : List Op)
    (hpass : emitPass initial v pivotSlot targets
      (SourceState.start initial) = some (operations, result)) :
    run initial operations = some result := by
  have h := emitPass_replays initial v pivotSlot targets
    (SourceState.start initial) result operations hpass
  simpa [run, executeFrom] using h

/-- Every actual contradiction discovered in the emitted DAG is
    accepted as a G5 certificate by the unchanged production checker. -/
theorem emitted_pass_accepts_contradiction
    (initial : List Row) (v pivotSlot : Nat)
    (targets : List Nat) (result : SourceState initial)
    (operations : List Op)
    (hpass : emitPass initial v pivotSlot targets
      (SourceState.start initial) = some (operations, result))
    (hbad : ∃ row ∈ result.dag.rows,
      row.coefficients = [] ∧ row.rhs = true) :
    accepts initial operations = true := by
  have hrun := emitPass_source_run initial v pivotSlot
    targets result operations hpass
  unfold accepts
  rw [hrun]
  exact Builder.accepted_of_contradiction initial result.dag hbad

/-- End-to-end soundness for a successfully emitted contradictory pivot
    pass: assuming source-row extraction is sound, no assignment satisfies
    the original CNF model predicate. -/
theorem emitted_pass_unsat_of_extraction
    (bound v pivotSlot : Nat)
    (cnfHolds : (Nat → Bool) → Prop)
    (initial : List Row) (targets : List Nat)
    (result : SourceState initial) (operations : List Op)
    (hextract : ∀ a, cnfHolds a → AllHold bound initial a)
    (hpass : emitPass initial v pivotSlot targets
      (SourceState.start initial) = some (operations, result))
    (hbad : ∃ row ∈ result.dag.rows,
      row.coefficients = [] ∧ row.rhs = true) :
    ¬ ∃ a : Nat → Bool, cnfHolds a := by
  exact accepts_unsat_of_extraction bound cnfHolds
    initial operations hextract
    (emitted_pass_accepts_contradiction initial v pivotSlot
      targets result operations hpass hbad)

#print axioms Witnora.G5EmittedPassAcceptedCertificate.emitPass_source_run
#print axioms Witnora.G5EmittedPassAcceptedCertificate.emitted_pass_accepts_contradiction
#print axioms Witnora.G5EmittedPassAcceptedCertificate.emitted_pass_unsat_of_extraction

end Witnora.G5EmittedPassAcceptedCertificate
