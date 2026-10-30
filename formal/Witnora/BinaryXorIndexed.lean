import Witnora.BinaryXorDiscovery

/-!
# Indexed, source-driven binary XOR extraction checker

Candidate pairs come only from actual length-two source clauses, rather
than from the Cartesian square of all declared variable IDs. Both parity
labels are considered for every such pair. A full exact two-clause pattern
and the independent G5 entailment checker are required for acceptance.
-/

namespace Witnora.BinaryXorIndexed

open Witnora.G5Extraction
open Witnora.Extraction
open Witnora.BinaryXorDiscovery

def pairsOfClause : List Witnora.Concrete.Literal → List (Nat × Nat)
  | [a, b] =>
      if decide (0 < a.1 ∧ a.1 < b.1) then [(a.1, b.1)]
      else if decide (0 < b.1 ∧ b.1 < a.1) then [(b.1, a.1)]
      else []
  | _ => []

def candidates (cnf : Witnora.Concrete.CNF) : List Equation :=
  cnf.flatMap (fun clause =>
    (pairsOfClause clause).flatMap (fun (u, v) =>
      ([false, true] : List Bool).map (fun rhs => ⟨u, v, rhs⟩)))

def hasExactClause (cnf : Witnora.Concrete.CNF)
    (u v : Nat) (pu pv : Bool) : Bool :=
  cnf.any (fun clause =>
    decide (clause.length = 2) &&
    decide ((u, pu) ∈ clause) &&
    decide ((v, pv) ∈ clause))

def valid (cnf : Witnora.Concrete.CNF) (eq : Equation) : Bool :=
  (if eq.rhs then
    hasExactClause cnf eq.u eq.v true true &&
    hasExactClause cnf eq.u eq.v false false
   else
    hasExactClause cnf eq.u eq.v true false &&
    hasExactClause cnf eq.u eq.v false true) &&
  checkPattern cnf [eq.u, eq.v] eq.rhs

def approved (cnf : Witnora.Concrete.CNF) : List Equation :=
  (candidates cnf).filter (valid cnf)

/-- Compare finite sets, reject repeated claims, and forbid any omission. -/
def checkExact (cnf : Witnora.Concrete.CNF)
    (reported : List Equation) : Bool :=
  (reported.all (fun eq => decide (eq ∈ approved cnf))) &&
  ((approved cnf).all (fun eq => decide (eq ∈ reported))) &&
  decide reported.Nodup

theorem checkExact_mem_iff (cnf : Witnora.Concrete.CNF)
    (reported : List Equation) (h : checkExact cnf reported = true)
    (eq : Equation) :
    eq ∈ reported ↔ eq ∈ approved cnf := by
  simp only [checkExact, Bool.and_eq_true] at h
  constructor
  · intro he
    have hs := List.all_eq_true.mp h.1.1 eq he
    simpa using hs
  · intro he
    have hs := List.all_eq_true.mp h.1.2 eq he
    simpa using hs

/-- No reported equation can be false in a model of the source CNF. -/
theorem checkExact_sound (cnf : Witnora.Concrete.CNF)
    (reported : List Equation) (h : checkExact cnf reported = true)
    (eq : Equation) (he : eq ∈ reported)
    (a : Nat → Bool) (ha : CNFHolds cnf a) :
    parityVars [eq.u, eq.v] a = eq.rhs := by
  have hv : valid cnf eq = true := by
    have happ := (checkExact_mem_iff cnf reported h eq).mp he
    have hfilter : eq ∈ candidates cnf ∧ valid cnf eq = true := by
      simpa [approved] using happ
    exact hfilter.2
  simp only [valid, Bool.and_eq_true] at hv
  exact checkPattern_sound cnf [eq.u, eq.v] eq.rhs hv.2 a ha

#print axioms Witnora.BinaryXorIndexed.checkExact_sound

end Witnora.BinaryXorIndexed
