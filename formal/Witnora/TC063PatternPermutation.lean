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
open Witnora.ComponentPartition
open Witnora.ExactAffineMembership

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

/-- Sorting a whole list of duplicate-free affine row supports leaves
    the executable G5 initial-source extraction checker unchanged. -/
theorem checkInitialRows_sortAffineRows
    (source : CNF) (rows : List Witnora.G5Trace.Row)
    (hNodup : ∀ row ∈ rows, row.coefficients.Nodup) :
    checkInitialRows source (sortAffineRows rows) =
      checkInitialRows source rows := by
  induction rows with
  | nil => rfl
  | cons row rest ih =>
      have hHead : row.coefficients.Nodup :=
        hNodup row (by simp)
      have hTail : ∀ r ∈ rest, r.coefficients.Nodup := by
        intro r hr
        exact hNodup r (by simp [hr])
      have hRest :
          rest.all ((fun r => checkPattern source r.coefficients r.rhs) ∘
              sortAffineRow) =
          rest.all (fun r => checkPattern source r.coefficients r.rhs) := by
        simpa only [checkInitialRows, sortAffineRows, List.all_map]
          using ih hTail
      simp [sortAffineRows, sortAffineRow, checkInitialRows,
        checkPattern_sortVariables source row.coefficients row.rhs hHead,
        hRest]

/-- Permuting the *source* side of a subsumption check preserves
    its result as well: source-clause literal order is immaterial. -/
theorem clauseSubsumes_perm_source
    (candidate ordered expected : List Literal)
    (hPerm : candidate.Perm ordered) :
    clauseSubsumes candidate expected =
      clauseSubsumes ordered expected := by
  unfold clauseSubsumes
  exact all_perm (fun lit => decide (lit ∈ expected)) hPerm

/-- Every canonical forbidden clause for one coefficient order has a
    literally permutation-equivalent clause after support reordering.
    Construct it by realizing the forbidden bits as a total assignment. -/
theorem signedClause_permutation_match
    (vars ordered : List Nat) (rhs : Bool)
    (hPerm : vars.Perm ordered) (hNodup : vars.Nodup)
    (clause : List Literal)
    (hClause : clause ∈ generateSignedClauses vars rhs) :
    ∃ orderedClause ∈ generateSignedClauses ordered rhs,
      clause.Perm orderedClause := by
  change clause ∈
    (generateForbiddenPatterns vars.length rhs).map
      (fun bad => signForbiddenClause (List.zip vars bad)) at hClause
  obtain ⟨bad, hBad, rfl⟩ := List.mem_map.mp hClause
  have hMem : bad ∈ allBits vars.length :=
    (List.mem_filter.mp hBad).1
  have hWrong : parityBits bad ≠ rhs := by
    simpa [generateForbiddenPatterns] using (List.mem_filter.mp hBad).2
  have hLen : bad.length = vars.length :=
    allBits_member_length vars.length bad hMem
  obtain ⟨a, hMap⟩ :=
    nodup_vars_realize_bits vars hNodup bad hLen
  have hWrongOld : parityVars vars a ≠ rhs := by
    rw [← parityBits_map vars a, hMap]
    exact hWrong
  have hWrongNew : parityBits (ordered.map a) ≠ rhs := by
    rw [parityBits_map, ← parityVars_perm hPerm a]
    exact hWrongOld
  have hMemNew : ordered.map a ∈ allBits ordered.length := by
    simpa using allBits_complete (ordered.map a)
  have hBadNew :
      ordered.map a ∈ generateForbiddenPatterns ordered.length rhs := by
    simp [generateForbiddenPatterns, hMemNew, hWrongNew]
  refine ⟨signForbiddenClause (List.zip ordered (ordered.map a)), ?_, ?_⟩
  · change signForbiddenClause (List.zip ordered (ordered.map a)) ∈
      (generateForbiddenPatterns ordered.length rhs).map
        (fun bits => signForbiddenClause (List.zip ordered bits))
    exact List.mem_map.mpr ⟨ordered.map a, hBadNew, rfl⟩
  · have hOriginal :
        signForbiddenClause (List.zip vars bad) =
          vars.map (fun v => (v, !(a v))) := by
        rw [← hMap, signForbiddenClause_zip_map]
    rw [hOriginal, signForbiddenClause_zip_map]
    exact hPerm.map (fun v => (v, !(a v)))

/-- Even when canonical forbidden clauses arrive in different orders and
    with permuted literals, source-clause coverage acceptance is identical. -/
theorem checkClauseCoverage_signedClauses_perm
    (vars ordered : List Nat) (rhs : Bool)
    (expected : List Literal)
    (hPerm : vars.Perm ordered) (hNodup : vars.Nodup) :
    checkClauseCoverage (generateSignedClauses vars rhs) expected =
      checkClauseCoverage (generateSignedClauses ordered rhs) expected := by
  have hOrderedNodup : ordered.Nodup :=
    (hPerm.nodup_iff).mp hNodup
  apply Bool.eq_iff_iff.mpr
  constructor
  · intro h
    obtain ⟨clause, hc, hsub⟩ := List.any_eq_true.mp h
    obtain ⟨target, ht, hp⟩ :=
      signedClause_permutation_match vars ordered rhs hPerm hNodup
        clause hc
    apply List.any_eq_true.mpr
    refine ⟨target, ht, ?_⟩
    simpa only [← clauseSubsumes_perm_source clause target expected hp]
      using hsub
  · intro h
    obtain ⟨clause, hc, hsub⟩ := List.any_eq_true.mp h
    obtain ⟨target, ht, hp⟩ :=
      signedClause_permutation_match ordered vars rhs hPerm.symm
        hOrderedNodup clause hc
    apply List.any_eq_true.mpr
    refine ⟨target, ht, ?_⟩
    simpa only [← clauseSubsumes_perm_source clause target expected hp]
      using hsub

/-- The original-clause coverage checker distributes over a
    concatenation of generated affine clause sets. -/
theorem checkClauseCoverage_append
    (front back : CNF) (expected : List Literal) :
    checkClauseCoverage (front ++ back) expected =
      (checkClauseCoverage front expected ||
        checkClauseCoverage back expected) := by
  simp [checkClauseCoverage, List.any_append]

/-- Reverse semantic extraction coverage is unaffected when every row
    coefficient list is sorted, provided supports are duplicate-free. -/
theorem checkClauseCoverage_expanded_sortAffineRows
    (rows : List Witnora.G5Trace.Row) (expected : List Literal)
    (hNodup : ∀ row ∈ rows, row.coefficients.Nodup) :
    checkClauseCoverage (expanded (sortAffineRows rows)) expected =
      checkClauseCoverage (expanded rows) expected := by
  induction rows with
  | nil => rfl
  | cons row rest ih =>
      have hHead : row.coefficients.Nodup :=
        hNodup row (by simp)
      have hTail : ∀ r ∈ rest, r.coefficients.Nodup := by
        intro r hr
        exact hNodup r (by simp [hr])
      change checkClauseCoverage
          (generateSignedClauses (sortVariables row.coefficients) row.rhs ++
            expanded (sortAffineRows rest)) expected =
        checkClauseCoverage
          (generateSignedClauses row.coefficients row.rhs ++
            expanded rest) expected
      rw [checkClauseCoverage_append, checkClauseCoverage_append]
      have hRow :=
        checkClauseCoverage_signedClauses_perm
          row.coefficients (sortVariables row.coefficients) row.rhs
          expected (sortVariables_perm row.coefficients).symm hHead
      rw [← hRow, ih hTail]

/-- Every original clause's reverse-coverage result is unchanged
    after deterministic coefficient sorting across the entire system. -/
theorem reverseCoverage_sortAffineRows
    (source : CNF) (rows : List Witnora.G5Trace.Row)
    (hNodup : ∀ row ∈ rows, row.coefficients.Nodup) :
    source.all (checkClauseCoverage (expanded (sortAffineRows rows))) =
      source.all (checkClauseCoverage (expanded rows)) := by
  induction source with
  | nil => rfl
  | cons clause rest ih =>
      simp only [List.all_cons]
      rw [checkClauseCoverage_expanded_sortAffineRows rows clause hNodup, ih]

/-- Row arity, duplicate-free support, and positivity are all
    preserved by coefficient sorting, so the actual row validator agrees. -/
theorem rowSupported_sortAffineRow
    (r : Nat) (row : Witnora.G5Trace.Row) :
    rowSupported r (sortAffineRow row) = rowSupported r row := by
  have hp := sortVariables_perm row.coefficients
  have hLen := hp.length_eq
  have hNodup := hp.nodup_iff
  have hPos := all_perm (fun v => decide (v > 0)) hp
  simp [rowSupported, sortAffineRow, hLen, hNodup, hPos]

/-- Every row support validator returns the same result after sorting. -/
theorem rowsSupported_sortAffineRows
    (r : Nat) (rows : List Witnora.G5Trace.Row) :
    (sortAffineRows rows).all (rowSupported r) =
      rows.all (rowSupported r) := by
  induction rows with
  | nil => rfl
  | cons row rest ih =>
      have hTail :
          rest.all (rowSupported r ∘ sortAffineRow) =
            rest.all (rowSupported r) := by
        simpa only [sortAffineRows, List.all_map] using ih
      simp [sortAffineRows, rowSupported_sortAffineRow, hTail]

/-- All three booleans in the full semantic affine-extraction check
    are now invariant under deterministic sorting of Nodup supports. -/
theorem checkSemanticExactAffine_sortAffineRows_of_nodup
    (r : Nat) (source : CNF) (rows : List Witnora.G5Trace.Row)
    (hNodup : ∀ row ∈ rows, row.coefficients.Nodup) :
    checkSemanticExactAffine r source (sortAffineRows rows) =
      checkSemanticExactAffine r source rows := by
  unfold checkSemanticExactAffine
  rw [rowsSupported_sortAffineRows r rows,
      checkInitialRows_sortAffineRows source rows hNodup,
      reverseCoverage_sortAffineRows source rows hNodup]

/-- The executable arity/positive-ID/Nodup validator itself certifies
    duplicate-freedom of every accepted row. -/
theorem rowSupported_implies_nodup
    (r : Nat) (row : Witnora.G5Trace.Row)
    (h : rowSupported r row = true) :
    row.coefficients.Nodup := by
  unfold rowSupported at h
  simp at h
  exact h.1.2

/-- Exact source-bound affine acceptance supplies all Nodup premises
    needed to apply permutation invariance to every row. -/
theorem semanticAffine_rows_nodup
    (r : Nat) (source : CNF) (rows : List Witnora.G5Trace.Row)
    (h : checkSemanticExactAffine r source rows = true) :
    ∀ row ∈ rows, row.coefficients.Nodup := by
  have hSupport : rows.all (rowSupported r) = true := by
    unfold checkSemanticExactAffine at h
    simp at h
    exact h.1.1
  intro row hr
  exact rowSupported_implies_nodup r row
    (List.all_eq_true.mp hSupport row hr)

/-- Main syntactic normalization theorem: *every* accepted semantic
    affine witness stays accepted by the original complete source checker
    after canonically sorting all row coefficients. -/
theorem checkSemanticExactAffine_sortAffineRows
    (r : Nat) (source : CNF) (rows : List Witnora.G5Trace.Row)
    (h : checkSemanticExactAffine r source rows = true) :
    checkSemanticExactAffine r source (sortAffineRows rows) = true := by
  have hNodup := semanticAffine_rows_nodup r source rows h
  rw [checkSemanticExactAffine_sortAffineRows_of_nodup
    r source rows hNodup]
  exact h

#print axioms Witnora.TC063PatternPermutation.checkSemanticExactAffine_sortAffineRows

#print axioms Witnora.TC063PatternPermutation.reverseCoverage_sortAffineRows

#print axioms Witnora.TC063PatternPermutation.signedClause_permutation_match
#print axioms Witnora.TC063PatternPermutation.checkClauseCoverage_signedClauses_perm

#print axioms Witnora.TC063PatternPermutation.checkInitialRows_sortAffineRows

#print axioms Witnora.TC063PatternPermutation.checkPattern_perm_of_nodup
#print axioms Witnora.TC063PatternPermutation.checkPattern_sortVariables

#print axioms Witnora.TC063PatternPermutation.allBits_member_length
#print axioms Witnora.TC063PatternPermutation.nodup_vars_realize_bits
#print axioms Witnora.TC063PatternPermutation.checkPattern_iff_patternCovered

end Witnora.TC063PatternPermutation
