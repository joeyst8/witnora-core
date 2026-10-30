import Witnora.G5Extraction

/-!
# Complete executable binary XOR-pattern discovery

For every ordered variable pair u < v from a finite ID list, test both
Boolean parity right-hand sides against the original CNF. Membership in
the result means exactly that Lean's complete clause-pattern extraction
checker accepts the equation. Every accepted equation is entailed by
every model of the original CNF.

Theorem statements are universal over input CNFs and ID lists. A separate
Python refinement check compares concrete extracted output to this model.
-/

namespace Witnora.BinaryXorDiscovery

open Witnora.G5Extraction
open Witnora.Extraction

structure Equation where
  u : Nat
  v : Nat
  rhs : Bool
  deriving DecidableEq, Repr

def allCandidates (ids : List Nat) : List Equation :=
  ids.flatMap (fun u =>
    ids.flatMap (fun v =>
      ([false, true] : List Bool).map (fun rhs => ⟨u, v, rhs⟩)))

def valid (cnf : Witnora.Concrete.CNF) (eq : Equation) : Bool :=
  decide (0 < eq.u ∧ eq.u < eq.v) &&
    checkPattern cnf [eq.u, eq.v] eq.rhs

def extract (cnf : Witnora.Concrete.CNF) (ids : List Nat) : List Equation :=
  (allCandidates ids).filter (valid cnf)

/-- Every possible RHS for each pair in the supplied domain is proposed. -/
theorem allCandidates_complete (ids : List Nat) (eq : Equation)
    (hu : eq.u ∈ ids) (hv : eq.v ∈ ids) :
    eq ∈ allCandidates ids := by
  rcases eq with ⟨u, v, rhs⟩
  simp only [allCandidates, List.mem_flatMap]
  refine ⟨u, ?_, v, ?_, ?_⟩
  · simpa using hu
  · simpa using hv
  · cases rhs <;> simp

/-- Exact membership: the result contains all and only supported complete
    binary patterns from the finite variable-domain specification. -/
theorem mem_extract_iff
    (cnf : Witnora.Concrete.CNF) (ids : List Nat)
    (eq : Equation) :
    eq ∈ extract cnf ids ↔
      eq.u ∈ ids ∧ eq.v ∈ ids ∧ valid cnf eq = true := by
  constructor
  · intro h
    have he : eq ∈ allCandidates ids ∧ valid cnf eq = true := by
      simpa [extract] using h
    rcases he with ⟨he, hvalid⟩
    simp [allCandidates, List.mem_flatMap] at he
    rcases he with ⟨u, hu, v, hv, hmatch⟩
    rcases eq with ⟨eu, ev, rhs⟩
    simp at hmatch
    rcases hmatch with h0 | h1
    · rcases h0 with ⟨rfl, rfl, rfl⟩
      exact ⟨hu, hv, hvalid⟩
    · rcases h1 with ⟨rfl, rfl, rfl⟩
      exact ⟨hu, hv, hvalid⟩
  · rintro ⟨hu, hv, hvalid⟩
    simp [extract, allCandidates_complete ids eq hu hv, hvalid]

/-- Every extracted binary equation follows from the source CNF. -/
theorem extract_sound
    (cnf : Witnora.Concrete.CNF) (ids : List Nat)
    (eq : Equation) (he : eq ∈ extract cnf ids)
    (a : Nat → Bool) (ha : CNFHolds cnf a) :
    parityVars [eq.u, eq.v] a = eq.rhs := by
  have hh := (mem_extract_iff cnf ids eq).mp he
  have hvalid := hh.2.2
  simp only [valid, Bool.and_eq_true] at hvalid
  exact checkPattern_sound cnf [eq.u, eq.v] eq.rhs hvalid.2 a ha

#print axioms Witnora.BinaryXorDiscovery.extract_sound

end Witnora.BinaryXorDiscovery
