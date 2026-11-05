import Witnora.TC063ModelGluing
import Witnora.G5CompleteCheckedCertificate

/-!
# TC-063 exact logical completeness reduction

The SAF(c,r) family already has an exact independent residual partition
on every separator branch, and the model-gluing theorem establishes an
UNSAT residual component on every branch of any UNSAT family member.

Here we isolate the next genuinely missing obligation: an UNSAT component
with accepted, source-bound affine extraction evidence must admit an
accepted closed G5 contradiction certificate.  *Assuming exactly this
obligation*, we construct a bounded TC-063 cover certificate and prove
the full family-level completeness statement.  No completeness claim is
made without that explicit assumption, and no machine-time bound follows.
-/

namespace Witnora.TC063CompletenessReduction

open Witnora.Concrete
open Witnora.G5Extraction
open Witnora.SemanticSAF
open Witnora.TC063Direct
open Witnora.TC063CoverBridge
open Witnora.TC063ModelGluing
open Witnora.SAFCheckedCover
open Witnora.ComponentPartition

/-- The remaining restricted affine UNSAT-to-G5-certificate completeness
    problem, stated independently of Python and the G14 separator loop. -/
def AffineG5Complete (r : Nat) : Prop :=
  ∀ cnf : CNF,
    CertifiedAffine r cnf →
    (¬ ∃ a : Nat → Bool, CNFHolds cnf a) →
    ∃ (bound : Nat) (rows : List Witnora.G5Trace.Row)
      (steps : List Witnora.G5Dag.XorRef),
      Witnora.SparseBridge.checkG5Closed bound cnf rows steps = true

/-- Every UNSAT SAF(c,r) member has an accepted bounded G14/G5 cover
    *if* unsatisfiable certified-affine components always admit checked
    G5 certificates.  All G14 model gluing and branch selection are
    constructed here rather than postulated. -/
theorem affine_g5_complete_implies_tc063_cover_complete
    (c r : Nat) (hG5 : AffineG5Complete r) :
    UnsatCoverComplete c (Family c r) := by
  classical
  intro raw hFamily hUnsat
  obtain ⟨separator, _, hBound, components, hBranches⟩ := hFamily
  have hPartition :
      ∀ branch ∈ Witnora.SeparatorAssignments.enumerate separator,
        checkPartition
          (Witnora.Conditioning.conditionCNF
            (Witnora.SeparatorAssignments.fixedOf branch)
            (Witnora.SignedSerialization.decodeCNF raw))
          (components branch) = true := by
    intro branch hb
    exact (hBranches branch hb).1
  have hGluing : BranchModelGluing separator components := by
    intro branch hb hModels
    exact glue_independent_unfixed_components
      (Witnora.SeparatorAssignments.fixedOf branch)
      (components branch)
      (hBranches branch hb).2.1
      (partition_components_unfixed
        (Witnora.SeparatorAssignments.fixedOf branch)
        (Witnora.SignedSerialization.decodeCNF raw)
        (components branch) (hBranches branch hb).1)
      hModels
  have hSemantic : SemanticUnsatCover separator components :=
    unsat_has_semantic_component_cover
      raw separator components hPartition hGluing hUnsat
  let BranchData := CNF × Nat × List Witnora.G5Trace.Row ×
    List Witnora.G5Dag.XorRef
  have hWitness :
      ∀ branch : List (Nat × Bool),
        ∃ data : BranchData,
          branch ∈ Witnora.SeparatorAssignments.enumerate separator →
            data.1 ∈ components branch ∧
              Witnora.SparseBridge.checkG5Closed
                data.2.1 data.1 data.2.2.1 data.2.2.2 = true := by
    intro branch
    by_cases hb :
        branch ∈ Witnora.SeparatorAssignments.enumerate separator
    · obtain ⟨selected, hSelected, hSelectedUnsat⟩ :=
        hSemantic branch hb
      have hAffine : CertifiedAffine r selected :=
        (hBranches branch hb).2.2 selected hSelected
      obtain ⟨bound, rows, steps, hCheck⟩ :=
        hG5 selected hAffine hSelectedUnsat
      refine ⟨(selected, bound, rows, steps), ?_⟩
      intro _
      exact ⟨hSelected, hCheck⟩
    · refine ⟨([], 0, [], []), ?_⟩
      intro hb'
      exact False.elim (hb hb')
  let data : List (Nat × Bool) → BranchData :=
    fun branch => Classical.choose (hWitness branch)
  let cert : CoverData := {
    separator := separator
    components := components
    selected := fun branch => (data branch).1
    bound := fun branch => (data branch).2.1
    rows := fun branch => (data branch).2.2.1
    steps := fun branch => (data branch).2.2.2
  }
  refine ⟨cert, ?_⟩
  change
    (decide (separator.length ≤ c) &&
      (Witnora.SeparatorAssignments.enumerate separator).all
        (fun branch =>
          (checkPartition
            (Witnora.Conditioning.conditionCNF
              (Witnora.SeparatorAssignments.fixedOf branch)
              (Witnora.SignedSerialization.decodeCNF raw))
            (components branch) &&
            decide ((data branch).1 ∈ components branch)) &&
          Witnora.SparseBridge.checkG5Closed
            (data branch).2.1 (data branch).1
            (data branch).2.2.1 (data branch).2.2.2)) = true
  have hBoundBool : decide (separator.length ≤ c) = true := by
    simp [hBound]
  rw [hBoundBool]
  simp only [Bool.true_and]
  apply List.all_eq_true.mpr
  intro branch hb
  obtain ⟨hSelected, hCheck⟩ :=
    (Classical.choose_spec (hWitness branch)) hb
  simpa [hPartition branch hb, data] using
    (And.intro hSelected hCheck)

/-- The conditional full TC-063 UNSAT iff accepted-cover theorem, with
    its sole remaining logical assumption displayed as AffineG5Complete. -/
theorem tc063_family_iff_of_affine_g5_complete
    (c r : Nat) (hG5 : AffineG5Complete r)
    (raw : List (List Int)) (hFamily : Family c r raw) :
    (¬ ∃ a, Witnora.SignedSerialization.signedCNFHolds raw a) ↔
      ∃ cert : CoverData, cert.accepts c raw = true := by
  exact tc063_unsat_iff_checked_cover c (Family c r)
    (affine_g5_complete_implies_tc063_cover_complete c r hG5)
    raw hFamily

#print axioms Witnora.TC063CompletenessReduction.affine_g5_complete_implies_tc063_cover_complete
#print axioms Witnora.TC063CompletenessReduction.tc063_family_iff_of_affine_g5_complete

end Witnora.TC063CompletenessReduction
