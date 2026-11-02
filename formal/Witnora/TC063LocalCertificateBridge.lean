import Witnora.TC063ModelGluing
import Witnora.SAFCheckedCover

/-!
# TC-063 global cover completeness reduced to local G5 completeness

The family-level semantic G14 cover is already proved from exact residual
partitions, independent component supports and model gluing. This theorem
constructs one *accepted executable G14/G5 cover* from that semantic cover
provided the one remaining local G5 obligation holds:

  Each UNSAT CertifiedAffine component has an accepted closed G5 certificate.

The premise is deliberately explicit. This file is NOT a completed
unconditional TC-063 theorem, a polynomial runtime guarantee, or a proof
about arbitrary CPython execution.
-/

namespace Witnora.TC063LocalCertificateBridge

open Witnora.Concrete
open Witnora.G5Extraction
open Witnora.SemanticSAF
open Witnora.TC063Direct
open Witnora.TC063CoverBridge
open Witnora.TC063ModelGluing

/-- The one remaining *component-level* certificate existence target.
    Every UNSAT independently certifiable affine component must admit
    a concrete closed G5 certificate accepted by the production checker. -/
def LocalCheckedG5Complete (r : Nat) : Prop :=
  ∀ component : CNF, CertifiedAffine r component →
    (¬ ∃ a : Nat → Bool, CNFHolds component a) →
    ∃ (bound : Nat) (rows : List Witnora.G5Trace.Row)
        (steps : List Witnora.G5Dag.XorRef),
      Witnora.SparseBridge.checkG5Closed
        bound component rows steps = true

/-- Branchwise certificate data, with membership and acceptance proved
    separately rather than trusted as fields of a Python object. -/
structure BranchG5Witness where
  selected : CNF
  bound : Nat
  rows : List Witnora.G5Trace.Row
  steps : List Witnora.G5Dag.XorRef

/-- The existing G14 semantic-cover theorem plus a local accepted-G5
    completeness hypothesis construct an actual bounded G14/G5 certificate
    for every UNSAT SAF member, with no hidden global SAT oracle. -/
theorem unsat_cover_complete_of_local_g5
    (c r : Nat)
    (hlocal : LocalCheckedG5Complete r) :
    UnsatCoverComplete c (Family c r) := by
  intro raw hfamily hunsat
  classical
  obtain ⟨separator, _, hsize, components, hbranches⟩ := hfamily
  have hglue : BranchModelGluing separator components := by
    intro branch hb hmodels
    exact glue_independent_unfixed_components
      (Witnora.SeparatorAssignments.fixedOf branch)
      (components branch)
      (hbranches branch hb).2.1
      (partition_components_unfixed
        (Witnora.SeparatorAssignments.fixedOf branch)
        (Witnora.SignedSerialization.decodeCNF raw)
        (components branch) (hbranches branch hb).1)
      hmodels
  have hcover : SemanticUnsatCover separator components :=
    unsat_has_semantic_component_cover raw separator components
      (fun branch hb => (hbranches branch hb).1)
      hglue hunsat
  let branches := Witnora.SeparatorAssignments.enumerate separator
  have perBranch (branch : List (Nat × Bool)) (hb : branch ∈ branches) :
      ∃ witness : BranchG5Witness,
        witness.selected ∈ components branch ∧
        Witnora.SparseBridge.checkG5Closed witness.bound
          witness.selected witness.rows witness.steps = true := by
    obtain ⟨component, hmem, hu⟩ := hcover branch hb
    have haffine : CertifiedAffine r component :=
      (hbranches branch hb).2.2 component hmem
    obtain ⟨bound, rows, steps, hchecked⟩ :=
      hlocal component haffine hu
    exact ⟨⟨component, bound, rows, steps⟩, hmem, hchecked⟩
  let witness : List (Nat × Bool) → BranchG5Witness :=
    fun branch =>
      if hb : branch ∈ branches then
        Classical.choose (perBranch branch hb)
      else ⟨[], 0, [], []⟩
  refine ⟨{
    separator := separator
    components := components
    selected := fun branch => (witness branch).selected
    bound := fun branch => (witness branch).bound
    rows := fun branch => (witness branch).rows
    steps := fun branch => (witness branch).steps
  }, ?_⟩
  change
    (decide (separator.length ≤ c) &&
      (Witnora.SeparatorAssignments.enumerate separator).all
        (fun branch =>
          (Witnora.ComponentPartition.checkPartition
            (Witnora.Conditioning.conditionCNF
              (Witnora.SeparatorAssignments.fixedOf branch)
              (Witnora.SignedSerialization.decodeCNF raw))
            (components branch) &&
           decide ((witness branch).selected ∈ components branch)) &&
          Witnora.SparseBridge.checkG5Closed
            (witness branch).bound (witness branch).selected
            (witness branch).rows (witness branch).steps)) = true
  simp only [Bool.and_eq_true]
  constructor
  · simp [hsize]
  · apply List.all_eq_true.mpr
    intro branch hb
    have hselected := Classical.choose_spec (perBranch branch hb)
    have heq : witness branch = Classical.choose (perBranch branch hb) := by
      have hb' : branch ∈ branches := hb
      simp only [witness, dif_pos hb']
    have hpart := (hbranches branch hb).1
    rw [heq]
    simp [hpart, hselected.1, hselected.2]

/-- Precise reduction of the published family-level TC-063 logical target:
    assuming local affine G5 completeness, UNSAT is equivalent to the
    existence of an accepted *bounded* G14/G5 cover for any SAF member. -/
theorem tc063_family_iff_of_local_g5
    (c r : Nat) (hlocal : LocalCheckedG5Complete r)
    (raw : List (List Int)) (hmember : Family c r raw) :
    (¬ ∃ a, Witnora.SignedSerialization.signedCNFHolds raw a) ↔
      ∃ cert : CoverData, cert.accepts c raw = true := by
  exact tc063_unsat_iff_checked_cover c (Family c r)
    (unsat_cover_complete_of_local_g5 c r hlocal) raw hmember

#print axioms Witnora.TC063LocalCertificateBridge.unsat_cover_complete_of_local_g5
#print axioms Witnora.TC063LocalCertificateBridge.tc063_family_iff_of_local_g5

end Witnora.TC063LocalCertificateBridge
