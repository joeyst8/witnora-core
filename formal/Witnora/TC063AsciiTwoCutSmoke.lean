import Witnora.TC063AsciiCutG14Composition

/-!
# A fully checked concrete *smoke fixture* for TC-063's proof architecture

This deliberately small UNSAT formula has a four-cycle primal graph,
two genuine opposite-vertex cuts, and contradictory unit clauses x2 and ¬x2.
It is NOT a historical target instance or a proof of the full TC-063 family
theorem.  It witnesses that the actual ASCII-document, structural-cut,
four-branch G14 partition, and G5 contradiction interfaces compose in Lean.
The fixture's exact source bytes live in
fixtures/tc063_ascii_two_cut_unsat_smoke.cnf and are checked in CI against
the literal below so later file changes cannot silently detach this proof.
-/

namespace Witnora.TC063AsciiTwoCutSmoke

open Witnora.Concrete
open Witnora.Conditioning
open Witnora.ComponentPartition
open Witnora.SeparatorAssignments
open Witnora.SignedSerialization
open Witnora.SparseBridge
open Witnora.TC063AsciiSourceVertexCuts
open Witnora.TC063AsciiCutG14Composition
open Witnora.TC063SourceVertexCuts
open Witnora.TC063VertexCouplingFiniteOracle
open Witnora.G14DFSSeenEnqueue

set_option maxRecDepth 8192
set_option maxHeartbeats 8000000

def smokeSource : List Nat :=
  [99, 32, 116, 99, 48, 54, 51, 32, 115, 116, 114, 117, 99, 116, 117, 114, 97, 108, 45, 97, 110, 100, 45, 117, 110, 115, 97, 116, 32, 99, 111, 109, 112, 111, 115, 105, 116, 105, 111, 110, 32, 115, 109, 111, 107, 101, 59, 32, 110, 111, 116, 32, 116, 104, 101, 32, 102, 117, 108, 108, 32, 84, 67, 45, 48, 54, 51, 32, 102, 97, 109, 105, 108, 121, 32, 116, 104, 101, 111, 114, 101, 109, 10, 112, 32, 99, 110, 102, 32, 52, 32, 54, 10, 49, 32, 50, 32, 48, 10, 50, 32, 51, 32, 48, 10, 51, 32, 52, 32, 48, 10, 49, 32, 52, 32, 48, 10, 50, 32, 48, 10, 45, 50, 32, 48, 10]

def smokeRaw : List (List Int) :=
  [[1, 2], [2, 3], [3, 4], [1, 4], [2], [-2]]

def smokeTokens : List Int :=
  [1, 2, 0, 2, 3, 0, 3, 4, 0, 1, 4, 0, 2, 0, -2, 0]

def smokeClaims : List (Nat × Nat) :=
  [(1, 3), (2, 4)]

def smokeResidual (branch : List (Nat × Bool)) : CNF :=
  conditionCNF (fixedOf branch) (decodeCNF smokeRaw)

def smokeComponents (branch : List (Nat × Bool)) : List CNF :=
  [smokeResidual branch]

def smokeSelected (branch : List (Nat × Bool)) : CNF :=
  smokeResidual branch

def smokeRows : List Witnora.G5Trace.Row :=
  [⟨[2], true⟩, ⟨[2], false⟩]

def smokeSteps : List Witnora.G5Dag.XorRef :=
  [(0, 1)]

example : checkAsciiTwoCuts smokeSource smokeTokens smokeRaw smokeClaims =
    true := by decide

/-- Every residual clause is accounted for exactly; we deliberately
    use the whole residual as a one-component partition for this smoke. -/
theorem smokePartitionsAccepted :
    ∀ branch ∈ enumerate [1, 3],
      checkPartition (smokeResidual branch)
        (smokeComponents branch) = true := by
  intro branch _
  simp [smokeComponents, checkPartition]

theorem smokeSelectedAccepted :
    ∀ branch ∈ enumerate [1, 3],
      smokeSelected branch ∈ smokeComponents branch := by
  intro branch _
  simp [smokeSelected, smokeComponents]

/-- The independent source unit clauses x2 and ¬x2 survive all four
    assignments to the genuine graph separator (x1,x3). -/
theorem smokeG5Accepted :
    ∀ branch ∈ enumerate [1, 3],
      checkG5Closed 5 (smokeSelected branch) smokeRows smokeSteps = true := by
  intro branch hb
  change branch ∈
    [[(1, false), (3, false)], [(1, false), (3, true)],
     [(1, true), (3, false)], [(1, true), (3, true)]] at hb
  simp only [List.mem_cons, List.not_mem_nil, or_false] at hb
  rcases hb with h | h | h | h
  all_goals subst branch <;> decide

/-- Fully executable, source-bound UNSAT proof of a concrete smoke case.
    This proves just the named instance, not full TC-063 completeness. -/
theorem smoke_ascii_two_cut_unsat :
    Witnora.DIMACSDocument.parseDocument smokeSource =
      some (Witnora.DIMACSTokens.serialize smokeRaw) ∧
    residualComponentCount
      (canonicalSourceVertices (decodeCNF smokeRaw))
      (clauseNeighbors (decodeCNF smokeRaw))
      [1, 3] > 1 ∧
    ¬ ∃ a, signedCNFHolds smokeRaw a := by
  exact checked_ascii_two_cut_g14_unsat
    smokeSource smokeTokens smokeRaw smokeClaims (by decide)
    (1, 3) (by decide) smokeComponents
    (by simpa [smokeResidual] using smokePartitionsAccepted)
    smokeSelected smokeSelectedAccepted
    (fun _ => 5) (fun _ => smokeRows) (fun _ => smokeSteps)
    smokeG5Accepted

#print axioms Witnora.TC063AsciiTwoCutSmoke.smokePartitionsAccepted
#print axioms Witnora.TC063AsciiTwoCutSmoke.smokeG5Accepted
#print axioms Witnora.TC063AsciiTwoCutSmoke.smoke_ascii_two_cut_unsat

end Witnora.TC063AsciiTwoCutSmoke
