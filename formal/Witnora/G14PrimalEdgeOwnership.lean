import Witnora.G14ComponentRouting

/-!
# G14 graph-edge labels imply sound residual component ownership

A primal-graph edge connects every pair of variables appearing in one
source clause. Once component labels are constant across nonseparator
edges, no conditioned residual clause can mix two component labels.

The result is universal in source CNF and separator. It isolates the
still-open correspondence between Python's DFS component labeling and
this graph-edge invariant.
-/

namespace Witnora.G14PrimalEdgeOwnership

open Witnora.Concrete
open Witnora.Conditioning
open Witnora.G5Extraction

/-- Literal membership of the conditioned clause is inherited from the
    exact original clause, even across early satisfaction exits. -/
theorem conditionClause_literals_from_source
    (fixed : Nat → Option Bool) (source residual : List Literal)
    (h : conditionClause fixed source = some residual) :
    ∀ lit ∈ residual, lit ∈ source := by
  induction source generalizing residual with
  | nil =>
      simp [conditionClause] at h
      subst residual
      simp
  | cons head tail ih =>
      cases hf : fixed head.1 with
      | none =>
          cases ht : conditionClause fixed tail with
          | none =>
              simp [conditionClause, hf, ht] at h
          | some reduced =>
              simp [conditionClause, hf, ht] at h
              cases h
              intro lit hm
              rcases List.mem_cons.mp hm with heq | htail
              · subst lit
                simp
              · exact List.mem_cons_of_mem _ (ih reduced ht lit htail)
      | some b =>
          by_cases hs : (if head.2 then b else !b) = true
          · simp [conditionClause, hf, hs] at h
          · have hsfalse : (if head.2 then b else !b) = false := by
              cases hx : (if head.2 then b else !b) <;> simp_all
            have htail : conditionClause fixed tail = some residual := by
              simpa [conditionClause, hf, hsfalse] using h
            intro lit hm
            exact List.mem_cons_of_mem _ (ih residual htail lit hm)

/-- A source primal edge is witnessed by a real source clause containing
    both variable IDs (including the u=v case). -/
def SourceEdge (source : CNF) (u v : Nat) : Prop :=
  ∃ clause ∈ source,
    u ∈ clause.map Prod.fst ∧ v ∈ clause.map Prod.fst

/-- Every recorded primal edge outside the separator has one label.
    This is the exact DFS-connected-component invariant to establish
    for the production Python graph builder. -/
def EdgeConsistent (source : CNF) (separator : List Nat)
    (componentOf : Nat → Nat) : Prop :=
  ∀ u v, SourceEdge source u v →
    u ∉ separator → v ∉ separator →
      componentOf u = componentOf v

/-- A source-clause pair is always a genuine primal edge. -/
theorem literals_form_source_edge
    (source : CNF) (clause : List Literal)
    (hclause : clause ∈ source)
    (u v : Literal)
    (hu : u ∈ clause) (hv : v ∈ clause) :
    SourceEdge source u.1 v.1 := by
  refine ⟨clause, hclause, ?_, ?_⟩
  · exact List.mem_map.mpr ⟨u, hu, rfl⟩
  · exact List.mem_map.mpr ⟨v, hv, rfl⟩

/-- No two variables surviving in one conditioned residual clause can
    be assigned to different nonseparator components, on *any* CNF. -/
theorem conditioned_residual_has_one_component
    (source : CNF) (separator : List Nat)
    (componentOf : Nat → Nat)
    (hconsistent : EdgeConsistent source separator componentOf)
    (fixed : Nat → Option Bool)
    (clause residual : List Literal)
    (hsource : clause ∈ source)
    (hcondition : conditionClause fixed clause = some residual)
    (u v : Literal) (hu : u ∈ residual) (hv : v ∈ residual)
    (hunsep : u.1 ∉ separator) (hvnsep : v.1 ∉ separator) :
    componentOf u.1 = componentOf v.1 := by
  have hsubset := conditionClause_literals_from_source
    fixed clause residual hcondition
  have hedge := literals_form_source_edge source clause hsource
    u v (hsubset u hu) (hsubset v hv)
  exact hconsistent u.1 v.1 hedge hunsep hvnsep

/-- Anchor on any surviving nonseparator literal: all remaining
    nonseparator literals have precisely its component owner. -/
theorem residual_owner_from_anchor
    (source : CNF) (separator : List Nat)
    (componentOf : Nat → Nat)
    (hconsistent : EdgeConsistent source separator componentOf)
    (fixed : Nat → Option Bool)
    (clause residual : List Literal)
    (hsource : clause ∈ source)
    (hcondition : conditionClause fixed clause = some residual)
    (anchor : Literal) (hanchor : anchor ∈ residual)
    (hanchorUnsep : anchor.1 ∉ separator) :
    ∀ lit ∈ residual, lit.1 ∉ separator →
      componentOf lit.1 = componentOf anchor.1 := by
  intro lit hlit hunsep
  exact conditioned_residual_has_one_component
    source separator componentOf hconsistent fixed
    clause residual hsource hcondition lit anchor
    hlit hanchor hunsep hanchorUnsep

#print axioms Witnora.G14PrimalEdgeOwnership.conditionClause_literals_from_source
#print axioms Witnora.G14PrimalEdgeOwnership.conditioned_residual_has_one_component

end Witnora.G14PrimalEdgeOwnership
