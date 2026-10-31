import Witnora.G14ConcreteBridge

/-!
# Executable bounded G14/G5 UNSAT-cover contract

This is a *sound accepted-certificate predicate*, not complete membership
recognition for the family SAF(c,r). Exact affine extraction of every
component, separator discovery, and a polynomial machine-cost bound remain
separate obligations. It avoids trusting a Boolean SAT/UNSAT label.
-/

namespace Witnora.SAFCheckedCover

open Witnora.Concrete
open Witnora.Conditioning
open Witnora.ComponentPartition
open Witnora.SignedSerialization
open Witnora.SparseBridge

/-- A finite, bound-checked certificate predicate. No original-CNF global
    assignment enumeration occurs inside this checker. -/
def checkBoundedUnsatCover
    (c : Nat) (raw : List (List Int)) (separator : List Nat)
    (components : List (Nat × Bool) → List CNF)
    (selected : List (Nat × Bool) → CNF)
    (bound : List (Nat × Bool) → Nat)
    (rows : List (Nat × Bool) → List Witnora.G5Trace.Row)
    (steps : List (Nat × Bool) → List Witnora.G5Dag.XorRef) : Bool :=
  decide (separator.length ≤ c) &&
    (Witnora.SeparatorAssignments.enumerate separator).all (fun branch =>
      (checkPartition
        (conditionCNF (Witnora.SeparatorAssignments.fixedOf branch)
          (decodeCNF raw))
        (components branch) &&
       decide (selected branch ∈ components branch)) &&
      checkG5Closed (bound branch) (selected branch)
        (rows branch) (steps branch))

/-- A passing executable bounded cover entails UNSAT of the actual signed
    source CNF; the only inputs are the certificate data and its acceptance
    proof. No unproved decomposition hypothesis is introduced. -/
theorem checkBoundedUnsatCover_sound
    (c : Nat) (raw : List (List Int)) (separator : List Nat)
    (components : List (Nat × Bool) → List CNF)
    (selected : List (Nat × Bool) → CNF)
    (bound : List (Nat × Bool) → Nat)
    (rows : List (Nat × Bool) → List Witnora.G5Trace.Row)
    (steps : List (Nat × Bool) → List Witnora.G5Dag.XorRef)
    (h : checkBoundedUnsatCover c raw separator
      components selected bound rows steps = true) :
    separator.length ≤ c ∧ ¬ ∃ a, signedCNFHolds raw a := by
  unfold checkBoundedUnsatCover at h
  simp at h
  obtain ⟨hc, hall⟩ := h
  refine ⟨hc, ?_⟩
  have hbranch (branch : List (Nat × Bool))
      (hb : branch ∈ Witnora.SeparatorAssignments.enumerate separator) :
      (checkPartition
        (conditionCNF (Witnora.SeparatorAssignments.fixedOf branch)
          (decodeCNF raw))
        (components branch) &&
       decide (selected branch ∈ components branch)) &&
      checkG5Closed (bound branch) (selected branch)
        (rows branch) (steps branch) = true :=
    by simpa using hall branch hb
  apply Witnora.G14ConcreteBridge.signed_unsat_of_enumerated_partitions
    raw separator components
  · intro branch hb
    have hs := hbranch branch hb
    simp at hs
    exact hs.1.1
  · exact selected
  · intro branch hb
    have hs := hbranch branch hb
    simp at hs
    exact hs.1.2
  · exact bound
  · exact rows
  · exact steps
  · intro branch hb
    have hs := hbranch branch hb
    simp at hs
    exact hs.2

/-- A separator exceeding the claimed fixed bound fails closed. -/
example :
    checkBoundedUnsatCover 0 [] [1]
      (fun _ => []) (fun _ => []) (fun _ => 0)
      (fun _ => []) (fun _ => []) = false := by decide

/-- Missing residual clauses are not silently accepted as an exact partition. -/
example :
    checkBoundedUnsatCover 1 [[2]] [1]
      (fun _ => []) (fun _ => []) (fun _ => 0)
      (fun _ => []) (fun _ => []) = false := by decide

#print axioms Witnora.SAFCheckedCover.checkBoundedUnsatCover_sound

end Witnora.SAFCheckedCover
