import Witnora.Concrete

/-!
# Finite canonical XOR-CNF specification

A canonical XOR CNF contains one clause excluding each length-n Boolean
pattern whose parity is different from rhs. Here a clause is represented
by its Boolean exclusion predicate. This executable specification is finite
and complete for every n, including n=0. The actual literal-list encoder
still requires a representation-refinement proof.
-/

namespace Witnora.FiniteXor

open Witnora.Concrete

def parityBits : List Bool → Bool
  | [] => false
  | bit :: rest => Bool.xor bit (parityBits rest)

/-- Evaluate the complete finite family of wrong-parity exclusions.
The test `actual ≠ bad` is the semantics of one forbidden clause. -/
def canonicalFinite (n : Nat) (rhs : Bool) (actual : List Bool) : Bool :=
  (allBits n).all (fun bad =>
    decide (parityBits bad = rhs) || decide (actual ≠ bad))

/-- Every length-n assignment satisfies the finite canonical XOR-CNF
exactly when its XOR parity equals rhs. No assumptions on n or rhs. -/
theorem canonicalFinite_iff (n : Nat) (rhs : Bool)
    (actual : List Bool) (hlen : actual.length = n) :
    canonicalFinite n rhs actual = true ↔ parityBits actual = rhs := by
  constructor
  · intro h
    unfold canonicalFinite at h
    have hmem : actual ∈ allBits n := by
      simpa [hlen] using allBits_complete actual
    have hrow := List.all_eq_true.mp h actual hmem
    simpa using hrow
  · intro hright
    unfold canonicalFinite
    apply List.all_eq_true.mpr
    intro bad _
    by_cases hbad : parityBits bad = rhs
    · simp [hbad]
    · have hneq : actual ≠ bad := by
        intro heq
        subst bad
        exact hbad hright
      simp [hneq]

/-- Executable normalization model for Python's positive integer-ID domain.
Reject zero, retain variables with odd occurrence counts and enumerate IDs in
ascending order. The finite range is a model of the Python dictionary/sort
result; a full representation-refinement theorem is separate. -/
def normalizePositiveVariables (raw : List Nat) : Option (List Nat) :=
  if raw.all (fun v => decide (0 < v)) then
    some ((List.range (raw.foldl max 0 + 1)).filter
      (fun v => raw.count v % 2 == 1))
  else none

/-- The executable normalizer rejects exactly the raw lists containing
a nonpositive (zero in Nat) variable. -/
theorem normalizePositiveVariables_valid_iff (raw : List Nat) :
    (normalizePositiveVariables raw).isSome = true ↔
      ∀ v ∈ raw, 0 < v := by
  constructor
  · intro hsome
    have hall : raw.all (fun v => decide (0 < v)) = true := by
      by_cases hh : raw.all (fun v => decide (0 < v)) = true
      · exact hh
      · simp [normalizePositiveVariables, hh] at hsome
    intro v hv
    have ht := List.all_eq_true.mp hall v hv
    simpa using ht
  · intro hvalid
    have hall : raw.all (fun v => decide (0 < v)) = true := by
      apply List.all_eq_true.mpr
      intro v hv
      simpa using hvalid v hv
    simp [normalizePositiveVariables, hall]

/-- Concrete regression examples of the canonical ordering and GF(2)
cancellation behavior, including the empty case. -/
example : normalizePositiveVariables [3, 1, 3, 2, 1, 5] = some [2, 5] := by decide
example : normalizePositiveVariables [1, 1] = some [] := by decide
example : normalizePositiveVariables [0, 0] = none := by decide

/-- Executable generator: enumerate all n-bit assignments and retain exactly
those with parity opposite rhs. Each retained bit vector represents the
literal clause that forbids precisely that assignment. -/
def generateForbiddenPatterns (n : Nat) (rhs : Bool) : List (List Bool) :=
  (allBits n).filter (fun bad => decide (parityBits bad ≠ rhs))

/-- Evaluate the concrete generated clause family. -/
def generatedFinite (n : Nat) (rhs : Bool) (actual : List Bool) : Bool :=
  (generateForbiddenPatterns n rhs).all (fun bad => decide (actual ≠ bad))

/-- The executable finite generator agrees exactly with the declarative
canonical XOR-CNF specification for every arity, rhs, and actual pattern. -/
theorem generatedFinite_eq_canonicalFinite
    (n : Nat) (rhs : Bool) (actual : List Bool) :
    generatedFinite n rhs actual = canonicalFinite n rhs actual := by
  apply Bool.eq_iff_iff.mpr
  constructor
  · intro h
    apply List.all_eq_true.mpr
    intro bad hmem
    by_cases hpar : parityBits bad = rhs
    · simp [hpar]
    · have hbad : bad ∈ generateForbiddenPatterns n rhs := by
        simp [generateForbiddenPatterns, hmem, hpar]
      have hx := List.all_eq_true.mp h bad hbad
      simp [hpar, hx]
  · intro h
    apply List.all_eq_true.mpr
    intro bad hmem
    have hbase : bad ∈ allBits n := (List.mem_filter.mp hmem).1
    have hpar : parityBits bad ≠ rhs := by
      have hpred := (List.mem_filter.mp hmem).2
      simpa [generateForbiddenPatterns] using hpred
    have hx := List.all_eq_true.mp h bad hbase
    simp [hpar] at hx
    simpa using hx

#print axioms Witnora.FiniteXor.generatedFinite_eq_canonicalFinite

#print axioms Witnora.FiniteXor.canonicalFinite_iff

end Witnora.FiniteXor
