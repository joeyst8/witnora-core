import Witnora.G5Extraction
import Witnora.SpokeCollapse

/-!
# Closed XOR-walk contradiction certificates

A walk certificate is an initial vertex and successive (next vertex, parity)
steps. Every step must be backed by a complete source-CNF binary XOR
pattern. A walk returning to its start with odd total parity proves UNSAT,
regardless of other CNF clauses. This generalizes the four-edge spoke
obstruction, without asserting the underlying GF(2) idea is novel.
-/

namespace Witnora.CycleParity

open Witnora.G5Extraction
open Witnora.Extraction
open Witnora.SpokeCollapse

def lastVertex (start : Nat) : List (Nat × Bool) → Nat
  | [] => start
  | (next, _) :: rest => lastVertex next rest

def rhsParity : List (Nat × Bool) → Bool
  | [] => false
  | (_, rhs) :: rest => rhs != rhsParity rest

def WalkHolds (a : Nat → Bool) (start : Nat) :
    List (Nat × Bool) → Prop
  | [] => True
  | (next, rhs) :: rest =>
      (a start != a next) = rhs ∧ WalkHolds a next rest

def checkSteps (cnf : Witnora.Concrete.CNF) (start : Nat) :
    List (Nat × Bool) → Bool
  | [] => true
  | (next, rhs) :: rest =>
      checkPattern cnf [start, next] rhs && checkSteps cnf next rest

theorem walk_endpoint (a : Nat → Bool) (start : Nat)
    (steps : List (Nat × Bool))
    (h : WalkHolds a start steps) :
    (a start != a (lastVertex start steps)) = rhsParity steps := by
  induction steps generalizing start with
  | nil =>
      simp [lastVertex, rhsParity]
  | cons step rest ih =>
      rcases step with ⟨next, rhs⟩
      have hh : (a start != a next) = rhs ∧ WalkHolds a next rest := h
      have hrest := ih next hh.2
      have hchain := spoke_endpoint
        (a start) (a (lastVertex next rest)) (a next)
        rhs (rhsParity rest) hh.1 hrest
      simpa [lastVertex, rhsParity] using hchain

theorem checkSteps_sound (cnf : Witnora.Concrete.CNF)
    (a : Nat → Bool) (ha : CNFHolds cnf a)
    (start : Nat) (steps : List (Nat × Bool))
    (h : checkSteps cnf start steps = true) :
    WalkHolds a start steps := by
  induction steps generalizing start with
  | nil => trivial
  | cons step rest ih =>
      rcases step with ⟨next, rhs⟩
      have hh : checkPattern cnf [start, next] rhs = true ∧
          checkSteps cnf next rest = true := by
        simpa [checkSteps, Bool.and_eq_true] using h
      constructor
      · have he := checkPattern_sound cnf [start, next] rhs hh.1 a ha
        simpa [parityVars] using he
      · exact ih next hh.2

/-- A complete source-backed odd-parity closed walk proves source UNSAT. -/
theorem closedWalk_unsat (cnf : Witnora.Concrete.CNF)
    (start : Nat) (steps : List (Nat × Bool))
    (hcheck : checkSteps cnf start steps = true)
    (hclosed : lastVertex start steps = start)
    (hodd : rhsParity steps = true) :
    ¬ ∃ a, CNFHolds cnf a := by
  rintro ⟨a, ha⟩
  have hw := checkSteps_sound cnf a ha start steps hcheck
  have hp := walk_endpoint a start steps hw
  rw [hclosed, hodd] at hp
  simp at hp

#print axioms Witnora.CycleParity.closedWalk_unsat

end Witnora.CycleParity
