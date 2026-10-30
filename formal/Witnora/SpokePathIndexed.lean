import Witnora.SpokePathDiscovery

/-!
# Indexed edge-join certificate for complete spoke path sets

The certificate compares the reported path set with *all* joins of the
verified binary-edge list. It does not enumerate every variable triple
against the source CNF again. Its soundness is universal over edge/path
lists; the caller separately checks exact binary-edge extraction.
-/

namespace Witnora.SpokePathIndexed

open Witnora.BinaryXorDiscovery
open Witnora.SpokePathDiscovery

def emit (middle x z : Nat) (left right : Bool) : List Path :=
  if x == z then [] else
  if x < z then [⟨x, z, middle, left, right⟩]
  else [⟨z, x, middle, right, left⟩]

def join (e f : Equation) : List Path :=
  (if e.u == f.u then emit e.u e.v f.v e.rhs f.rhs else []) ++
  (if e.u == f.v then emit e.u e.v f.u e.rhs f.rhs else []) ++
  (if e.v == f.u then emit e.v e.u f.v e.rhs f.rhs else []) ++
  (if e.v == f.v then emit e.v e.u f.u e.rhs f.rhs else [])

def allJoins (edges : List Equation) : List Path :=
  edges.flatMap (fun e => edges.flatMap (fun f => join e f))

/-- Reject omissions, fabricated paths, and duplicate reported paths. -/
def checkExact (edges : List Equation) (reported : List Path) : Bool :=
  (reported.all (fun p => decide (p ∈ allJoins edges))) &&
  ((allJoins edges).all (fun p => decide (p ∈ reported))) &&
  decide reported.Nodup

theorem checkExact_mem_iff (edges : List Equation) (reported : List Path)
    (h : checkExact edges reported = true) (p : Path) :
    p ∈ reported ↔ p ∈ allJoins edges := by
  simp only [checkExact, Bool.and_eq_true] at h
  constructor
  · intro hp
    have hs := List.all_eq_true.mp h.1.1 p hp
    simpa using hs
  · intro hp
    have hs := List.all_eq_true.mp h.1.2 p hp
    simpa using hs

#print axioms Witnora.SpokePathIndexed.checkExact_mem_iff

end Witnora.SpokePathIndexed
