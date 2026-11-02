import Witnora.G5Extraction

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
