import Witnora.BinaryXorDiscovery

/-!
# Complete finite spoke-path discovery

A path x--middle--z consists of two binary XOR equations with x < z,
all variable IDs distinct, and independent parity labels. The executable
specification enumerates the full finite universe and filters it by source
CNF coverage. This is the mathematical target for the Python graph join.
-/

namespace Witnora.SpokePathDiscovery

open Witnora.G5Extraction
open Witnora.Extraction

structure Path where
  x : Nat
  z : Nat
  middle : Nat
  left : Bool
  right : Bool
  deriving DecidableEq, Repr

def allCandidates (ids : List Nat) : List Path :=
  ids.flatMap (fun x =>
    ids.flatMap (fun z =>
      ids.flatMap (fun middle =>
        ([false, true] : List Bool).flatMap (fun left =>
          ([false, true] : List Bool).map (fun right =>
            ⟨x, z, middle, left, right⟩)))))

def valid (cnf : Witnora.Concrete.CNF) (p : Path) : Bool :=
  decide (0 < p.x ∧ p.x < p.z ∧ 0 < p.middle ∧
    p.middle ≠ p.x ∧ p.middle ≠ p.z) &&
  checkPattern cnf [p.x, p.middle] p.left &&
  checkPattern cnf [p.middle, p.z] p.right

def extract (cnf : Witnora.Concrete.CNF) (ids : List Nat) : List Path :=
  (allCandidates ids).filter (valid cnf)

theorem allCandidates_complete (ids : List Nat) (p : Path)
    (hx : p.x ∈ ids) (hz : p.z ∈ ids)
    (hm : p.middle ∈ ids) :
    p ∈ allCandidates ids := by
  rcases p with ⟨x, z, m, l, r⟩
  simp only [allCandidates, List.mem_flatMap]
  refine ⟨x, ?_, z, ?_, m, ?_, ?_⟩
  · simpa using hx
  · simpa using hz
  · simpa using hm
  · cases l <;> cases r <;> simp

theorem mem_extract_iff (cnf : Witnora.Concrete.CNF)
    (ids : List Nat) (p : Path) :
    p ∈ extract cnf ids ↔
      p ∈ allCandidates ids ∧ valid cnf p = true := by
  simp [extract]

theorem extract_sound (cnf : Witnora.Concrete.CNF)
    (ids : List Nat) (p : Path) (hp : p ∈ extract cnf ids)
    (a : Nat → Bool) (ha : CNFHolds cnf a) :
    parityVars [p.x, p.middle] a = p.left ∧
      parityVars [p.middle, p.z] a = p.right := by
  have hv := (mem_extract_iff cnf ids p).mp hp
  have hc := hv.2
  simp only [valid, Bool.and_eq_true] at hc
  exact ⟨checkPattern_sound cnf [p.x, p.middle] p.left hc.1.2 a ha,
    checkPattern_sound cnf [p.middle, p.z] p.right hc.2 a ha⟩

#print axioms Witnora.SpokePathDiscovery.extract_sound

end Witnora.SpokePathDiscovery
