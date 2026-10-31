import Witnora.SAFCheckedCover
import Witnora.ExactAffineMembership

/-!
# Direct TC-063 theorem target: one auditable completeness gap

The verifier soundness direction is already kernel-proved. The missing
family-level step is not "another UNSAT example": it is that every UNSAT
member of the designated SAF(c,r) family admits an *accepted* bounded G14/G5
cover. This file states that premise exactly and proves what it would yield.

The family predicate is deliberately a parameter. No arbitrary Python
recognizer verdict is silently promoted into mathematical membership, and
no polynomial runtime theorem is inferred from this logical result.
-/

namespace Witnora.TC063Direct

open Witnora.SignedSerialization
open Witnora.SAFCheckedCover
open Witnora.Concrete

/-- Candidate G14/G5 cover data without an assumed truth flag. -/
structure CoverData where
  separator : List Nat
  components : List (Nat × Bool) → List CNF
  selected : List (Nat × Bool) → CNF
  bound : List (Nat × Bool) → Nat
  rows : List (Nat × Bool) → List Witnora.G5Trace.Row
  steps : List (Nat × Bool) → List Witnora.G5Dag.XorRef

def CoverData.accepts (c : Nat) (raw : List (List Int))
    (cert : CoverData) : Bool :=
  checkBoundedUnsatCover c raw cert.separator cert.components
    cert.selected cert.bound cert.rows cert.steps

/-- Every accepted UNSAT cover is semantically correct, with no
    postulated component-model transfer. -/
theorem acceptedCover_sound (c : Nat) (raw : List (List Int))
    (cert : CoverData) (h : cert.accepts c raw = true) :
    cert.separator.length ≤ c ∧ ¬ ∃ a, signedCNFHolds raw a :=
  checkBoundedUnsatCover_sound c raw cert.separator cert.components
    cert.selected cert.bound cert.rows cert.steps h

/-- The one hard *existence* obligation for UNSAT family members.
    This is NOT proved or asserted for the Python implementation. -/
def UnsatCoverComplete (c : Nat)
    (SAF : List (List Int) → Prop) : Prop :=
  ∀ raw, SAF raw → (¬ ∃ a, signedCNFHolds raw a) →
    ∃ cert : CoverData, cert.accepts c raw = true

/-- Exactly what certificate completeness would buy for the restricted
    family: UNSAT iff a checkable bounded G14/G5 cover exists. -/
theorem tc063_unsat_iff_checked_cover
    (c : Nat) (SAF : List (List Int) → Prop)
    (hcomplete : UnsatCoverComplete c SAF)
    (raw : List (List Int)) (hmember : SAF raw) :
    (¬ ∃ a, signedCNFHolds raw a) ↔
      ∃ cert : CoverData, cert.accepts c raw = true := by
  constructor
  · exact hcomplete raw hmember
  · rintro ⟨cert, hcert⟩
    exact (acceptedCover_sound c raw cert hcert).2

/-- Proof-carrying answers; an unchecked UNKNOWN/diagnostic label is not
    an accepted result. -/
inductive CertifiedResult (c : Nat) (raw : List (List Int)) : Type where
  | sat (a : Nat → Bool) (proof : signedCNFHolds raw a)
  | unsat (cert : CoverData) (proof : cert.accepts c raw = true)

theorem tc063_total_certificates_of_complete_cover
    (c : Nat) (SAF : List (List Int) → Prop)
    (hcomplete : UnsatCoverComplete c SAF)
    (raw : List (List Int)) (hmember : SAF raw) :
    Nonempty (CertifiedResult c raw) := by
  classical
  by_cases hsat : ∃ a, signedCNFHolds raw a
  · obtain ⟨a, ha⟩ := hsat
    exact ⟨.sat a ha⟩
  · obtain ⟨cert, hc⟩ := hcomplete raw hmember hsat
    exact ⟨.unsat cert hc⟩

/-- A truly satisfiable formula cannot have an accepted contradictory
    cover, irrespective of a recognizer's untrusted claim about membership. -/
theorem sat_rejects_every_unsat_cover
    (c : Nat) (raw : List (List Int)) (a : Nat → Bool)
    (hsat : signedCNFHolds raw a) (cert : CoverData) :
    cert.accepts c raw = false := by
  cases hc : cert.accepts c raw with
  | false => rfl
  | true =>
      have hu := (acceptedCover_sound c raw cert hc).2
      exact False.elim (hu ⟨a, hsat⟩)

/-- Simple satisfiable source: no candidate may pass the UNSAT gate. -/
example (cert : CoverData) :
    cert.accepts 1 [[1]] = false := by
  apply sat_rejects_every_unsat_cover 1 [[1]] (fun _ => true)
  unfold signedCNFHolds
  decide

#print axioms Witnora.TC063Direct.acceptedCover_sound
#print axioms Witnora.TC063Direct.tc063_unsat_iff_checked_cover
#print axioms Witnora.TC063Direct.tc063_total_certificates_of_complete_cover
#print axioms Witnora.TC063Direct.sat_rejects_every_unsat_cover

end Witnora.TC063Direct
