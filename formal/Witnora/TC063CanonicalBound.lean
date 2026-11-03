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

#print axioms Witnora.TC063CanonicalBound.checkInitialRows_boundedCanonRows

#print axioms Witnora.TC063CanonicalBound.canonicalSupport_idempotent
#print axioms Witnora.TC063CanonicalBound.canonicalSupport_perm_of_bounded

#print axioms Witnora.TC063CanonicalBound.canonicalSupport_nodup

#print axioms Witnora.TC063CanonicalBound.mem_canonicalSupport_iff
#print axioms Witnora.TC063CanonicalBound.mem_canonicalSupport_idempotent

end Witnora.TC063CanonicalBound
