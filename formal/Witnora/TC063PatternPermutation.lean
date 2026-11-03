import Witnora.TC063CanonicalAffineBridge

/-!
# Reordering finite forbidden-pattern extraction certificates

The source-bound G5 extractor checks all wrong-parity bit patterns
for an ordered row variable list.  This module relates that list
enumeration to a universally quantified assignment-based coverage
property, so component coefficient permutations can be transported
without trusting Python and without enumerating all global variables.
-/

namespace Witnora.TC063PatternPermutation

open Witnora.Concrete
open Witnora.FiniteXor
open Witnora.Extraction
open Witnora.G5Extraction
open Witnora.TC063CanonicalAffineBridge

/-- Every enumerated n-bit pattern really has length n. -/
theorem allBits_member_length
    (n : Nat) (bits : List Bool)
    (h : bits ∈ allBits n) : bits.length = n := by
  induction n generalizing bits with
  | zero =>
      have hb : bits = [] := by
        simpa [allBits] using h
      simp [hb]
  | succ n ih =>
      have hparts : ∃ rest ∈ allBits n,
          bits ∈ [false :: rest, true :: rest] := by
        simpa [allBits] using h
      obtain ⟨rest, hr, hm⟩ := hparts
      have hc : bits = false :: rest ∨ bits = true :: rest := by
        simpa using hm
      rcases hc with hfalse | htrue
      · rw [hfalse]
        simp [ih rest hr]
      · rw [htrue]
        simp [ih rest hr]

/-- With no repeated variable names, any vector of bits of the same
    length can be realized by a total Boolean assignment on Nat. -/
theorem nodup_vars_realize_bits
    (vars : List Nat) (hNodup : vars.Nodup)
    (bits : List Bool) (hLen : bits.length = vars.length) :
    ∃ a : Nat → Bool, vars.map a = bits := by
  induction vars generalizing bits with
  | nil =>
      cases bits with
      | nil =>
          exact ⟨fun _ => false, rfl⟩
      | cons b rest =>
          simp at hLen
  | cons v rest ih =>
      cases bits with
      | nil =>
          simp at hLen
      | cons b tail =>
          have hNot : v ∉ rest := (List.nodup_cons.mp hNodup).1
          have hRestNodup : rest.Nodup := (List.nodup_cons.mp hNodup).2
          have hTailLen : tail.length = rest.length := by
            simpa using hLen
          obtain ⟨a, ha⟩ := ih hRestNodup tail hTailLen
          let updated : Nat → Bool :=
            fun w => if w = v then b else a w
          have hRest : rest.map updated = rest.map a := by
            apply List.map_congr_left
            intro w hw
            have hn : w ≠ v := by
              intro heq
              subst w
              exact hNot hw
            simp [updated, hn]
          refine ⟨updated, ?_⟩
          change updated v :: rest.map updated = b :: tail
          have hv : updated v = b := by simp [updated]
          rw [hv, hRest, ha]

/-- The bad-assignment literal list is the elementwise signed mapping of
    the coefficient variables when the bad bits are drawn from a model. -/
theorem signForbiddenClause_zip_map
    (vars : List Nat) (a : Nat → Bool) :
    signForbiddenClause (List.zip vars (vars.map a)) =
      vars.map (fun v => (v, !(a v))) := by
  induction vars with
  | nil => rfl
  | cons v rest ih =>
      simpa [signForbiddenClause] using
        congrArg (List.cons (v, !(a v))) ih

/-- Assignment-based formulation of the exact syntactic coverage test
    for every bit pattern of incorrect parity on this variable support. -/
def PatternCovered (source : CNF)
    (vars : List Nat) (rhs : Bool) : Prop :=
  ∀ a : Nat → Bool,
    parityVars vars a ≠ rhs →
      checkClauseCoverage source
        (vars.map (fun v => (v, !(a v)))) = true

/-- Any passing source pattern check covers every wrong-parity
    assignment restricted to that row's variables. -/
theorem checkPattern_implies_patternCovered
    (source : CNF) (vars : List Nat) (rhs : Bool)
    (hCheck : checkPattern source vars rhs = true) :
    PatternCovered source vars rhs := by
  intro a hWrong
  let bad := vars.map a
  have hMem : bad ∈ allBits vars.length := by
    simpa [bad] using allBits_complete bad
  have hWrongBits : parityBits bad ≠ rhs := by
    simpa [bad, parityBits_map] using hWrong
  have hForbidden :
      bad ∈ generateForbiddenPatterns vars.length rhs := by
    simp [generateForbiddenPatterns, hMem, hWrongBits]
  have hRow := List.all_eq_true.mp hCheck bad hForbidden
  simpa [checkPattern, bad, signForbiddenClause_zip_map] using hRow

/-- Conversely, a Nodup support makes *every* enumerated wrong-parity
    bit pattern realizable by some total assignment.  Thus the
    assignment formulation also implies exact executable acceptance. -/
theorem patternCovered_implies_checkPattern
    (source : CNF) (vars : List Nat) (rhs : Bool)
    (hNodup : vars.Nodup)
    (hCovered : PatternCovered source vars rhs) :
    checkPattern source vars rhs = true := by
  unfold checkPattern
  apply List.all_eq_true.mpr
  intro bad hBad
  have hParts := List.mem_filter.mp hBad
  have hMem : bad ∈ allBits vars.length := hParts.1
  have hWrong : parityBits bad ≠ rhs := by
    simpa [generateForbiddenPatterns] using hParts.2
  have hLen : bad.length = vars.length :=
    allBits_member_length vars.length bad hMem
  obtain ⟨a, hMap⟩ :=
    nodup_vars_realize_bits vars hNodup bad hLen
  have hWrongVars : parityVars vars a ≠ rhs := by
    have hx : parityBits (vars.map a) ≠ rhs := by
      simpa [hMap] using hWrong
    simpa [parityBits_map] using hx
  have hCheck := hCovered a hWrongVars
  change checkClauseCoverage source
    (signForbiddenClause (List.zip vars bad)) = true
  rw [← hMap, signForbiddenClause_zip_map]
  exact hCheck

theorem checkPattern_iff_patternCovered
    (source : CNF) (vars : List Nat) (rhs : Bool)
    (hNodup : vars.Nodup) :
    checkPattern source vars rhs = true ↔
      PatternCovered source vars rhs := by
  constructor
  · exact checkPattern_implies_patternCovered source vars rhs
  · exact patternCovered_implies_checkPattern source vars rhs hNodup

/-- Assignment-based source-clause coverage is invariant under
    permutation of the row's coefficient variables. -/
theorem patternCovered_of_perm
    (source : CNF) (vars ordered : List Nat) (rhs : Bool)
    (hPerm : vars.Perm ordered)
    (hCovered : PatternCovered source vars rhs) :
    PatternCovered source ordered rhs := by
  intro a hWrong
  have hWrongOriginal : parityVars vars a ≠ rhs := by
    rw [parityVars_perm hPerm a]
    exact hWrong
  have hOld := hCovered a hWrongOriginal
  have hClausePerm :
      (vars.map (fun v => (v, !(a v)))).Perm
      (ordered.map (fun v => (v, !(a v)))) :=
    hPerm.map (fun v => (v, !(a v)))
  have hEq := checkClauseCoverage_perm_expected source
    (vars.map (fun v => (v, !(a v))))
    (ordered.map (fun v => (v, !(a v)))) hClausePerm
  simpa only [hEq] using hOld

/-- The *executable* source-bound pattern checker is invariant under
    coefficient permutations whenever variables are duplicate-free. -/
theorem checkPattern_perm_of_nodup
    (source : CNF) (vars ordered : List Nat) (rhs : Bool)
    (hPerm : vars.Perm ordered) (hNodup : vars.Nodup) :
    checkPattern source vars rhs =
      checkPattern source ordered rhs := by
  have hOrderedNodup : ordered.Nodup :=
    (hPerm.nodup_iff).mp hNodup
  apply Bool.eq_iff_iff.mpr
  constructor
  · intro h
    apply patternCovered_implies_checkPattern source ordered rhs hOrderedNodup
    exact patternCovered_of_perm source vars ordered rhs hPerm
      (checkPattern_implies_patternCovered source vars rhs h)
  · intro h
    apply patternCovered_implies_checkPattern source vars rhs hNodup
    exact patternCovered_of_perm source ordered vars rhs hPerm.symm
      (checkPattern_implies_patternCovered source ordered rhs h)

/-- Deterministic insertion sorting leaves the exact source-bound
    forbidden-pattern acceptance boolean unchanged. -/
theorem checkPattern_sortVariables
    (source : CNF) (vars : List Nat) (rhs : Bool)
    (hNodup : vars.Nodup) :
    checkPattern source (sortVariables vars) rhs =
      checkPattern source vars rhs := by
  exact (checkPattern_perm_of_nodup source vars
    (sortVariables vars) rhs
    (sortVariables_perm vars).symm hNodup).symm

#print axioms Witnora.TC063PatternPermutation.checkPattern_perm_of_nodup
#print axioms Witnora.TC063PatternPermutation.checkPattern_sortVariables

#print axioms Witnora.TC063PatternPermutation.allBits_member_length
#print axioms Witnora.TC063PatternPermutation.nodup_vars_realize_bits
#print axioms Witnora.TC063PatternPermutation.checkPattern_iff_patternCovered

end Witnora.TC063PatternPermutation
