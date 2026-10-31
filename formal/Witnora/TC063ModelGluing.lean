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

/-- Arbitrarily many pairwise independent components can be satisfied
    simultaneously, preserving an arbitrary base assignment on all variables
    outside the union of their supports. -/
theorem glue_pairwise_components (parts : List CNF) :
    Independent parts →
    (∀ component ∈ parts, ∃ a : Nat → Bool, CNFHolds component a) →
    ∀ base : Nat → Bool,
      ∃ a : Nat → Bool,
        (∀ component ∈ parts, CNFHolds component a) ∧
        (∀ v, v ∉ (parts.map variableSupport).flatten → a v = base v) := by
  induction parts with
  | nil =>
      intro _ _ base
      refine ⟨base, ?_, ?_⟩
      · simp
      · simp
  | cons head tail ih =>
      intro hp hm base
      have hp' : List.Pairwise
          (fun left right : CNF =>
            ∀ v, v ∈ variableSupport left →
              v ∉ variableSupport right) (head :: tail) := hp
      obtain ⟨hhead, htail⟩ := List.pairwise_cons.mp hp'
      have hmhead : ∃ a, CNFHolds head a := hm head (by simp)
      obtain ⟨ah, hh⟩ := hmhead
      have hmtail : ∀ component ∈ tail,
          ∃ a : Nat → Bool, CNFHolds component a := by
        intro component hc
        exact hm component (by simp [hc])
      obtain ⟨aTail, ht, htbase⟩ := ih htail hmtail base
      let a := patchSupport (variableSupport head) ah aTail
      refine ⟨a, ?_, ?_⟩
      · intro component hc
        rcases List.mem_cons.mp hc with hEq | hcTail
        · subst component
          exact (cnfHolds_congr_on_support head ah a
            (by
              intro v hv
              simp [a, patchSupport, hv])).1 hh
        · have hdis : ∀ v ∈ variableSupport component,
              v ∉ variableSupport head := by
            intro v hv hbad
            exact (hhead component hcTail v hbad) hv
          exact (cnfHolds_congr_on_support component aTail a
            (by
              intro v hv
              simp [a, patchSupport, hdis v hv])).1
            (ht component hcTail)
      · intro v hv
        have hvhead : v ∉ variableSupport head := by
          intro hmem
          apply hv
          simp [hmem]
        have hvtail : v ∉ (tail.map variableSupport).flatten := by
          intro hmem
          apply hv
          simp [hmem]
        simp [a, patchSupport, hvhead, htbase v hvtail]

#print axioms Witnora.TC063ModelGluing.glue_pairwise_components

/-- A canonical total assignment extending any partial fixed assignment. -/
def baseOfFixed (fixed : Nat → Option Bool) : Nat → Bool :=
  fun v => (fixed v).getD false

theorem baseOfFixed_agrees (fixed : Nat → Option Bool) :
    Witnora.Conditioning.agreesWith fixed (baseOfFixed fixed) := by
  intro v b hv
  simp [baseOfFixed, hv]

/-- Pairwise independence plus absence of fixed variables in all residual
    components guarantees a simultaneously satisfying separator-consistent
    model. This uses actual list-level gluing, not an assumed constructor. -/
theorem glue_independent_unfixed_components
    (fixed : Nat → Option Bool) (parts : List CNF)
    (hi : Independent parts)
    (hunfixed : ∀ component ∈ parts,
      ∀ v ∈ variableSupport component, fixed v = none)
    (hmodels : ∀ component ∈ parts,
      ∃ a : Nat → Bool, CNFHolds component a) :
    ∃ a : Nat → Bool,
      Witnora.Conditioning.agreesWith fixed a ∧
      ∀ component ∈ parts, CNFHolds component a := by
  obtain ⟨a, hall, houtside⟩ :=
    glue_pairwise_components parts hi hmodels (baseOfFixed fixed)
  refine ⟨a, ?_, hall⟩
  intro v b hv
  have hnot : v ∉ (parts.map variableSupport).flatten := by
    intro hmem
    obtain ⟨support, hsupport, hvar⟩ := List.mem_flatten.mp hmem
    obtain ⟨component, hcomponent, heq⟩ := List.mem_map.mp hsupport
    subst support
    have hn := hunfixed component hcomponent v hvar
    rw [hv] at hn
    cases hn
  rw [houtside v hnot]
  exact baseOfFixed_agrees fixed v b hv

#print axioms Witnora.TC063ModelGluing.glue_independent_unfixed_components

end Witnora.TC063ModelGluing
