import SeparatorAgreement

/-!
  TC-063 G14 generic primal-graph → residual-component ownership.

  Unlike a component-classification assumption, this module derives clause
  ownership from an explicitly checked no-cross-edges graph invariant.
  It works for *every* finite list CNF over *any* variable type, separator
  assignment and two-way component labeling. Empty reduced clauses remain
  explicit UNSAT witnesses rather than being silently classified/dropped.

  This is a theorem about the Lean graph invariant, not yet a verification
  of the Python primal-graph builder or connected-components algorithm.
-/

namespace Witnora.TC063.PrimalGraph

open Witnora.SeparatorAgreement

universe u
variable {Var : Type u}

-- Exact (unweighted) primal-graph edge construction from source clauses.
def CoOccurs (formula : CNF Var) (x y : Var) : Prop :=
  ∃ c, c ∈ formula ∧
    (∃ lit, lit ∈ c ∧ lit.1 = x) ∧
    (∃ lit, lit ∈ c ∧ lit.1 = y)

-- This is the graph-separator invariant: no surviving primal-graph edge
-- connects vertices of different assigned components.
def NoCrossEdges (formula : CNF Var) (owner : Var → Option Bool) : Prop :=
  ∀ x y, CoOccurs formula x y →
    ∀ a b, owner x = some a → owner y = some b → a = b

-- Every *unassigned* variable is classified into one of the two residual
-- components. Assigned separator variables need no owner.
def AllUnassignedOwned (fixed : Var → Option Bool)
    (owner : Var → Option Bool) : Prop :=
  ∀ x, fixed x = none → ∃ b, owner x = some b

theorem reduced_member_in_source
    {fixed : Var → Option Bool} {c r : Clause Var}
    (hreduce : ReduceClause fixed c = some r)
    {lit : Literal Var} (hmem : lit ∈ r) : lit ∈ c := by
  have heq : r = ResidualClause fixed c :=
    (reduceClause_some_characterization hreduce).2
  have hfilter : lit ∈ ResidualClause fixed c := by
    rw [← heq]
    exact hmem
  exact (List.mem_filter.mp hfilter).1

theorem reduced_member_unassigned
    {fixed : Var → Option Bool} {c r : Clause Var}
    (hreduce : ReduceClause fixed c = some r)
    {lit : Literal Var} (hmem : lit ∈ r) : fixed lit.1 = none := by
  have heq : r = ResidualClause fixed c :=
    (reduceClause_some_characterization hreduce).2
  have hfilter : lit ∈ ResidualClause fixed c := by
    rw [← heq]
    exact hmem
  have hnone : (fixed lit.1).isNone = true :=
    (List.mem_filter.mp hfilter).2
  cases h : fixed lit.1 with
  | none => exact h
  | some b => simp [h] at hnone

-- The graph invariant proves all literals in any surviving clause with
-- owners belong to the SAME component. No ownership assumption on the
-- clause itself is needed.
theorem reduced_clause_no_cross
    {formula : CNF Var} {owner : Var → Option Bool}
    {fixed : Var → Option Bool} {c r : Clause Var}
    (hgraph : NoCrossEdges formula owner)
    (hc : c ∈ formula) (hreduce : ReduceClause fixed c = some r)
    {litA litB : Literal Var} (ha : litA ∈ r) (hb : litB ∈ r)
    {a b : Bool} (hoa : owner litA.1 = some a)
    (hob : owner litB.1 = some b) : a = b := by
  have hco : CoOccurs formula litA.1 litB.1 :=
    ⟨c, hc,
      ⟨litA, reduced_member_in_source hreduce ha, rfl⟩,
      ⟨litB, reduced_member_in_source hreduce hb, rfl⟩⟩
  exact hgraph litA.1 litB.1 hco a b hoa hob

-- Canonical owner: the component of the first surviving literal.
-- An empty residual clause has no owner, intentionally.
def ResidualOwner (owner : Var → Option Bool) : Clause Var → Option Bool
  | [] => none
  | lit :: _ => owner lit.1

-- Nonempty surviving clauses are classified, and EVERY surviving literal
-- agrees with that owner. Empty clauses are dealt with separately.
theorem nonempty_reduced_clause_owned
    {formula : CNF Var} {owner : Var → Option Bool}
    {fixed : Var → Option Bool} {c r : Clause Var}
    (hgraph : NoCrossEdges formula owner)
    (hcovered : AllUnassignedOwned fixed owner)
    (hc : c ∈ formula) (hreduce : ReduceClause fixed c = some r)
    (hnonempty : r ≠ []) :
    ∃ b, ResidualOwner owner r = some b ∧
      ∀ lit, lit ∈ r → owner lit.1 = some b := by
  cases r with
  | nil => exact False.elim (hnonempty rfl)
  | cons head tail =>
    have hhead : head ∈ head :: tail := by simp
    have hheadNone : fixed head.1 = none :=
      reduced_member_unassigned hreduce hhead
    obtain ⟨b, hb⟩ := hcovered head.1 hheadNone
    refine ⟨b, ?_, ?_⟩
    · simpa [ResidualOwner] using hb
    · intro lit hmem
      have hfree : fixed lit.1 = none :=
        reduced_member_unassigned hreduce hmem
      obtain ⟨b', hb'⟩ := hcovered lit.1 hfree
      have hsame : b = b' :=
        reduced_clause_no_cross hgraph hc hreduce hhead hmem hb hb'
      simpa [← hsame] using hb'

-- A constructive total decision for every output clause: either the empty
-- contradiction, or a unique component owner shared by all its literals.
theorem every_reduced_clause_classified_or_empty
    {formula : CNF Var} {owner : Var → Option Bool}
    {fixed : Var → Option Bool}
    (hgraph : NoCrossEdges formula owner)
    (hcovered : AllUnassignedOwned fixed owner) :
    ∀ r, r ∈ ReduceCNF fixed formula →
      r = [] ∨
      ∃ b, ResidualOwner owner r = some b ∧
        ∀ lit, lit ∈ r → owner lit.1 = some b := by
  intro r hr
  by_cases hempty : r = []
  · exact Or.inl hempty
  · obtain ⟨c, hc, hreduce⟩ := List.mem_filterMap.mp hr
    exact Or.inr (nonempty_reduced_clause_owned
      hgraph hcovered hc hreduce hempty)

-- An empty reduced clause is a contradiction for every total assignment.
theorem empty_reduced_clause_unsat
    {fixed : Var → Option Bool} {formula : CNF Var}
    (hempty : ([] : Clause Var) ∈ ReduceCNF fixed formula) :
    ¬ ∃ global : Assignment Var, CNFSat global (ReduceCNF fixed formula) := by
  rintro ⟨global, hsat⟩
  obtain ⟨lit, hmem, _⟩ := hsat [] hempty
  cases hmem

-- When no empty contradiction exists, component ownership is complete and
-- can be plugged into the existing G14 owner-partition / SAT-lifting rules.
theorem graph_implies_complete_component_cover
    {formula : CNF Var} {owner : Var → Option Bool}
    {fixed : Var → Option Bool}
    (hgraph : NoCrossEdges formula owner)
    (hcovered : AllUnassignedOwned fixed owner)
    (hnoempty : ([] : Clause Var) ∉ ReduceCNF fixed formula) :
    ∀ r, r ∈ ReduceCNF fixed formula →
      r ∈ OwnerComponent (ResidualOwner owner) false
            (ReduceCNF fixed formula) ∨
      r ∈ OwnerComponent (ResidualOwner owner) true
            (ReduceCNF fixed formula) := by
  apply ownedComponent_cover
  intro r hr
  have hcase := every_reduced_clause_classified_or_empty hgraph hcovered r hr
  rcases hcase with he | ⟨b, hb, _⟩
  · exact False.elim (hnoempty (he ▸ hr))
  · exact ⟨b, hb⟩

end Witnora.TC063.PrimalGraph

#print axioms Witnora.TC063.PrimalGraph.graph_implies_complete_component_cover
