import Witnora.G5Extraction
import Witnora.G5Dag

/-!
# Composition of checked XOR-CNF extraction and G5 DAG certificates

The two executable verifiers are connected here. A single explicit
representation lemma (sparseParity = parityVars on certified rows) remains
as the mathematical bridge between their interpretations. This assumption
must be discharged before the resulting checker is unconditional.
-/

namespace Witnora.G5Verified

open Witnora.G5Trace
open Witnora.G5Extraction
open Witnora.G5Dag
open Witnora.G5Certificate
open Witnora.Extraction
open Witnora.SparseParity

def checkG5 (cnf : Witnora.Concrete.CNF)
    (rows : List Row) (steps : List XorRef) : Bool :=
  checkInitialRows cnf rows && checkDagContradiction rows steps

/-- The original CNF is UNSAT when both executable checks pass and the
list-parity/sparse-parity representation refinement is available. -/
theorem checkG5_unsat_of_sparse_bridge
    (bound : Nat) (cnf : Witnora.Concrete.CNF)
    (rows : List Row) (steps : List XorRef)
    (hbridge : ∀ row, row ∈ rows → ∀ a : Nat → Bool,
      sparseParity bound row.coefficients a =
        parityVars row.coefficients a)
    (h : checkG5 cnf rows steps = true) :
    ¬ ∃ a, CNFHolds cnf a := by
  have hextract : checkInitialRows cnf rows = true := by
    have := h
    simp [checkG5] at this
    exact this.1
  have hdag : checkDagContradiction rows steps = true := by
    have := h
    simp [checkG5] at this
    exact this.2
  apply checkDagContradiction_unsat bound (CNFHolds cnf) rows steps
  · intro a hcnf row hr
    unfold AllHold RowHolds
    intro r hrmem
    rw [hbridge r hrmem a]
    exact checkInitialRows_sound cnf rows hextract a hcnf r hrmem
  · exact hdag

#print axioms Witnora.G5Verified.checkG5_unsat_of_sparse_bridge

end Witnora.G5Verified
