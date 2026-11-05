import Witnora.TC063PatternPermutation

/-!
# Canonical bounded sparse support for TC-063

The source-bound semantic-affine witness can now be sorted while preserving
its full extraction acceptance.  This module begins the remaining bridge
from finite support membership to the strict bounded canonicalSupport
representation used by the executable G5 certificate checker.
-/

namespace Witnora.TC063CanonicalBound

open Witnora.Concrete
open Witnora.SparseBridge
open Witnora.FiniteXor
open Witnora.G5Trace
open Witnora.G5Extraction
open Witnora.ComponentPartition
open Witnora.G5InitialSupportCoverage
open Witnora.SemanticSAF
open Witnora.TC063CompletenessReduction
open Witnora.TC063Direct
open Witnora.ExactAffineMembership
open Witnora.TC063CanonicalAffineBridge
open Witnora.TC063PatternPermutation

/-- Bounded canonical support contains exactly those original coefficients
    whose numeric IDs lie strictly below the bound. -/
theorem mem_canonicalSupport_iff
    (bound v : Nat) (coeff : List Nat) :
    v ∈ canonicalSupport bound coeff ↔
      v < bound ∧ v ∈ coeff := by
  induction bound with
  | zero =>
      simp [canonicalSupport]
  | succ n ih =>
      simp only [canonicalSupport, List.mem_append]
      by_cases hn : n ∈ coeff
      · have hFlag : decide (n ∈ coeff) = true := by simp [hn]
        simp only [hFlag, ite_true, List.mem_singleton]
        constructor
        · intro h
          rcases h with hOld | hAt
          · obtain ⟨hLt, hCoeff⟩ := (ih.mp hOld)
            exact ⟨by omega, hCoeff⟩
          · subst v
            exact ⟨by omega, hn⟩
        · rintro ⟨hLt, hCoeff⟩
          by_cases hv : v = n
          · exact Or.inr hv
          · exact Or.inl (ih.mpr ⟨by omega, hCoeff⟩)
      · have hFlag : decide (n ∈ coeff) = false := by simp [hn]
        simp only [hFlag, Bool.false_eq_true, ite_false, List.not_mem_nil, or_false]
        constructor
        · intro h
          obtain ⟨hLt, hCoeff⟩ := (ih.mp h)
          exact ⟨by omega, hCoeff⟩
        · rintro ⟨hLt, hCoeff⟩
          apply ih.mpr
          constructor
          · have hv : v ≠ n := by
              intro hEq
              subst v
              exact hn hCoeff
            omega
          · exact hCoeff

/-- The membership predicate of canonical support is idempotent for every
    bound and every raw coefficient list, even with duplicates. -/
theorem mem_canonicalSupport_idempotent
    (bound v : Nat) (coeff : List Nat) :
    v ∈ canonicalSupport bound (canonicalSupport bound coeff) ↔
      v ∈ canonicalSupport bound coeff := by
  rw [mem_canonicalSupport_iff]
  constructor
  · exact And.right
  · intro h
    exact ⟨((mem_canonicalSupport_iff bound v coeff).mp h).1, h⟩

/-- The bounded canonical support enumerates every in-range variable
    at most once, even when its input contains duplicates. -/
theorem canonicalSupport_nodup
    (bound : Nat) (coeff : List Nat) :
    (canonicalSupport bound coeff).Nodup := by
  induction bound with
  | zero => simp [canonicalSupport]
  | succ n ih =>
      by_cases hn : n ∈ coeff
      · have hExpand :
            canonicalSupport (n + 1) coeff =
              canonicalSupport n coeff ++ [n] := by
          simp [canonicalSupport, hn]
        rw [hExpand]
        have hNot : n ∉ canonicalSupport n coeff := by
          intro h
          have hLt := (mem_canonicalSupport_iff n n coeff).mp h |>.1
          omega
        apply (List.pairwise_append).2
        refine ⟨ih, by simp, ?_⟩
        intro a ha b hb
        have hbEq : b = n := by simpa using hb
        subst b
        intro heq
        subst a
        exact hNot ha
      · have hExpand :
            canonicalSupport (n + 1) coeff =
              canonicalSupport n coeff := by
          simp [canonicalSupport, hn]
        rw [hExpand]
        exact ih

/-- The canonical scan is extensional in the membership predicates
    of indices below its exclusive bound. -/
theorem canonicalSupport_congr_on_bound
    (bound : Nat) (xs ys : List Nat) :
    (∀ v, v < bound → (v ∈ xs ↔ v ∈ ys)) →
      canonicalSupport bound xs = canonicalSupport bound ys := by
  induction bound with
  | zero =>
      intro _
      rfl
  | succ n ih =>
      intro h
      have hRest : canonicalSupport n xs = canonicalSupport n ys :=
        ih (by
          intro v hv
          exact h v (by omega))
      have hFlag : decide (n ∈ xs) = decide (n ∈ ys) := by
        by_cases hx : n ∈ xs
        · have hy : n ∈ ys := (h n (by omega)).mp hx
          simp [hx, hy]
        · have hy : n ∉ ys := by
            intro hy
            exact hx ((h n (by omega)).mpr hy)
          simp [hx, hy]
      simp only [canonicalSupport]
      rw [hRest, hFlag]

/-- The executable bounded canonicalizer is exactly idempotent, not just
    semantically or permutation-equivalent. -/
theorem canonicalSupport_idempotent
    (bound : Nat) (coeff : List Nat) :
    canonicalSupport bound (canonicalSupport bound coeff) =
      canonicalSupport bound coeff := by
  apply canonicalSupport_congr_on_bound bound
    (canonicalSupport bound coeff) coeff
  intro v hv
  constructor
  · intro h
    exact ((mem_canonicalSupport_iff bound v coeff).mp h).2
  · intro h
    exact (mem_canonicalSupport_iff bound v coeff).mpr ⟨hv, h⟩

/-- A finite duplicate-free natural-number list contains each name
    either once or not at all; we prove the exact count formula. -/
private theorem nodup_count_nat
    (xs : List Nat) :
    xs.Nodup → ∀ v : Nat,
      List.count v xs = if v ∈ xs then 1 else 0 := by
  induction xs with
  | nil =>
      intro _ v
      simp
  | cons x rest ih =>
      intro h v
      have hNot : x ∉ rest := (List.nodup_cons.mp h).1
      have hRest : rest.Nodup := (List.nodup_cons.mp h).2
      by_cases heq : v = x
      · subst v
        have hTail : List.count x rest = 0 := by
          simpa [hNot] using ih hRest x
        simp [List.count_cons, hTail, hNot]
      · have hTail := ih hRest v
        have hNe : x ≠ v := Ne.symm heq
        simp [List.count_cons, heq, hNe, hTail]

/-- Two finite duplicate-free variable lists with exactly the same
    variable membership are permutations in Lean's literal List.Perm. -/
theorem nodup_perm_of_mem_iff
    (xs ys : List Nat)
    (hX : xs.Nodup) (hY : ys.Nodup)
    (hMem : ∀ v, v ∈ xs ↔ v ∈ ys) :
    xs.Perm ys := by
  apply List.perm_iff_count.mpr
  intro v
  rw [nodup_count_nat xs hX v, nodup_count_nat ys hY v]
  simp only [hMem v]

/-- Under a strict finite upper bound, canonicalSupport is a genuine
    permutation of any Nodup coefficient list, enabling source-checker
    transport without proving facts about the insertion-sort algorithm. -/
theorem canonicalSupport_perm_of_bounded
    (bound : Nat) (coeff : List Nat)
    (hNodup : coeff.Nodup)
    (hBound : ∀ v ∈ coeff, v < bound) :
    (canonicalSupport bound coeff).Perm coeff := by
  apply nodup_perm_of_mem_iff
    (canonicalSupport bound coeff) coeff
    (canonicalSupport_nodup bound coeff) hNodup
  intro v
  constructor
  · intro h
    exact ((mem_canonicalSupport_iff bound v coeff).mp h).2
  · intro h
    exact (mem_canonicalSupport_iff bound v coeff).mpr
      ⟨hBound v h, h⟩

/-- Canonicalize every affine row directly with the bounded sparse
    implementation, retaining its right-hand side and row order. -/
def boundedCanonRow (bound : Nat) (row : Row) : Row :=
  { row with coefficients := canonicalSupport bound row.coefficients }

def boundedCanonRows (bound : Nat) (rows : List Row) : List Row :=
  rows.map (boundedCanonRow bound)

/-- The actual source-bound G5 extraction check is unchanged if
    duplicate-free input rows are in range and we canonically scan them. -/
theorem checkInitialRows_boundedCanonRows
    (bound : Nat) (source : CNF) (rows : List Row) :
    (∀ row ∈ rows, row.coefficients.Nodup) →
    (∀ row ∈ rows, ∀ v ∈ row.coefficients, v < bound) →
    checkInitialRows source (boundedCanonRows bound rows) =
      checkInitialRows source rows := by
  induction rows with
  | nil =>
      intro _ _
      rfl
  | cons row rest ih =>
      intro hNodup hBound
      have hHead : row.coefficients.Nodup :=
        hNodup row (by simp)
      have hHeadBound : ∀ v ∈ row.coefficients, v < bound :=
        hBound row (by simp)
      have hTailNo : ∀ r ∈ rest, r.coefficients.Nodup := by
        intro r hr
        exact hNodup r (by simp [hr])
      have hTailBound : ∀ r ∈ rest, ∀ v ∈ r.coefficients, v < bound := by
        intro r hr
        exact hBound r (by simp [hr])
      have hPerm := canonicalSupport_perm_of_bounded bound
        row.coefficients hHead hHeadBound
      have hHeadEq :
          checkPattern source (canonicalSupport bound row.coefficients) row.rhs =
            checkPattern source row.coefficients row.rhs :=
        checkPattern_perm_of_nodup source
          (canonicalSupport bound row.coefficients)
          row.coefficients row.rhs hPerm
          (canonicalSupport_nodup bound row.coefficients)
      have hTailEq :
          rest.all ((fun r => checkPattern source r.coefficients r.rhs) ∘
              boundedCanonRow bound) =
            rest.all (fun r => checkPattern source r.coefficients r.rhs) := by
        simpa only [checkInitialRows, boundedCanonRows, List.all_map]
          using ih hTailNo hTailBound
      simp [boundedCanonRows, boundedCanonRow, checkInitialRows,
        hHeadEq, hTailEq]

/-- Reverse CNF clause coverage is invariant for the entire family
    of per-row bounded canonical supports. -/
theorem checkClauseCoverage_expanded_boundedCanonRows
    (bound : Nat) (rows : List Row) (expected : List Literal) :
    (∀ row ∈ rows, row.coefficients.Nodup) →
    (∀ row ∈ rows, ∀ v ∈ row.coefficients, v < bound) →
    checkClauseCoverage (expanded (boundedCanonRows bound rows)) expected =
      checkClauseCoverage (expanded rows) expected := by
  induction rows with
  | nil =>
      intro _ _
      rfl
  | cons row rest ih =>
      intro hNodup hBound
      have hHead : row.coefficients.Nodup :=
        hNodup row (by simp)
      have hHeadBound : ∀ v ∈ row.coefficients, v < bound :=
        hBound row (by simp)
      have hTailNo : ∀ r ∈ rest, r.coefficients.Nodup := by
        intro r hr
        exact hNodup r (by simp [hr])
      have hTailBound : ∀ r ∈ rest, ∀ v ∈ r.coefficients, v < bound := by
        intro r hr
        exact hBound r (by simp [hr])
      change checkClauseCoverage
          (generateSignedClauses (canonicalSupport bound row.coefficients)
            row.rhs ++ expanded (boundedCanonRows bound rest)) expected =
        checkClauseCoverage
          (generateSignedClauses row.coefficients row.rhs ++
            expanded rest) expected
      rw [checkClauseCoverage_append, checkClauseCoverage_append]
      have hPerm := canonicalSupport_perm_of_bounded bound
        row.coefficients hHead hHeadBound
      have hRow :=
        checkClauseCoverage_signedClauses_perm
          row.coefficients (canonicalSupport bound row.coefficients)
          row.rhs expected hPerm.symm hHead
      rw [← hRow, ih hTailNo hTailBound]

/-- Preserve source coverage of all clauses, not only individually
    extracted XOR patterns. -/
theorem reverseCoverage_boundedCanonRows
    (bound : Nat) (source : CNF) (rows : List Row)
    (hNodup : ∀ row ∈ rows, row.coefficients.Nodup)
    (hBound : ∀ row ∈ rows, ∀ v ∈ row.coefficients, v < bound) :
    source.all (checkClauseCoverage (expanded (boundedCanonRows bound rows))) =
      source.all (checkClauseCoverage (expanded rows)) := by
  induction source with
  | nil => rfl
  | cons clause rest ih =>
      simp only [List.all_cons]
      rw [checkClauseCoverage_expanded_boundedCanonRows
        bound rows clause hNodup hBound, ih]

/-- Canonical support has exactly the same arity, positivity,
    and duplicate-free validation as any bounded Nodup input row. -/
theorem rowSupported_boundedCanonRow
    (r bound : Nat) (row : Row)
    (hNodup : row.coefficients.Nodup)
    (hBound : ∀ v ∈ row.coefficients, v < bound) :
    rowSupported r (boundedCanonRow bound row) =
      rowSupported r row := by
  have hp := canonicalSupport_perm_of_bounded bound row.coefficients
    hNodup hBound
  have hLen := hp.length_eq
  have hDup := hp.nodup_iff
  have hPos := all_perm (fun v => decide (v > 0)) hp
  simp [rowSupported, boundedCanonRow, hLen, hDup, hPos]

/-- Transport row-level validation across a list of bounded
    canonicalized affine equations. -/
theorem rowsSupported_boundedCanonRows
    (r bound : Nat) (rows : List Row) :
    (∀ row ∈ rows, row.coefficients.Nodup) →
    (∀ row ∈ rows, ∀ v ∈ row.coefficients, v < bound) →
    (boundedCanonRows bound rows).all (rowSupported r) =
      rows.all (rowSupported r) := by
  induction rows with
  | nil =>
      intro _ _
      rfl
  | cons row rest ih =>
      intro hNodup hBound
      have hHead : row.coefficients.Nodup :=
        hNodup row (by simp)
      have hHeadBound : ∀ v ∈ row.coefficients, v < bound :=
        hBound row (by simp)
      have hTailNo : ∀ r ∈ rest, r.coefficients.Nodup := by
        intro r hr
        exact hNodup r (by simp [hr])
      have hTailBound : ∀ r ∈ rest, ∀ v ∈ r.coefficients, v < bound := by
        intro r hr
        exact hBound r (by simp [hr])
      have hTailEq :
          rest.all (rowSupported r ∘ boundedCanonRow bound) =
            rest.all (rowSupported r) := by
        simpa only [boundedCanonRows, List.all_map]
          using ih hTailNo hTailBound
      simp [boundedCanonRows, rowSupported_boundedCanonRow
        r bound row hHead hHeadBound, hTailEq]

/-- Every component accepted by the semantic affine CNF extraction
    checker remains accepted after strict bounded canonicalization. -/
theorem checkSemanticExactAffine_boundedCanonRows
    (r bound : Nat) (source : CNF) (rows : List Row)
    (hCheck : checkSemanticExactAffine r source rows = true)
    (hBound : ∀ row ∈ rows, ∀ v ∈ row.coefficients, v < bound) :
    checkSemanticExactAffine r source (boundedCanonRows bound rows) = true := by
  have hNodup := semanticAffine_rows_nodup r source rows hCheck
  have hEq :
      checkSemanticExactAffine r source (boundedCanonRows bound rows) =
        checkSemanticExactAffine r source rows := by
    unfold checkSemanticExactAffine
    rw [rowsSupported_boundedCanonRows r bound rows hNodup hBound,
        checkInitialRows_boundedCanonRows bound source rows hNodup hBound,
        reverseCoverage_boundedCanonRows bound source rows hNodup hBound]
  rw [hEq]
  exact hCheck

/-- Explicit largest-variable fold; this avoids choosing a
    nonconstructive bound or relying on the numerical density of IDs. -/
def maxVariable : List Nat → Nat
  | [] => 0
  | v :: rest => max v (maxVariable rest)

theorem le_maxVariable_of_mem (xs : List Nat) :
    ∀ v ∈ xs, v ≤ maxVariable xs := by
  induction xs with
  | nil =>
      intro v hv
      simp at hv
  | cons x rest ih =>
      intro v hv
      rcases List.mem_cons.mp hv with heq | hRest
      · subst v
        exact Nat.le_max_left x (maxVariable rest)
      · exact Nat.le_trans (ih v hRest) (Nat.le_max_right x (maxVariable rest))

/-- The support schedule lists row variables directly, including repeats.
    This is finite and avoids enumerating every integer below max ID. -/
def supportRows (rows : List Row) : List Nat :=
  rows.flatMap (fun row => row.coefficients)

theorem row_membership_supportRows (rows : List Row) :
    ∀ row ∈ rows, ∀ v ∈ row.coefficients, v ∈ supportRows rows := by
  intro row hr v hv
  change v ∈ rows.flatMap (fun row => row.coefficients)
  exact List.mem_flatMap.mpr ⟨row, hr, hv⟩

def boundForRows (rows : List Row) : Nat :=
  maxVariable (supportRows rows) + 1

theorem rows_bounded_boundForRows (rows : List Row) :
    ∀ row ∈ rows, ∀ v ∈ row.coefficients, v < boundForRows rows := by
  intro row hr v hv
  have hMem := row_membership_supportRows rows row hr v hv
  have hLe := le_maxVariable_of_mem (supportRows rows) v hMem
  unfold boundForRows
  omega

/-- The resulting bounded canonical rows mechanically pass the *exact*
    canonical G5 row representation checker. -/
theorem checkCanonicalRows_boundedCanonRows
    (bound : Nat) (rows : List Row) :
    checkCanonicalRows bound (boundedCanonRows bound rows) = true := by
  unfold checkCanonicalRows
  apply List.all_eq_true.mpr
  intro row' hr'
  obtain ⟨row, _, hEq⟩ := List.mem_map.mp hr'
  subst row'
  simp [checkCanonicalRow, boundedCanonRow, canonicalSupport_idempotent]

/-- The original finite variable names form a complete schedule
    for every bounded canonical row. -/
theorem supportRows_covers_boundedCanonRows
    (bound : Nat) (rows : List Row) :
    Covered (supportRows rows) (boundedCanonRows bound rows) := by
  intro row' hr' v hv
  obtain ⟨row, hr, hEq⟩ := List.mem_map.mp hr'
  subst row'
  have hOld : v ∈ row.coefficients :=
    ((mem_canonicalSupport_iff bound v row.coefficients).mp hv).2
  exact row_membership_supportRows rows row hr v hOld

/-- The explicit schedule uses only variable names below its finite
    bound.  No integer interval is materialized. -/
theorem supportRows_in_range (rows : List Row) :
    ∀ v ∈ supportRows rows, v < boundForRows rows := by
  intro v hv
  have hLe := le_maxVariable_of_mem (supportRows rows) v hv
  unfold boundForRows
  omega

/-!
## TC-063 family-level logical completeness

The complete finite-bound construction now supplies all the premises
of the already-checked G5 indexed emitter and G14 family reduction,
with no assumed canonical witness and no preexisting contradiction trace.
This establishes logical certificate completeness for precisely the
explicit CertifiedAffine/Family(c,r) predicate.  It does not establish
polynomial time or correspondence to all CPython runs.
-/

/-- Every machine-checker-certified exact affine CNF has an explicitly
    bounded, canonical, extraction-accepted G5 initial row representation
    and a finite complete variable schedule. -/
theorem certifiedAffine_has_canonicalWitness
    (r : Nat) (cnf : CNF) (h : CertifiedAffine r cnf) :
    CanonicalAffineWitness r cnf := by
  obtain ⟨rows, hCheck⟩ := h
  let bound := boundForRows rows
  have hBound :
      ∀ row ∈ rows, ∀ v ∈ row.coefficients, v < bound := by
    simpa only [bound] using rows_bounded_boundForRows rows
  refine ⟨bound, boundedCanonRows bound rows, supportRows rows,
    ?_, ?_, ?_, ?_⟩
  · exact checkSemanticExactAffine_boundedCanonRows
      r bound cnf rows hCheck hBound
  · exact checkCanonicalRows_boundedCanonRows bound rows
  · exact supportRows_covers_boundedCanonRows bound rows
  · intro v hv
    exact supportRows_in_range rows v hv

/-- The formerly conditional local G5 completeness premise is
    established for all CertifiedAffine components of bounded arity r. -/
theorem certifiedAffine_g5_complete (r : Nat) :
    AffineG5Complete r := by
  exact affine_g5_complete_of_canonical_witness r
    (fun cnf h => certifiedAffine_has_canonicalWitness r cnf h)

/-- Every UNSAT instance in the explicitly defined restricted SAF
    family has a verified G14 branch cover whose selected components
    carry source-bound closed G5 contradiction certificates. -/
theorem tc063_restricted_family_cover_complete (c r : Nat) :
    UnsatCoverComplete c (Family c r) := by
  exact affine_g5_complete_implies_tc063_cover_complete c r
    (certifiedAffine_g5_complete r)

/-- The infinite restricted-family TC-063 *logical* result:
    source UNSAT if and only if an accepted finite G14/G5 cover exists.
    This is not a P-versus-NP separation or a polynomial runtime claim. -/
theorem tc063_restricted_family_unsat_iff_checked_cover
    (c r : Nat) (raw : List (List Int))
    (hFamily : Family c r raw) :
    (¬ ∃ a, Witnora.SignedSerialization.signedCNFHolds raw a) ↔
      ∃ cert : CoverData, cert.accepts c raw = true := by
  exact tc063_family_iff_of_affine_g5_complete c r
    (certifiedAffine_g5_complete r) raw hFamily

#print axioms Witnora.TC063CanonicalBound.certifiedAffine_has_canonicalWitness
#print axioms Witnora.TC063CanonicalBound.tc063_restricted_family_cover_complete
#print axioms Witnora.TC063CanonicalBound.tc063_restricted_family_unsat_iff_checked_cover

#print axioms Witnora.TC063CanonicalBound.checkCanonicalRows_boundedCanonRows
#print axioms Witnora.TC063CanonicalBound.supportRows_covers_boundedCanonRows

#print axioms Witnora.TC063CanonicalBound.checkSemanticExactAffine_boundedCanonRows

#print axioms Witnora.TC063CanonicalBound.reverseCoverage_boundedCanonRows

#print axioms Witnora.TC063CanonicalBound.checkInitialRows_boundedCanonRows

#print axioms Witnora.TC063CanonicalBound.canonicalSupport_idempotent
#print axioms Witnora.TC063CanonicalBound.canonicalSupport_perm_of_bounded

#print axioms Witnora.TC063CanonicalBound.canonicalSupport_nodup

#print axioms Witnora.TC063CanonicalBound.mem_canonicalSupport_iff
#print axioms Witnora.TC063CanonicalBound.mem_canonicalSupport_idempotent

end Witnora.TC063CanonicalBound
