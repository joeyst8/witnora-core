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
      change
        (v ∈ canonicalSupport n coeff ∨
          v ∈ (if decide (n ∈ coeff) then [n] else [])) ↔
          v < n + 1 ∧ v ∈ coeff
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
        simp only [hFlag, ite_false, List.not_mem_nil, or_false]
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
  rw [mem_canonicalSupport_iff, mem_canonicalSupport_iff]
  constructor
  · exact And.right
  · intro h
    exact ⟨(mem_canonicalSupport_iff bound v coeff).mp h |>.1, h⟩

#print axioms Witnora.TC063CanonicalBound.mem_canonicalSupport_iff
#print axioms Witnora.TC063CanonicalBound.mem_canonicalSupport_idempotent

end Witnora.TC063CanonicalBound
