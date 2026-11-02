import Witnora.ExactSignedXorCNF

/-!
# TC-063 exact clause-coverage invariance under literal permutation

The boolean source-coverage gate must not depend on literal ordering:
a source clause subsumes a proposed forbidden clause exactly when it
subsumes any permutation of the same literal multiset. This is the first
checker-level lemma needed for full canonical affine witness normalization.
Semantic parity invariance alone does not establish this result.
-/

namespace Witnora.TC063ClausePermutation

open Witnora.Concrete
open Witnora.FiniteXor
open Witnora.G5Extraction

theorem clauseSubsumes_expected_perm
    (source expected other : List Literal)
    (hperm : expected.Perm other) :
    clauseSubsumes source expected = clauseSubsumes source other := by
  have heq : (fun lit : Literal => decide (lit ∈ expected)) =
      (fun lit : Literal => decide (lit ∈ other)) := by
    funext lit
    simp [hperm.mem_iff]
  unfold clauseSubsumes
  rw [heq]

theorem checkClauseCoverage_expected_perm
    (cnf : CNF) (expected other : List Literal)
    (hperm : expected.Perm other) :
    checkClauseCoverage cnf expected =
      checkClauseCoverage cnf other := by
  have heq :
      (fun source => clauseSubsumes source expected) =
      (fun source => clauseSubsumes source other) := by
    funext source
    exact clauseSubsumes_expected_perm source expected other hperm
  unfold checkClauseCoverage
  rw [heq]

theorem signForbiddenClause_perm
    (fixed other : List (Nat × Bool))
    (hperm : fixed.Perm other) :
    (signForbiddenClause fixed).Perm (signForbiddenClause other) := by
  unfold signForbiddenClause
  exact hperm.map _

theorem checkClauseCoverage_permuted_forbidden
    (cnf : CNF) (fixed other : List (Nat × Bool))
    (hperm : fixed.Perm other) :
    checkClauseCoverage cnf (signForbiddenClause fixed) =
      checkClauseCoverage cnf (signForbiddenClause other) := by
  exact checkClauseCoverage_expected_perm cnf _ _
    (signForbiddenClause_perm fixed other hperm)

/-- A permutation of variable positions can transport every same-length
    Boolean pattern, keeping the zipped variable/bit pairs and the bits
    themselves permuted. This requires no assignment enumeration. -/
theorem zip_pattern_transport
    {vars other : List Nat} (hperm : vars.Perm other)
    (bitsOther : List Bool) (hlen : bitsOther.length = other.length) :
    ∃ bits : List Bool,
      bits.length = vars.length ∧
      (List.zip vars bits).Perm (List.zip other bitsOther) ∧
      bits.Perm bitsOther := by
  induction hperm generalizing bitsOther with
  | nil =>
      cases bitsOther with
      | nil => exact ⟨[], rfl, List.Perm.nil, List.Perm.nil⟩
      | cons b rest => simp at hlen
  | @cons v xs ys hp ih =>
      cases bitsOther with
      | nil => simp at hlen
      | cons b bs =>
          have htail : bs.length = ys.length := by
            simpa using hlen
          obtain ⟨bits, hbLen, hpairs, hbits⟩ := ih bs htail
          refine ⟨b :: bits, ?_, ?_, ?_⟩
          · simp [hbLen]
          · simpa using (List.Perm.cons (v, b) hpairs)
          · exact List.Perm.cons b hbits
  | @swap x y xs =>
      cases bitsOther with
      | nil => simp at hlen
      | cons b rest =>
          cases rest with
          | nil => simp at hlen
          | cons d tail =>
              have htail : tail.length = xs.length := by
                simpa using hlen
              refine ⟨d :: b :: tail, by simp [htail], ?_, ?_⟩
              · simpa using (List.Perm.swap (x, b) (y, d)
                  (List.zip xs tail))
              · exact List.Perm.swap b d tail
  | @trans xs ys zs hxy hyz ihxy ihyz =>
      obtain ⟨mid, hmidlen, hmiddle, hmidbits⟩ :=
        ihyz bitsOther hlen
      obtain ⟨bits, hbitsLen, hfirst, hfirstBits⟩ :=
        ihxy mid hmidlen
      exact ⟨bits, hbitsLen, hfirst.trans hmiddle,
        hfirstBits.trans hmidbits⟩

/-- XOR of forbidden Boolean patterns is invariant under any reordering. -/
theorem parityBits_perm
    {bits other : List Bool} (hperm : bits.Perm other) :
    parityBits bits = parityBits other := by
  induction hperm with
  | nil => rfl
  | cons b hp ih =>
      simpa only [parityBits] using congrArg (Bool.xor b) ih
  | swap b d xs =>
      cases b <;> cases d <;> simp [parityBits, Bool.xor]
  | trans hp hq ihp ihq =>
      exact ihp.trans ihq

/-- Every forbidden assignment of the permuted variable row has an
    equally forbidden assignment of the original row with identical
    signed-literal coverage. Thus the actual Boolean extraction checker
    is sound under arbitrary variable-order permutations. -/
theorem checkPattern_true_of_perm
    (cnf : CNF) {vars other : List Nat}
    (hperm : vars.Perm other) (rhs : Bool)
    (hcheck : checkPattern cnf vars rhs = true) :
    checkPattern cnf other rhs = true := by
  unfold checkPattern at hcheck ⊢
  apply List.all_eq_true.mpr
  intro bitsOther hbadOther
  have hmemberOther : bitsOther ∈ allBits other.length :=
    (List.mem_filter.mp hbadOther).1
  have hwrongOther : parityBits bitsOther ≠ rhs := by
    simpa using (List.mem_filter.mp hbadOther).2
  have hlen : bitsOther.length = other.length :=
    Witnora.ExactSignedXorCNF.allBits_member_length
      other.length bitsOther hmemberOther
  obtain ⟨bits, hbitsLen, hpair, hbitsPerm⟩ :=
    zip_pattern_transport hperm bitsOther hlen
  have hmember : bits ∈ allBits vars.length := by
    simpa [hbitsLen] using allBits_complete bits
  have hwrong : parityBits bits ≠ rhs := by
    rw [parityBits_perm hbitsPerm]
    exact hwrongOther
  have hbad : bits ∈ generateForbiddenPatterns vars.length rhs := by
    simp [generateForbiddenPatterns, hmember, hwrong]
  have hcovered :
      checkClauseCoverage cnf
        (signForbiddenClause (List.zip vars bits)) = true :=
    List.all_eq_true.mp hcheck bits hbad
  rw [← checkClauseCoverage_permuted_forbidden cnf
    (List.zip vars bits) (List.zip other bitsOther) hpair]
  exact hcovered

/-- The source checker verdict itself is invariant under any variable
    permutation, not merely the mathematical parity equation. -/
theorem checkPattern_perm
    (cnf : CNF) {vars other : List Nat}
    (hperm : vars.Perm other) (rhs : Bool) :
    checkPattern cnf vars rhs = checkPattern cnf other rhs := by
  by_cases h : checkPattern cnf vars rhs = true
  · have hr := checkPattern_true_of_perm cnf hperm rhs h
    simp [h, hr]
  · have hl : checkPattern cnf vars rhs = false := by
      cases hx : checkPattern cnf vars rhs with
      | false => rfl
      | true => exact False.elim (h hx)
    have hr : checkPattern cnf other rhs = false := by
      cases hx : checkPattern cnf other rhs with
      | false => rfl
      | true =>
          have hback := checkPattern_true_of_perm cnf hperm.symm rhs hx
          exact False.elim (h hback)
    simp [hl, hr]

/-- A forbidden signed clause generated from a row stays present up
    to literal ordering after any variable permutation. This is the
    source-set bridge required to normalize full affine components. -/
theorem generated_signed_clause_perm_exists
    {vars other : List Nat} (hperm : vars.Perm other)
    (rhs : Bool) (clause : List Literal)
    (hmem : clause ∈ generateSignedClauses vars rhs) :
    ∃ translated ∈ generateSignedClauses other rhs,
      clause.Perm translated := by
  change clause ∈ (generateForbiddenPatterns vars.length rhs).map
    (fun bad => signForbiddenClause (List.zip vars bad)) at hmem
  obtain ⟨bad, hbad, rfl⟩ := List.mem_map.mp hmem
  have hbits : bad ∈ allBits vars.length :=
    (List.mem_filter.mp hbad).1
  have hwrong : parityBits bad ≠ rhs := by
    simpa using (List.mem_filter.mp hbad).2
  have hlen : bad.length = vars.length :=
    Witnora.ExactSignedXorCNF.allBits_member_length vars.length bad hbits
  obtain ⟨translatedBits, htranslatedLen, hpairs, hbitsPerm⟩ :=
    zip_pattern_transport hperm.symm bad hlen
  have htranslatedMember : translatedBits ∈ allBits other.length := by
    simpa [htranslatedLen] using allBits_complete translatedBits
  have htranslatedWrong : parityBits translatedBits ≠ rhs := by
    rw [parityBits_perm hbitsPerm]
    exact hwrong
  have hbadOther :
      translatedBits ∈ generateForbiddenPatterns other.length rhs := by
    simp [generateForbiddenPatterns, htranslatedMember, htranslatedWrong]
  refine ⟨signForbiddenClause (List.zip other translatedBits), ?_, ?_⟩
  · exact List.mem_map.mpr ⟨translatedBits, hbadOther, rfl⟩
  · exact (signForbiddenClause_perm _ _ hpairs).symm

example :
    checkClauseCoverage
      [[(1, true), (2, false)]]
      [(1, true), (2, false)] =
    checkClauseCoverage
      [[(1, true), (2, false)]]
      [(2, false), (1, true)] := by decide

#print axioms Witnora.TC063ClausePermutation.clauseSubsumes_expected_perm
#print axioms Witnora.TC063ClausePermutation.checkClauseCoverage_expected_perm
#print axioms Witnora.TC063ClausePermutation.signForbiddenClause_perm
#print axioms Witnora.TC063ClausePermutation.zip_pattern_transport
#print axioms Witnora.TC063ClausePermutation.parityBits_perm
#print axioms Witnora.TC063ClausePermutation.checkPattern_perm
#print axioms Witnora.TC063ClausePermutation.generated_signed_clause_perm_exists

end Witnora.TC063ClausePermutation
