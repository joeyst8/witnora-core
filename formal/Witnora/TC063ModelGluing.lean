import Witnora.TC063CoverBridge

/-!
# TC-063 model-gluing locality and two-component construction

The checker evaluates every literal from its variable value. This file
proves that changing variables outside a component's support cannot change
that component's truth value, and constructs a simultaneous satisfying
assignment for two disjoint components.
-/

namespace Witnora.TC063ModelGluing

open Witnora.Concrete
open Witnora.FiniteXor
open Witnora.G5Extraction
open Witnora.SemanticSAF

/-- A literal depends only on its own variable, not on other assignments. -/
theorem signedLitTrue_congr (a b : Nat → Bool) (lit : Literal)
    (h : a lit.1 = b lit.1) :
    signedLitTrue a lit = signedLitTrue b lit := by
  cases lit with
  | mk v polarity =>
    cases polarity <;> simp [signedLitTrue, h]

/-- A clause is unchanged if its literal variables keep the same values. -/
theorem clause_eval_congr (a b : Nat → Bool) (clause : List Literal)
    (h : ∀ lit ∈ clause, a lit.1 = b lit.1) :
    clause.any (signedLitTrue a) = clause.any (signedLitTrue b) := by
  induction clause with
  | nil => rfl
  | cons lit rest ih =>
    have hhead : a lit.1 = b lit.1 := h lit (by simp)
    have htail : ∀ item ∈ rest, a item.1 = b item.1 := by
      intro item hi
      exact h item (by simp [hi])
    simp only [List.any_cons, signedLitTrue_congr a b lit hhead,
      ih htail]

/-- Locality theorem: a component's truth depends only on its own support. -/
theorem cnfHolds_congr_on_support (cnf : CNF)
    (a b : Nat → Bool)
    (h : ∀ v ∈ variableSupport cnf, a v = b v) :
    CNFHolds cnf a ↔ CNFHolds cnf b := by
  have hclause : ∀ clause ∈ cnf,
      clause.any (signedLitTrue a) =
        clause.any (signedLitTrue b) := by
    intro clause hc
    apply clause_eval_congr a b clause
    intro lit hl
    apply h lit.1
    apply List.mem_map.mpr
    refine ⟨lit, ?_, rfl⟩
    exact List.mem_flatten.mpr ⟨clause, hc, hl⟩
  constructor
  · intro ha
    apply List.all_eq_true.mpr
    intro clause hc
    rw [← hclause clause hc]
    exact List.all_eq_true.mp ha clause hc
  · intro hb
    apply List.all_eq_true.mpr
    intro clause hc
    rw [hclause clause hc]
    exact List.all_eq_true.mp hb clause hc

/-- Preserve the first model on its support; keep the second elsewhere. -/
def patchSupport (support : List Nat) (first second : Nat → Bool) :
    Nat → Bool :=
  fun v => if v ∈ support then first v else second v

/-- Construct a satisfying assignment for two independent components.
    In particular, their individually selected models need not agree
    outside their own supports. -/
theorem glue_two_disjoint_components
    (left right : CNF)
    (hdisjoint : ∀ v, v ∈ variableSupport left →
      v ∉ variableSupport right)
    (al ar : Nat → Bool)
    (hl : CNFHolds left al)
    (hr : CNFHolds right ar) :
    ∃ a : Nat → Bool, CNFHolds left a ∧ CNFHolds right a := by
  let a := patchSupport (variableSupport left) al ar
  refine ⟨a, ?_, ?_⟩
  · exact (cnfHolds_congr_on_support left al a
      (by
        intro v hv
        simp [a, patchSupport, hv])).1 hl
  · exact (cnfHolds_congr_on_support right ar a
      (by
        intro v hv
        have hnot : v ∉ variableSupport left := by
          intro hleft
          exact hdisjoint v hleft hv
        simp [a, patchSupport, hnot])).1 hr

#print axioms Witnora.TC063ModelGluing.cnfHolds_congr_on_support
#print axioms Witnora.TC063ModelGluing.glue_two_disjoint_components

end Witnora.TC063ModelGluing
