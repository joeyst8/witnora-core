import TC063PrimalGraphOwnership

set_option maxHeartbeats 2000000
set_option maxRecDepth 4096

/-!
  Executable graph-cut premise checker, instantiated to the 160 clauses
  of archived Dubois20. Var i in the DIMACS source is Fin 60 index i-1.
  The fixture parser / DIMACS byte-refinement boundary remains outside Lean.
-/

namespace Witnora.TC063.CheckedGraph

open Witnora.SeparatorAgreement
open Witnora.TC063.PrimalGraph

universe u

def edgePass {Var : Type u} (owner : Var → Option Bool)
    (l1 l2 : Literal Var) : Bool :=
  match owner l1.1, owner l2.1 with
  | some a, some b => a == b
  | _, _ => true

def checkNoCrossEdges {Var : Type u}
    (formula : CNF Var) (owner : Var → Option Bool) : Bool :=
  formula.all (fun c => c.all (fun l1 => c.all (edgePass owner l1)))

theorem checkNoCrossEdges_sound {Var : Type u}
    (formula : CNF Var) (owner : Var → Option Bool)
    (hcheck : checkNoCrossEdges formula owner = true) :
    NoCrossEdges formula owner := by
  intro x y hco a b hx hy
  obtain ⟨c, hc, ⟨l1, hl1, h1⟩, ⟨l2, hl2, h2⟩⟩ := hco
  have hclause :
      (c.all (fun l1 => c.all (edgePass owner l1))) = true :=
    (List.all_eq_true.mp hcheck) c hc
  have hfirst : (c.all (edgePass owner l1)) = true :=
    (List.all_eq_true.mp hclause) l1 hl1
  have hsecond : edgePass owner l1 l2 = true :=
    (List.all_eq_true.mp hfirst) l2 hl2
  have hsame : (a == b) = true := by
    simpa [edgePass, h1, h2, hx, hy] using hsecond
  cases a <;> cases b <;> simp_all

-- Full original CNF from the archived 40 groups × four clauses per group.
-- A Python fixture audit prevents generator/order/content drift.
def dubois20Clauses : CNF (Fin 60) := [
    [((40 : Fin 60), false), (1, false), (0, true)],
    [((40 : Fin 60), false), (0, false), (1, true)],
    [((1 : Fin 60), false), (0, false), (40, true)],
    [((0 : Fin 60), true), (1, true), (40, true)],
    [((39 : Fin 60), false), (38, false), (0, true)],
    [((39 : Fin 60), false), (0, false), (38, true)],
    [((38 : Fin 60), false), (0, false), (39, true)],
    [((0 : Fin 60), true), (38, true), (39, true)],
    [((41 : Fin 60), false), (2, false), (1, true)],
    [((41 : Fin 60), false), (1, false), (2, true)],
    [((2 : Fin 60), false), (1, false), (41, true)],
    [((1 : Fin 60), true), (2, true), (41, true)],
    [((42 : Fin 60), false), (3, false), (2, true)],
    [((42 : Fin 60), false), (2, false), (3, true)],
    [((3 : Fin 60), false), (2, false), (42, true)],
    [((2 : Fin 60), true), (3, true), (42, true)],
    [((43 : Fin 60), false), (4, false), (3, true)],
    [((43 : Fin 60), false), (3, false), (4, true)],
    [((4 : Fin 60), false), (3, false), (43, true)],
    [((3 : Fin 60), true), (4, true), (43, true)],
    [((44 : Fin 60), false), (5, false), (4, true)],
    [((44 : Fin 60), false), (4, false), (5, true)],
    [((5 : Fin 60), false), (4, false), (44, true)],
    [((4 : Fin 60), true), (5, true), (44, true)],
    [((45 : Fin 60), false), (6, false), (5, true)],
    [((45 : Fin 60), false), (5, false), (6, true)],
    [((6 : Fin 60), false), (5, false), (45, true)],
    [((5 : Fin 60), true), (6, true), (45, true)],
    [((46 : Fin 60), false), (7, false), (6, true)],
    [((46 : Fin 60), false), (6, false), (7, true)],
    [((7 : Fin 60), false), (6, false), (46, true)],
    [((6 : Fin 60), true), (7, true), (46, true)],
    [((47 : Fin 60), false), (8, false), (7, true)],
    [((47 : Fin 60), false), (7, false), (8, true)],
    [((8 : Fin 60), false), (7, false), (47, true)],
    [((7 : Fin 60), true), (8, true), (47, true)],
    [((48 : Fin 60), false), (9, false), (8, true)],
    [((48 : Fin 60), false), (8, false), (9, true)],
    [((9 : Fin 60), false), (8, false), (48, true)],
    [((8 : Fin 60), true), (9, true), (48, true)],
    [((49 : Fin 60), false), (10, false), (9, true)],
    [((49 : Fin 60), false), (9, false), (10, true)],
    [((10 : Fin 60), false), (9, false), (49, true)],
    [((9 : Fin 60), true), (10, true), (49, true)],
    [((50 : Fin 60), false), (11, false), (10, true)],
    [((50 : Fin 60), false), (10, false), (11, true)],
    [((11 : Fin 60), false), (10, false), (50, true)],
    [((10 : Fin 60), true), (11, true), (50, true)],
    [((51 : Fin 60), false), (12, false), (11, true)],
    [((51 : Fin 60), false), (11, false), (12, true)],
    [((12 : Fin 60), false), (11, false), (51, true)],
    [((11 : Fin 60), true), (12, true), (51, true)],
    [((52 : Fin 60), false), (13, false), (12, true)],
    [((52 : Fin 60), false), (12, false), (13, true)],
    [((13 : Fin 60), false), (12, false), (52, true)],
    [((12 : Fin 60), true), (13, true), (52, true)],
    [((53 : Fin 60), false), (14, false), (13, true)],
    [((53 : Fin 60), false), (13, false), (14, true)],
    [((14 : Fin 60), false), (13, false), (53, true)],
    [((13 : Fin 60), true), (14, true), (53, true)],
    [((54 : Fin 60), false), (15, false), (14, true)],
    [((54 : Fin 60), false), (14, false), (15, true)],
    [((15 : Fin 60), false), (14, false), (54, true)],
    [((14 : Fin 60), true), (15, true), (54, true)],
    [((55 : Fin 60), false), (16, false), (15, true)],
    [((55 : Fin 60), false), (15, false), (16, true)],
    [((16 : Fin 60), false), (15, false), (55, true)],
    [((15 : Fin 60), true), (16, true), (55, true)],
    [((56 : Fin 60), false), (17, false), (16, true)],
    [((56 : Fin 60), false), (16, false), (17, true)],
    [((17 : Fin 60), false), (16, false), (56, true)],
    [((16 : Fin 60), true), (17, true), (56, true)],
    [((57 : Fin 60), false), (18, false), (17, true)],
    [((57 : Fin 60), false), (17, false), (18, true)],
    [((18 : Fin 60), false), (17, false), (57, true)],
    [((17 : Fin 60), true), (18, true), (57, true)],
    [((59 : Fin 60), false), (58, false), (18, true)],
    [((59 : Fin 60), false), (18, false), (58, true)],
    [((58 : Fin 60), false), (18, false), (59, true)],
    [((18 : Fin 60), true), (58, true), (59, true)],
    [((57 : Fin 60), false), (20, false), (19, true)],
    [((57 : Fin 60), false), (19, false), (20, true)],
    [((20 : Fin 60), false), (19, false), (57, true)],
    [((19 : Fin 60), true), (20, true), (57, true)],
    [((59 : Fin 60), false), (58, false), (19, true)],
    [((59 : Fin 60), false), (19, false), (58, true)],
    [((58 : Fin 60), false), (19, false), (59, true)],
    [((19 : Fin 60), true), (58, true), (59, true)],
    [((56 : Fin 60), false), (21, false), (20, true)],
    [((56 : Fin 60), false), (20, false), (21, true)],
    [((21 : Fin 60), false), (20, false), (56, true)],
    [((20 : Fin 60), true), (21, true), (56, true)],
    [((55 : Fin 60), false), (22, false), (21, true)],
    [((55 : Fin 60), false), (21, false), (22, true)],
    [((22 : Fin 60), false), (21, false), (55, true)],
    [((21 : Fin 60), true), (22, true), (55, true)],
    [((54 : Fin 60), false), (23, false), (22, true)],
    [((54 : Fin 60), false), (22, false), (23, true)],
    [((23 : Fin 60), false), (22, false), (54, true)],
    [((22 : Fin 60), true), (23, true), (54, true)],
    [((53 : Fin 60), false), (24, false), (23, true)],
    [((53 : Fin 60), false), (23, false), (24, true)],
    [((24 : Fin 60), false), (23, false), (53, true)],
    [((23 : Fin 60), true), (24, true), (53, true)],
    [((52 : Fin 60), false), (25, false), (24, true)],
    [((52 : Fin 60), false), (24, false), (25, true)],
    [((25 : Fin 60), false), (24, false), (52, true)],
    [((24 : Fin 60), true), (25, true), (52, true)],
    [((51 : Fin 60), false), (26, false), (25, true)],
    [((51 : Fin 60), false), (25, false), (26, true)],
    [((26 : Fin 60), false), (25, false), (51, true)],
    [((25 : Fin 60), true), (26, true), (51, true)],
    [((50 : Fin 60), false), (27, false), (26, true)],
    [((50 : Fin 60), false), (26, false), (27, true)],
    [((27 : Fin 60), false), (26, false), (50, true)],
    [((26 : Fin 60), true), (27, true), (50, true)],
    [((49 : Fin 60), false), (28, false), (27, true)],
    [((49 : Fin 60), false), (27, false), (28, true)],
    [((28 : Fin 60), false), (27, false), (49, true)],
    [((27 : Fin 60), true), (28, true), (49, true)],
    [((48 : Fin 60), false), (29, false), (28, true)],
    [((48 : Fin 60), false), (28, false), (29, true)],
    [((29 : Fin 60), false), (28, false), (48, true)],
    [((28 : Fin 60), true), (29, true), (48, true)],
    [((47 : Fin 60), false), (30, false), (29, true)],
    [((47 : Fin 60), false), (29, false), (30, true)],
    [((30 : Fin 60), false), (29, false), (47, true)],
    [((29 : Fin 60), true), (30, true), (47, true)],
    [((46 : Fin 60), false), (31, false), (30, true)],
    [((46 : Fin 60), false), (30, false), (31, true)],
    [((31 : Fin 60), false), (30, false), (46, true)],
    [((30 : Fin 60), true), (31, true), (46, true)],
    [((45 : Fin 60), false), (32, false), (31, true)],
    [((45 : Fin 60), false), (31, false), (32, true)],
    [((32 : Fin 60), false), (31, false), (45, true)],
    [((31 : Fin 60), true), (32, true), (45, true)],
    [((44 : Fin 60), false), (33, false), (32, true)],
    [((44 : Fin 60), false), (32, false), (33, true)],
    [((33 : Fin 60), false), (32, false), (44, true)],
    [((32 : Fin 60), true), (33, true), (44, true)],
    [((43 : Fin 60), false), (34, false), (33, true)],
    [((43 : Fin 60), false), (33, false), (34, true)],
    [((34 : Fin 60), false), (33, false), (43, true)],
    [((33 : Fin 60), true), (34, true), (43, true)],
    [((42 : Fin 60), false), (35, false), (34, true)],
    [((42 : Fin 60), false), (34, false), (35, true)],
    [((35 : Fin 60), false), (34, false), (42, true)],
    [((34 : Fin 60), true), (35, true), (42, true)],
    [((41 : Fin 60), false), (36, false), (35, true)],
    [((41 : Fin 60), false), (35, false), (36, true)],
    [((36 : Fin 60), false), (35, false), (41, true)],
    [((35 : Fin 60), true), (36, true), (41, true)],
    [((40 : Fin 60), false), (37, false), (36, true)],
    [((40 : Fin 60), false), (36, false), (37, true)],
    [((37 : Fin 60), false), (36, false), (40, true)],
    [((36 : Fin 60), true), (37, true), (40, true)],
    [((39 : Fin 60), false), (38, false), (37, false)],
    [((39 : Fin 60), false), (37, true), (38, true)],
    [((38 : Fin 60), false), (37, true), (39, true)],
    [((37 : Fin 60), false), (38, true), (39, true)]
  ]

-- Component A zero-based: 0..8 and 29..48.
-- Component B zero-based: 10..27 and 49..59.
-- Separator: bit indexes 9 and 28 (DIMACS variables 10 and 29).
def duboisOwner (v : Fin 60) : Option Bool :=
  if v.val = 9 ∨ v.val = 28 then none
  else if v.val < 9 ∨ (29 ≤ v.val ∧ v.val ≤ 48) then some false
  else some true

def duboisFixed (s10 s29 : Bool) (v : Fin 60) : Option Bool :=
  if v.val = 9 then some s10
  else if v.val = 28 then some s29
  else none

-- The graph checker is evaluated by Lean's kernel reduction, not a native
-- evaluation oracle, on the entire clause fixture (1,440 ordered pairs).
theorem duboisGraphCheck :
    checkNoCrossEdges dubois20Clauses duboisOwner = true := by
  decide

theorem duboisGraphInvariant :
    NoCrossEdges dubois20Clauses duboisOwner :=
  checkNoCrossEdges_sound dubois20Clauses duboisOwner duboisGraphCheck

-- Because the domain is Fin 60, this quantifies over EVERY variable, not
-- just those visited by a selected residual clause.
theorem duboisOwnerComplete (s10 s29 : Bool) :
    AllUnassignedOwned (duboisFixed s10 s29) duboisOwner := by
  intro x hx
  by_cases hsep : x.val = 9 ∨ x.val = 28
  · rcases hsep with h10 | h29
    · simp [duboisFixed, h10] at hx
    · simp [duboisFixed, h29] at hx
  · by_cases hA : x.val < 9 ∨ (29 ≤ x.val ∧ x.val ≤ 48)
    · exact ⟨false, by simp [duboisOwner, hsep, hA]⟩
    · exact ⟨true, by simp [duboisOwner, hsep, hA]⟩

-- Each source clause has three distinct variables and at most one fixed
-- separator variable; none reduces to the empty clause.
theorem duboisNoEmptyResidual (s10 s29 : Bool) :
    ([] : Clause (Fin 60)) ∉ ReduceCNF (duboisFixed s10 s29) dubois20Clauses := by
  cases s10 <;> cases s29 <;> decide

-- For all four separator assignments, exact reduction + graph checking
-- formally imply a complete non-overlapping two-component ownership cover.
theorem duboisOwnedResidualCover (s10 s29 : Bool) :
    ∀ r, r ∈ ReduceCNF (duboisFixed s10 s29) dubois20Clauses →
      r ∈ OwnerComponent (ResidualOwner duboisOwner) false
            (ReduceCNF (duboisFixed s10 s29) dubois20Clauses) ∨
      r ∈ OwnerComponent (ResidualOwner duboisOwner) true
            (ReduceCNF (duboisFixed s10 s29) dubois20Clauses) :=
  graph_implies_complete_component_cover
    duboisGraphInvariant (duboisOwnerComplete s10 s29)
    (duboisNoEmptyResidual s10 s29)

-- The current Python recognizer (c=2,r=3) returns DIMACS variables 1 and
-- 38 as its first valid separator. Removing them yields one 56-variable
-- component and one two-variable component {39,40}. We kernel-check that
-- actual recognizer-shaped labeling separately from the balanced 29/29 cut.
def recognizedOwner (v : Fin 60) : Option Bool :=
  if v.val = 0 ∨ v.val = 37 then none
  else if v.val = 38 ∨ v.val = 39 then some true
  else some false

def recognizedFixed (s1 s38 : Bool) (v : Fin 60) : Option Bool :=
  if v.val = 0 then some s1
  else if v.val = 37 then some s38
  else none

theorem recognizedGraphCheck :
    checkNoCrossEdges dubois20Clauses recognizedOwner = true := by
  decide

theorem recognizedGraphInvariant :
    NoCrossEdges dubois20Clauses recognizedOwner :=
  checkNoCrossEdges_sound dubois20Clauses recognizedOwner recognizedGraphCheck

theorem recognizedOwnerComplete (s1 s38 : Bool) :
    AllUnassignedOwned (recognizedFixed s1 s38) recognizedOwner := by
  intro x hx
  by_cases hsep : x.val = 0 ∨ x.val = 37
  · rcases hsep with h1 | h38
    · simp [recognizedFixed, h1] at hx
    · simp [recognizedFixed, h38] at hx
  · by_cases hsmall : x.val = 38 ∨ x.val = 39
    · exact ⟨true, by simp only [recognizedOwner, if_neg hsep, if_pos hsmall]⟩
    · exact ⟨false, by simp only [recognizedOwner, if_neg hsep, if_neg hsmall]⟩

theorem recognizedNoEmptyResidual (s1 s38 : Bool) :
    ([] : Clause (Fin 60)) ∉
      ReduceCNF (recognizedFixed s1 s38) dubois20Clauses := by
  cases s1 <;> cases s38 <;> decide

theorem recognizedOwnedResidualCover (s1 s38 : Bool) :
    ∀ r, r ∈ ReduceCNF (recognizedFixed s1 s38) dubois20Clauses →
      r ∈ OwnerComponent (ResidualOwner recognizedOwner) false
            (ReduceCNF (recognizedFixed s1 s38) dubois20Clauses) ∨
      r ∈ OwnerComponent (ResidualOwner recognizedOwner) true
            (ReduceCNF (recognizedFixed s1 s38) dubois20Clauses) :=
  graph_implies_complete_component_cover
    recognizedGraphInvariant (recognizedOwnerComplete s1 s38)
    (recognizedNoEmptyResidual s1 s38)

end Witnora.TC063.CheckedGraph

#print axioms Witnora.TC063.CheckedGraph.duboisOwnedResidualCover
#print axioms Witnora.TC063.CheckedGraph.recognizedOwnedResidualCover
