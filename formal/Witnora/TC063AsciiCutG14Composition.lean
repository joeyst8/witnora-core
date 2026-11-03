import Witnora.TC063AsciiSourceVertexCuts
import Witnora.G14ConcreteBridge

/-!
# TC-063: checked source-ASCII separator + G14/G5 UNSAT composition

This theorem combines three independently checked boundaries:
1. actual ASCII DIMACS bytes are parsed to exactly the supplied CNF;
2. the claimed selected two-vertex separator is genuine for that CNF;
3. each enumerated separator branch has a checked conditioned partition
   and a checked G5 contradiction certificate for a selected component.

Successful premises imply UNSAT of the supplied signed source clauses.
They do *not* establish that a generic input has a two-cut or that Python
can always discover/provide a successful certificate for each branch.
-/

namespace Witnora.TC063AsciiCutG14Composition

open Witnora.TC063AsciiSourceVertexCuts
open Witnora.TC063SourceVertexCuts
open Witnora.TC063VertexCouplingFiniteOracle
open Witnora.G14DFSSeenEnqueue
open Witnora.Conditioning
open Witnora.ComponentPartition

/-- A real source-ASCII separator and a complete collection of checked
    G14/G5 branch witnesses together establish a contradiction for every
    satisfying assignment of the source's exact signed clauses. -/
theorem checked_ascii_two_cut_g14_unsat
    (source : List Nat) (tokens : List Int)
    (raw : List (List Int)) (claimed : List (Nat × Nat))
    (hAsciiCut : checkAsciiTwoCuts source tokens raw claimed = true)
    (pair : Nat × Nat) (hClaimed : pair ∈ claimed)
    (components : List (Nat × Bool) → List Witnora.Concrete.CNF)
    (hpart : ∀ branch ∈ Witnora.SeparatorAssignments.enumerate [pair.1, pair.2],
      checkPartition
        (conditionCNF (Witnora.SeparatorAssignments.fixedOf branch)
          (Witnora.SignedSerialization.decodeCNF raw))
        (components branch) = true)
    (selected : List (Nat × Bool) → Witnora.Concrete.CNF)
    (hselected : ∀ branch ∈ Witnora.SeparatorAssignments.enumerate [pair.1, pair.2],
      selected branch ∈ components branch)
    (bound : List (Nat × Bool) → Nat)
    (rows : List (Nat × Bool) → List Witnora.G5Trace.Row)
    (steps : List (Nat × Bool) → List Witnora.G5Dag.XorRef)
    (hcert : ∀ branch ∈ Witnora.SeparatorAssignments.enumerate [pair.1, pair.2],
      Witnora.G5Extraction.checkG5Closed (bound branch) (selected branch)
        (rows branch) (steps branch) = true) :
    Witnora.DIMACSDocument.parseDocument source =
      some (Witnora.DIMACSTokens.serialize raw) ∧
    residualComponentCount
      (canonicalSourceVertices (Witnora.SignedSerialization.decodeCNF raw))
      (clauseNeighbors (Witnora.SignedSerialization.decodeCNF raw))
      [pair.1, pair.2] > 1 ∧
    ¬ ∃ a, Witnora.SignedSerialization.signedCNFHolds raw a := by
  obtain ⟨hDoc, hStream, hSigned⟩ :=
    checked_ascii_parts source tokens raw claimed hAsciiCut
  have hBridge :=
    Witnora.G14ConcreteBridge.checked_ascii_dimacs_g14_unsat
      source tokens raw hDoc hStream [pair.1, pair.2]
      components hpart selected hselected bound rows steps hcert
  exact ⟨hBridge.1,
    checked_signed_pair_is_source_cut raw claimed hSigned pair hClaimed,
    hBridge.2⟩

#print axioms Witnora.TC063AsciiCutG14Composition.checked_ascii_two_cut_g14_unsat

end Witnora.TC063AsciiCutG14Composition
