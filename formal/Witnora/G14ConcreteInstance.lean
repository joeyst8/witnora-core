import Witnora.G14ConcreteBridge

/-!
# Concrete two-branch G14 -> G5 -> DIMACS UNSAT instance

Source formula: (x1 ∨ x2) ∧ (¬x1 ∨ x2) ∧ (¬x2).
Separator [1] has two branches, and each conditioned residual is
the contradictory pair [x2], [¬x2]. Both branches are certified by
the concrete closed G5 checker, without an external SAT oracle.
-/

namespace Witnora.G14ConcreteInstance

open Witnora.Concrete
open Witnora.G14ConcreteBridge
open Witnora.G5Extraction
open Witnora.ComponentPartition
open Witnora.Conditioning
open Witnora.SeparatorAssignments
open Witnora.SignedSerialization
open Witnora.SparseBridge
open Witnora.DIMACSDocument
open Witnora.DIMACSTokens

def sourceBytes : List Nat :=
  [112, 32, 99, 110, 102, 32, 50, 32, 51, 10, 49, 32, 50, 32, 48, 10, 45, 49, 32, 50, 32, 48, 10, 45, 50, 32, 48, 10]

def sourceTokens : List Int := [1, 2, 0, -1, 2, 0, -2, 0]
def rawClauses : List (List Int) := [[1, 2], [-1, 2], [-2]]

def residual : CNF := [[(2, true)], [(2, false)]]

def components (_branch : List (Nat × Bool)) : List CNF := [residual]
def selected (_branch : List (Nat × Bool)) : CNF := residual

def bound (_branch : List (Nat × Bool)) : Nat := 3

def rows (_branch : List (Nat × Bool)) : List Witnora.G5Trace.Row :=
  [⟨[2], true⟩, ⟨[2], false⟩]

def steps (_branch : List (Nat × Bool)) : List Witnora.G5Dag.XorRef :=
  [(0, 1)]

theorem document_passes :
    checkDocument sourceBytes sourceTokens = true := by
  decide

theorem stream_passes :
    checkStream sourceTokens rawClauses = true := by
  decide

theorem all_partitions_pass :
    ∀ branch ∈ enumerate [1],
      checkPartition
        (conditionCNF (fixedOf branch) (decodeCNF rawClauses))
        (components branch) = true := by
  intro branch hb
  have hcases : branch = [(1, false)] ∨ branch = [(1, true)] := by
    simpa [enumerate] using hb
  rcases hcases with hfalse | htrue
  · subst branch
    decide
  · subst branch
    decide

theorem all_selected_members :
    ∀ branch ∈ enumerate [1],
      selected branch ∈ components branch := by
  intro branch _
  simp [selected, components]

theorem all_g5_certificates_pass :
    ∀ branch ∈ enumerate [1],
      checkG5Closed (bound branch) (selected branch)
        (rows branch) (steps branch) = true := by
  intro branch _
  change checkG5Closed 3 residual
    [⟨[2], true⟩, ⟨[2], false⟩] [(0, 1)] = true
  decide

/-- Concrete kernel-checked nontrivial G14 branch composition:
    true input ASCII DIMACS -> exhaustive separator branches ->
    checked conditioned partitions -> selected G5 contradictions -> UNSAT. -/
theorem concrete_two_branch_g14_unsat :
    parseDocument sourceBytes = some (serialize rawClauses) ∧
    ¬ ∃ a, signedCNFHolds rawClauses a := by
  exact checked_ascii_dimacs_g14_unsat
    sourceBytes sourceTokens rawClauses document_passes stream_passes
    [1] components all_partitions_pass selected all_selected_members
    bound rows steps all_g5_certificates_pass

/-- Mutating a source clause cannot reuse the old DIMACS evidence. -/
theorem modified_document_rejected :
    checkDocument
      [112, 32, 99, 110, 102, 32, 50, 32, 51, 10, 49, 32, 50, 32, 48, 10, 45, 49, 32, 50, 32, 48, 10, 50, 32, 48, 10]
      sourceTokens = false := by
  decide

/-- Dropping one residual unit clause invalidates the partition. -/
theorem missing_residual_clause_rejected :
    checkPartition
      (conditionCNF (fixedOf [(1, false)]) (decodeCNF rawClauses))
      [[[(2, true)]]] = false := by
  decide

#print axioms Witnora.G14ConcreteInstance.all_partitions_pass
#print axioms Witnora.G14ConcreteInstance.all_g5_certificates_pass
#print axioms Witnora.G14ConcreteInstance.concrete_two_branch_g14_unsat

end Witnora.G14ConcreteInstance
