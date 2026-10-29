import Witnora.Concrete

/-!
# CNF encoding of one forbidden assignment

The full canonical XOR-to-CNF encoding consists of forbidden assignments:
each assignment with the wrong parity contributes one clause rejecting exactly
that assignment. This file establishes the clause-level equivalence for all
variable IDs and assignments. Composition into an exact XOR-CNF extraction
theorem still requires completeness of the forbidden-assignment family.
-/

namespace Witnora.Extraction

open Witnora.Concrete

def forbidClause (fixed : List (Nat × Bool)) : List Literal :=
  fixed.map (fun p => (p.1, !p.2))

/-- The clause that forbids a fixed assignment is true precisely when at
least one of those variable values differs from the assignment. -/
theorem forbidClause_true (bits : List Bool) (fixed : List (Nat × Bool)) :
    (forbidClause fixed).any (litTrue bits) = !(agrees bits fixed) := by
  induction fixed with
  | nil => rfl
  | cons p tail ih =>
    rcases p with ⟨v, value⟩
    simp only [forbidClause, List.map_cons, List.any_cons,
      agrees, List.all_cons, litTrue, ih]
    cases hb : readVar bits v <;>
      cases hv : value <;>
      cases ht : agrees bits tail <;>
      decide

#print axioms Witnora.Extraction.forbidClause_true

end Witnora.Extraction
