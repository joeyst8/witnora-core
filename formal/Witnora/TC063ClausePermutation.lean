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

end Witnora.TC063ClausePermutation
