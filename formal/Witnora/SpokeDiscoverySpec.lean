import Witnora.SpokeSourceBridge

/-!
# Executable finite specification of discovered spoke candidates

A candidate is a proposed pair of paths with conflicting endpoint parity.
The executable filter validates complete extracted CNF patterns directly
against the source. Its output is *exactly* the accepted subset of the
proposed finite list, and every accepted element proves source CNF UNSAT.

This is a universal theorem over arbitrary CNFs and proposal lists. The
remaining Python-language refinement task is to show Python's enumeration
of proposals corresponds to the Lean proposal enumeration.
-/

namespace Witnora.SpokeDiscoverySpec

open Witnora.G5Extraction
open Witnora.SpokeCollapse
open Witnora.SpokeSourceBridge

structure Proposal where
  x : Nat
  z : Nat
  first : Spoke
  second : Spoke
  deriving DecidableEq, Repr

def valid (cnf : Witnora.Concrete.CNF) (p : Proposal) : Bool :=
  decide (0 < p.x ∧ 0 < p.z ∧ p.x ≠ p.z ∧
    p.first.middle ≠ p.second.middle ∧
    p.first.middle ≠ p.x ∧ p.first.middle ≠ p.z ∧
    p.second.middle ≠ p.x ∧ p.second.middle ≠ p.z) &&
  checkSpokeConflict cnf p.x p.z p.first p.second

/-- Executable discovery specification relative to a complete finite
    proposal list: retain exactly those proposals whose evidence checks. -/
def discoverFrom (cnf : Witnora.Concrete.CNF)
    (proposals : List Proposal) : List Proposal :=
  proposals.filter (valid cnf)

/-- A candidate appears in the result iff it was proposed and satisfies
    every validated endpoint, intermediary and source-pattern condition. -/
theorem mem_discoverFrom_iff
    (cnf : Witnora.Concrete.CNF) (proposals : List Proposal)
    (p : Proposal) :
    p ∈ discoverFrom cnf proposals ↔
      p ∈ proposals ∧ valid cnf p = true := by
  simp [discoverFrom]

/-- Soundness is universal: no accepted candidate can be a false UNSAT
    deduction about the original formula, regardless of proposal order. -/
theorem discoverFrom_unsat
    (cnf : Witnora.Concrete.CNF) (proposals : List Proposal)
    (p : Proposal) (hp : p ∈ discoverFrom cnf proposals) :
    ¬ ∃ a, CNFHolds cnf a := by
  have hv := (mem_discoverFrom_iff cnf proposals p).mp hp
  have hvalid := hv.2
  simp only [valid, Bool.and_eq_true] at hvalid
  have hpattern : checkSpokeConflict cnf p.x p.z p.first p.second = true :=
    hvalid.2
  exact checkSpokeConflict_unsat cnf p.x p.z p.first p.second hpattern

#print axioms Witnora.SpokeDiscoverySpec.discoverFrom_unsat

end Witnora.SpokeDiscoverySpec
