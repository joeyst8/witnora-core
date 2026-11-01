import Witnora.G5IndexedScheduledEmitter
import Witnora.G5EliminationInvariant

/-!
# Global model invariance of indexed XOR row replacement

The DAG-backed source and the independent row-list interpreter use
target-first XOR replacement. Keeping the source row unchanged makes
the transformation logically reversible for the *entire* row table,
not just a pair of equations.

This is the semantic bridge from indexed replay to Gaussian elimination:
row-list order and exact sparse-coefficient order need not match.
-/

namespace Witnora.G5GlobalRowModelInvariant

open Witnora.G5Trace
open Witnora.G5Certificate
open Witnora.G5EliminationInvariant
open Witnora.G5RowTableRelation
open Witnora.G5DriverXorOrderBridge

/-- A complete row table holds when every successfully looked-up slot
    holds, including tables with no rows. -/
def SlotsHold (bound : Nat) (rows : List Row) (a : Nat → Bool) : Prop :=
  ∀ slot row, rows[slot]? = some row → RowHolds bound row a

/-- Any legal indexed target XOR replacement preserves *all* satisfying
    assignments of the entire working-row table, in both directions. -/
theorem xor_update_models_iff
    (bound : Nat) (rows : List Row) (a : Nat → Bool)
    (target source : Nat) (targetRow sourceRow : Row)
    (hne : target ≠ source)
    (ht : rows[target]? = some targetRow)
    (hs : rows[source]? = some sourceRow) :
    SlotsHold bound rows a ↔
    SlotsHold bound (rows.set target (xorRow targetRow sourceRow)) a := by
  constructor
  · intro hall slot row hlookup
    by_cases heq : slot = target
    · subst slot
      have hnew := row_lookup_set_self rows target targetRow
        (xorRow targetRow sourceRow) ht
      have hr : row = xorRow targetRow sourceRow :=
        Option.some.inj (hlookup.symm.trans hnew)
      subst row
      exact xorRow_holds bound targetRow sourceRow a
        (hall target targetRow ht) (hall source sourceRow hs)
    · have hold : rows[slot]? = some row := by
        rw [← row_lookup_set_other rows target slot
          (xorRow targetRow sourceRow) (Ne.symm heq)]
        exact hlookup
      exact hall slot row hold
  · intro hall slot row hlookup
    have hsourceNew : (rows.set target
        (xorRow targetRow sourceRow))[source]? = some sourceRow := by
      rw [row_lookup_set_other rows target source
        (xorRow targetRow sourceRow) hne]
      exact hs
    have hsource : RowHolds bound sourceRow a :=
      hall source sourceRow hsourceNew
    have htargetNew := row_lookup_set_self rows target targetRow
      (xorRow targetRow sourceRow) ht
    have hxor : RowHolds bound (xorRow targetRow sourceRow) a :=
      hall target (xorRow targetRow sourceRow) htargetNew
    have htargetHold : RowHolds bound targetRow a := by
      have hreverse : RowHolds bound (xorRow sourceRow targetRow) a :=
        (xorRow_comm_holds bound sourceRow targetRow a).mpr hxor
      exact ((xor_replacement_iff bound sourceRow targetRow a).mpr
        ⟨hsource, hreverse⟩).2
    by_cases heq : slot = target
    · subst slot
      have hr : row = targetRow :=
        Option.some.inj (hlookup.symm.trans ht)
      subst row
      exact htargetHold
    · have hnew : (rows.set target
          (xorRow targetRow sourceRow))[slot]? = some row := by
        rw [row_lookup_set_other rows target slot
          (xorRow targetRow sourceRow) (Ne.symm heq)]
        exact hlookup
      exact hall slot row hnew

/-- Consequently, the independent replay's actual ADD_ROW_XOR step is
    logically reversible across all rows, whenever the step is legal. -/
theorem applyStep_xor_models_iff
    (bound : Nat) (rows next : List Row)
    (target source : Nat) (a : Nat → Bool)
    (h : applyStep rows (.addXor target source) = some next) :
    SlotsHold bound rows a ↔ SlotsHold bound next a := by
  by_cases hne : target ≠ source
  · cases ht : rows[target]? with
    | none =>
        simp [applyStep, hne, ht] at h
    | some targetRow =>
        cases hs : rows[source]? with
        | none =>
            simp [applyStep, hne, ht, hs] at h
        | some sourceRow =>
            have hexact := applyStep_addXor_exact rows target source
              targetRow sourceRow hne ht hs
            have heq : next = rows.set target
                (xorRow targetRow sourceRow) :=
              Option.some.inj (h.symm.trans hexact)
            subst next
            exact xor_update_models_iff bound rows a
              target source targetRow sourceRow hne ht hs
  · have heq : target = source := Decidable.not_not.mp hne
    subst source
    simp [applyStep] at h

#print axioms Witnora.G5GlobalRowModelInvariant.xor_update_models_iff
#print axioms Witnora.G5GlobalRowModelInvariant.applyStep_xor_models_iff

end Witnora.G5GlobalRowModelInvariant
