import Init

/-!
# Abstract separator decomposition: first Lean formalization gate

An *abstract* decomposition contract is supplied as hypothesis `decomposes`.
This file formally proves existential SAT lifting and UNSAT coverage from that
contract. It does not establish that Witnora's Python decomposition meets the
contract, or verify G5, runtime, parsimonious counting, or TC-063 as a whole.

`S`: separator assignments.
`I`: residual component identifiers.
`R i`: assignments to residual component i.
`F s b`: satisfaction of the original CNF by the assembled assignment.
`C s i x`: satisfaction of component i after fixing separator s.

The dependent product `(i : I) → R i` models separately assigned components;
a future certificate theorem must establish these components are variable-disjoint
and cover all residual variables, with a correct assembly/restriction operation.
-/

universe u v w

namespace Witnora.Separator

variable {S : Type u} {I : Type v} {R : I → Type w}

def Decomposes
    (F : S → ((i : I) → R i) → Prop)
    (C : S → (i : I) → R i → Prop) : Prop :=
  ∀ s b, F s b ↔ ∀ i, C s i (b i)

/-- SAT iff some separator branch has a model for each independent component,
assuming an exact decomposition contract. -/
theorem sat_iff_components
    (F : S → ((i : I) → R i) → Prop)
    (C : S → (i : I) → R i → Prop)
    (decomposes : Decomposes F C) :
    (∃ s b, F s b) ↔ (∃ s, ∀ i, ∃ x, C s i x) := by
  classical
  constructor
  · intro h
    obtain ⟨s, b, hb⟩ := h
    exact ⟨s, fun i => ⟨b i, (decomposes s b).mp hb i⟩⟩
  · intro h
    obtain ⟨s, hs⟩ := h
    let b : (i : I) → R i := fun i => Classical.choose (hs i)
    refine ⟨s, b, ?_⟩
    apply (decomposes s b).mpr
    intro i
    exact Classical.choose_spec (hs i)

/-- UNSAT iff every separator branch contains a component with no model.
This uses classical logic, as does the finite Boolean instance application. -/
theorem unsat_iff_cover
    (F : S → ((i : I) → R i) → Prop)
    (C : S → (i : I) → R i → Prop)
    (decomposes : Decomposes F C) :
    (¬ ∃ s b, F s b) ↔ (∀ s, ∃ i, ∀ x, ¬ C s i x) := by
  classical
  constructor
  · intro hunsat s
    apply Classical.byContradiction
    intro hcover
    apply hunsat
    apply (sat_iff_components F C decomposes).mpr
    refine ⟨s, ?_⟩
    intro i
    apply Classical.byContradiction
    intro hcomponent
    apply hcover
    refine ⟨i, ?_⟩
    intro x hx
    exact hcomponent ⟨x, hx⟩
  · intro hcover hsat
    obtain ⟨s, hs⟩ := (sat_iff_components F C decomposes).mp hsat
    obtain ⟨i, hi⟩ := hcover s
    obtain ⟨x, hx⟩ := hs i
    exact hi x hx

#print axioms Witnora.Separator.sat_iff_components
#print axioms Witnora.Separator.unsat_iff_cover

end Witnora.Separator
