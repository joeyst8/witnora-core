import Witnora.SemanticSAF

/-!
# TC-063 semantic cover: expose the exact model-gluing obligation

This module derives UNSAT residual-component cover existence once a
branch's independent local models can be amalgamated with its separator.
It does not assume the existence of a G5 certificate, nor claim the
independence-to-gluing lemma has been completed.
-/

namespace Witnora.TC063CoverBridge

open Witnora.Concrete
open Witnora.G5Extraction
open Witnora.Conditioning
open Witnora.ComponentPartition
open Witnora.SignedSerialization
open Witnora.SemanticSAF

/-- A *semantic* UNSAT cover: one UNSAT residual component per branch.
    There is no G5 row trace here yet. -/
def SemanticUnsatCover (separator : List Nat)
    (components : List (Nat × Bool) → List CNF) : Prop :=
  ∀ branch ∈ Witnora.SeparatorAssignments.enumerate separator,
    ∃ component ∈ components branch,
      ¬ ∃ a : Nat → Bool, CNFHolds component a

/-- Exact witness-gluing obligation: local component models can be made
    consistent simultaneously and with the chosen separator branch. -/
def BranchModelGluing (separator : List Nat)
    (components : List (Nat × Bool) → List CNF) : Prop :=
  ∀ branch ∈ Witnora.SeparatorAssignments.enumerate separator,
    (∀ component ∈ components branch,
      ∃ a : Nat → Bool, CNFHolds component a) →
    ∃ a : Nat → Bool,
      agreesWith (Witnora.SeparatorAssignments.fixedOf branch) a ∧
      ∀ component ∈ components branch, CNFHolds component a

/-- A structural, exact partition and the model-gluing fact suffice
    to derive the complete *semantic* UNSAT component cover. -/
theorem unsat_has_semantic_component_cover
    (raw : List (List Int)) (separator : List Nat)
    (components : List (Nat × Bool) → List CNF)
    (hpartition :
      ∀ branch ∈ Witnora.SeparatorAssignments.enumerate separator,
        checkPartition
          (conditionCNF
            (Witnora.SeparatorAssignments.fixedOf branch)
            (decodeCNF raw))
          (components branch) = true)
    (hglue : BranchModelGluing separator components)
    (hunsat : ¬ ∃ a : Nat → Bool, signedCNFHolds raw a) :
    SemanticUnsatCover separator components := by
  classical
  intro branch hb
  by_contra hno
  have hlocal : ∀ component ∈ components branch,
      ∃ a : Nat → Bool, CNFHolds component a := by
    intro component hc
    by_contra hnot
    exact hno ⟨component, hc, hnot⟩
  obtain ⟨a, hagree, hall⟩ := hglue branch hb hlocal
  have hparts :
      (components branch).all
        (fun component => component.all
          (fun clause => clause.any
            (Witnora.FiniteXor.signedLitTrue a))) = true := by
    apply List.all_eq_true.mpr
    intro component hc
    exact hall component hc
  have hsource : CNFHolds (decodeCNF raw) a :=
    (conditioned_partition_correct
      (Witnora.SeparatorAssignments.fixedOf branch)
      (decodeCNF raw) (components branch)
      (hpartition branch hb) a hagree).2 hparts
  exact hunsat ⟨a, (signedCNFHolds_iff raw a).2 hsource⟩

/-- For semantic SAF membership, the remaining premise is precisely
    model gluing; no additional model-transfer assumption is hidden. -/
theorem family_unsat_has_semantic_cover
    (c r : Nat) (raw : List (List Int))
    (hfamily : Family c r raw)
    (hunsat : ¬ ∃ a : Nat → Bool, signedCNFHolds raw a) :
    ∃ separator : List Nat,
      separator.length ≤ c ∧
      ∃ components : List (Nat × Bool) → List CNF,
        BranchModelGluing separator components →
          SemanticUnsatCover separator components := by
  obtain ⟨separator, _, hsize, components, hbranch⟩ := hfamily
  refine ⟨separator, hsize, components, ?_⟩
  intro hglue
  exact unsat_has_semantic_component_cover raw separator components
    (fun branch hb => (hbranch branch hb).1) hglue hunsat

#print axioms Witnora.TC063CoverBridge.unsat_has_semantic_component_cover
#print axioms Witnora.TC063CoverBridge.family_unsat_has_semantic_cover

end Witnora.TC063CoverBridge
