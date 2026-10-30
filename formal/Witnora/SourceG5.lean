import Witnora.CNFSorted
import Witnora.SparseBridge

/-!
# Source signed-CNF to G5 UNSAT composition

This bridges the canonicalized *signed clause data* to a verified G5
contradiction. The original signed clauses need not be sorted, unique, or
tautology-free. It does NOT prove that an external Python/DIMACS lexer
produces this list, nor does it claim G5 completeness.
-/

namespace Witnora.SourceG5

open Witnora.Concrete
open Witnora.CNFSorted
open Witnora.SignedSerialization
open Witnora.SparseBridge
open Witnora.G5Trace
open Witnora.G5Dag

/-- A closed checker for source signed clauses and an indexed G5 DAG. -/
def checkRawG5 (bound : Nat) (raw : List (List Int))
    (rows : List Row) (steps : List XorRef) : Bool :=
  checkG5Closed bound (canonicalize (decodeCNF raw)) rows steps

/-- An accepted contradiction proves UNSAT for the original signed CNF,
not merely for its canonical representation. -/
theorem checkRawG5_unsat (bound : Nat) (raw : List (List Int))
    (rows : List Row) (steps : List XorRef)
    (h : checkRawG5 bound raw rows steps = true) :
    ¬ ∃ a, signedCNFHolds raw a := by
  intro ⟨a, ha⟩
  have hclosed : checkG5Closed bound (canonicalize (decodeCNF raw))
      rows steps = true := h
  have hun := checkG5Closed_unsat bound (canonicalize (decodeCNF raw))
    rows steps hclosed
  apply hun
  refine ⟨a, ?_⟩
  apply (canonicalize_correct (decodeCNF raw) a).mpr
  exact (signedCNFHolds_iff raw a).mp ha

#print axioms Witnora.SourceG5.checkRawG5_unsat

end Witnora.SourceG5
