import Witnora.G14PrimalEdgeOwnership

/-!
# Proof-producing G14 DFS component label acceptance

The production Python DFS provides component membership. Lean checks
directly that each nonseparator variable is labeled and that no source
primal edge crosses component labels. These checks are universal in the
size and shape of the source CNF, and compose with the previously proved
unique-residual-owner theorem.

The checker verifies a supplied DFS result; proving CPython DFS always
produces such a result is a separate refinement obligation.
-/

namespace Witnora.G14DFSLabelCheck

open Witnora.Concrete
open Witnora.FiniteXor
open Witnora.G14PrimalEdgeOwnership

def nonseparatorLiterals (separator : List Nat)
    (clause : List Literal) : List Literal :=
  clause.filter (fun lit => decide (lit.1 ∉ separator))

/-- Enumerate every pair in each source clause, including repeated
    variables and diagonal pairs; enforce the graph label invariant. -/
def checkClauseEdgeLabels (separator : List Nat)
    (componentOf : Nat → Nat) (clause : List Literal) : Bool :=
  let remaining := nonseparatorLiterals separator clause
  remaining.all (fun u =>
    remaining.all (fun v => decide (componentOf u.1 = componentOf v.1)))

def checkGraphEdgeLabels (source : CNF) (separator : List Nat)
    (componentOf : Nat → Nat) : Bool :=
  source.all (checkClauseEdgeLabels separator componentOf)

/-- If the executable checker accepts, every nonseparator primal edge
    has consistent component labels. -/
theorem checkGraphEdgeLabels_sound
    (source : CNF) (separator : List Nat)
    (componentOf : Nat → Nat)
    (hcheck : checkGraphEdgeLabels source separator componentOf = true) :
    EdgeConsistent source separator componentOf := by
  intro u v hedge hunsep hvnsep
  obtain ⟨clause, hc, hu, hv⟩ := hedge
  obtain ⟨lu, hlu, heu⟩ := List.mem_map.mp hu
  obtain ⟨lv, hlv, hev⟩ := List.mem_map.mp hv
  have huvar : lu.1 = u := by simpa using heu
  have hvvar : lv.1 = v := by simpa using hev
  have hlu : lu ∈ nonseparatorLiterals separator clause := by
    apply List.mem_filter.mpr
    refine ⟨hlu, ?_⟩
    simp [huvar, hunsep]
  have hlv : lv ∈ nonseparatorLiterals separator clause := by
    apply List.mem_filter.mpr
    refine ⟨hlv, ?_⟩
    simp [hvvar, hvnsep]
  have hclause := List.all_eq_true.mp hcheck clause hc
  have hfirst := List.all_eq_true.mp hclause lu hlu
  have hsecond := List.all_eq_true.mp hfirst lv hlv
  have heq : componentOf lu.1 = componentOf lv.1 := by
    simpa using hsecond
  simpa [huvar, hvvar] using heq

/-- Every nonseparator source variable must appear in Python's supplied
    list of labeled variables. Otherwise an incomplete component table
    could pass the edge-only test vacuously. -/
def checkAllVariablesLabeled (source : CNF)
    (separator labeled : List Nat) : Bool :=
  source.all (fun clause =>
    clause.all (fun lit =>
      decide (lit.1 ∈ separator) || decide (lit.1 ∈ labeled)))

theorem checkAllVariablesLabeled_sound
    (source : CNF) (separator labeled : List Nat)
    (h : checkAllVariablesLabeled source separator labeled = true)
    (clause : List Literal) (hc : clause ∈ source)
    (lit : Literal) (hlit : lit ∈ clause)
    (hnsep : lit.1 ∉ separator) :
    lit.1 ∈ labeled := by
  have hclause := List.all_eq_true.mp h clause hc
  have hline := List.all_eq_true.mp hclause lit hlit
  have hsep : decide (lit.1 ∈ separator) = false := by
    simp [hnsep]
  simpa [checkAllVariablesLabeled, hsep] using hline

/-- A source passing the label checks cannot have a conditioned residual
    clause whose nonseparator literals cross component IDs. -/
theorem checked_labels_residual_unique
    (source : CNF) (separator : List Nat)
    (componentOf : Nat → Nat)
    (hcheck : checkGraphEdgeLabels source separator componentOf = true)
    (fixed : Nat → Option Bool)
    (clause residual : List Literal)
    (hsource : clause ∈ source)
    (hcondition : Witnora.Conditioning.conditionClause fixed clause =
      some residual)
    (u v : Literal) (hu : u ∈ residual) (hv : v ∈ residual)
    (hunsep : u.1 ∉ separator) (hvnsep : v.1 ∉ separator) :
    componentOf u.1 = componentOf v.1 := by
  exact conditioned_residual_has_one_component
    source separator componentOf
    (checkGraphEdgeLabels_sound source separator componentOf hcheck)
    fixed clause residual hsource hcondition
    u v hu hv hunsep hvnsep

/-- Explicit adversarial rejection: u and v co-occur, but are
    dishonestly assigned to different components. -/
example :
    checkGraphEdgeLabels
      [[(1, true), (2, false)]] []
      (fun v => v) = false := by decide

example :
    checkGraphEdgeLabels
      [[(1, true), (2, false)]] [1]
      (fun v => v) = true := by decide

#print axioms Witnora.G14DFSLabelCheck.checkGraphEdgeLabels_sound
#print axioms Witnora.G14DFSLabelCheck.checkAllVariablesLabeled_sound
#print axioms Witnora.G14DFSLabelCheck.checked_labels_residual_unique

end Witnora.G14DFSLabelCheck
