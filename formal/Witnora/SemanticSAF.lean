import Witnora.TC063Direct

/-!
# A mathematical, Python-independent certificate-admissible SAF(c,r) target

Membership here requires checkable evidence of equivalence to bounded
GF(2) rows for every variable-disjoint residual component on every branch.
It does not define the family as "whatever Python recognizes".

The same mathematical CNF model set may have many syntactically distinct
representations. This choice is stronger than the existing narrow
exact-source-coverage recognizer. Recognition completeness is open.
-/

namespace Witnora.SemanticSAF

open Witnora.Concrete
open Witnora.G5Extraction
open Witnora.Extraction
open Witnora.ComponentPartition
open Witnora.Conditioning
open Witnora.SignedSerialization
open Witnora.ExactAffineMembership
open Witnora.TC063Direct

/-- Semantic affine representability by bounded, positive-ID distinct rows.
    Crucially, no Python extraction algorithm is mentioned. -/
def SemanticAffine (r : Nat) (cnf : CNF) : Prop :=
  ∃ rows : List Witnora.G5Trace.Row,
    rows.all (rowSupported r) = true ∧
    ∀ a : Nat → Bool,
      CNFHolds cnf a ↔
        ∀ row ∈ rows, parityVars row.coefficients a = row.rhs

/-- A passing executable equivalence check is sufficient evidence for
    membership in the independently defined semantic affine family. -/
theorem checked_implies_semantic_affine
    (r : Nat) (cnf : CNF) (rows : List Witnora.G5Trace.Row)
    (h : checkSemanticExactAffine r cnf rows = true) :
    SemanticAffine r cnf := by
  refine ⟨rows, ?_, ?_⟩
  · unfold checkSemanticExactAffine at h
    simp at h
    exact List.all_eq_true.mpr h.1.1
  · intro a
    exact checkSemanticExactAffine_sound r cnf rows h a

/-- Adding a clause entailed by the existing source leaves exact semantic
    affine membership intact, using the same row witnesses. -/
theorem semantic_affine_closed_under_covered_clause
    (r : Nat) (cnf : CNF) (extra : List Literal)
    (hmember : SemanticAffine r cnf)
    (hcovered : checkClauseCoverage cnf extra = true) :
    SemanticAffine r (cnf ++ [extra]) := by
  obtain ⟨rows, hsupported, hequiv⟩ := hmember
  refine ⟨rows, hsupported, ?_⟩
  intro a
  exact (covered_clause_extension_iff cnf extra hcovered a).trans (hequiv a)

/-- Pure model-equivalence is too permissive for a *complexity* family:
    every UNSAT CNF is equivalent to the inconsistent empty-support XOR row.
    This theorem is an adversarial warning, not a membership algorithm. -/
theorem every_unsat_semantically_affine (r : Nat) (cnf : CNF)
    (hunsat : ¬ ∃ a : Nat → Bool, CNFHolds cnf a) :
    SemanticAffine r cnf := by
  refine ⟨[{coefficients := [], rhs := true}], by decide, ?_⟩
  intro a
  constructor
  · intro hc
    exact False.elim (hunsat ⟨a, hc⟩)
  · intro hrows
    have hbad := hrows {coefficients := [], rhs := true} (by simp)
    simp [parityVars] at hbad

/-- The *actual* restricted family therefore requires a concrete,
    independently checkable affine extraction witness, not mere semantic
    existential equivalence. This still does not trust Python execution. -/
def CertifiedAffine (r : Nat) (cnf : CNF) : Prop :=
  ∃ rows : List Witnora.G5Trace.Row,
    checkSemanticExactAffine r cnf rows = true

theorem certified_affine_sound (r : Nat) (cnf : CNF)
    (h : CertifiedAffine r cnf) : SemanticAffine r cnf := by
  obtain ⟨rows, hc⟩ := h
  exact checked_implies_semantic_affine r cnf rows hc

/-- Variable support of a component, including every residual literal. -/
def variableSupport (cnf : CNF) : List Nat :=
  cnf.flatten.map Prod.fst

/-- A component list is genuinely independent when no two distinct
    components share any variable; no connected-component finder is trusted. -/
def Independent (parts : List CNF) : Prop :=
  parts.Pairwise (fun left right =>
    ∀ v, v ∈ variableSupport left → v ∉ variableSupport right)

/-- Certificate-admissible SAF(c,r): a bounded duplicate-free separator,
    exhaustive branches, exact independent residual partitions, and each
    component equipped with a checkable exact affine representation.
    This avoids the vacuous all-UNSAT semantic-equivalence family. -/
def Family (c r : Nat) (raw : List (List Int)) : Prop :=
  ∃ separator : List Nat,
    separator.Nodup ∧ separator.length ≤ c ∧
    ∃ components : List (Nat × Bool) → List CNF,
      ∀ branch ∈ Witnora.SeparatorAssignments.enumerate separator,
        checkPartition
          (conditionCNF (Witnora.SeparatorAssignments.fixedOf branch)
            (decodeCNF raw))
          (components branch) = true ∧
        Independent (components branch) ∧
        ∀ component ∈ components branch, CertifiedAffine r component

/-- Even a semantic SAF witness guarantees the exact original-to-residual
    model relationship on every branch. No Python conditioning contract. -/
theorem family_partition_model_transfer
    (c r : Nat) (raw : List (List Int)) (hfamily : Family c r raw) :
    ∃ separator : List Nat,
      separator.length ≤ c ∧
      ∃ components : List (Nat × Bool) → List CNF,
        ∀ branch ∈ Witnora.SeparatorAssignments.enumerate separator,
          ∀ a : Nat → Bool,
            agreesWith (Witnora.SeparatorAssignments.fixedOf branch) a →
              (CNFHolds (decodeCNF raw) a ↔
                (components branch).all (fun component =>
                  component.all (fun clause =>
                    clause.any (Witnora.FiniteXor.signedLitTrue a))) = true) := by
  obtain ⟨separator, _, hsize, components, hbranches⟩ := hfamily
  refine ⟨separator, hsize, components, ?_⟩
  intro branch hb a hag
  exact conditioned_partition_correct
    (Witnora.SeparatorAssignments.fixedOf branch)
    (decodeCNF raw) (components branch)
    (hbranches branch hb).1 a hag

/-- The full TC-063 soundness/completeness theorem, now instantiated with
    an explicit mathematical family rather than a Python-recognized label.
    Its only family-level logical gap is the shown cover-completeness premise;
    machine-cost and interpreter-refinement remain additional open targets. -/
theorem tc063_semantic_family_target
    (c r : Nat)
    (hcomplete : UnsatCoverComplete c (Family c r))
    (raw : List (List Int)) (hmember : Family c r raw) :
    (¬ ∃ a, signedCNFHolds raw a) ↔
      ∃ cert : CoverData, cert.accepts c raw = true :=
  tc063_unsat_iff_checked_cover c (Family c r) hcomplete raw hmember

/-- The redundant three-variable clause is also *certifiably* affine in
    this supported case, despite the historical Python recognizer rejecting
    its syntactic source coverage. -/
example :
    CertifiedAffine 2
      [[(1, true), (2, false)], [(1, false), (2, true)],
       [(1, true), (2, false), (3, true)]] := by
  refine ⟨[{coefficients := [1, 2], rhs := false}], ?_⟩
  decide

/-- A concrete redundant clause still belongs to the same semantic affine
    component: x1=x2 plus a weaker three-variable clause. -/
example :
    SemanticAffine 2
      [[(1, true), (2, false)], [(1, false), (2, true)],
       [(1, true), (2, false), (3, true)]] := by
  apply checked_implies_semantic_affine 2 _
    [{coefficients := [1, 2], rhs := false}]
  decide

#print axioms Witnora.SemanticSAF.checked_implies_semantic_affine
#print axioms Witnora.SemanticSAF.every_unsat_semantically_affine
#print axioms Witnora.SemanticSAF.certified_affine_sound
#print axioms Witnora.SemanticSAF.semantic_affine_closed_under_covered_clause
#print axioms Witnora.SemanticSAF.family_partition_model_transfer
#print axioms Witnora.SemanticSAF.tc063_semantic_family_target

end Witnora.SemanticSAF
