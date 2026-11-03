import Witnora.GeneralRUP

/-!
# Indexed reasons for general-CNF RUP steps

Every claimed propagated unit carries the ID of a present source or derived
clause supporting it; the final conflict also cites a present row. The Lean
checker looks up those rows and verifies all literals and accumulated
assumptions. The proof erases the indices into the already-proved general RUP
checker; therefore this module introduces no new SAT inference assumption.

Row lookup here uses List.getElem? and is not yet constant-time. A future
Array-backed implementation may improve checking cost without changing the
semantics or universal soundness theorem.
-/

namespace Witnora.GeneralRUPIndexed

open Witnora.Concrete
open Witnora.G5Extraction
open Witnora.GeneralRUP

structure UnitReason where
  forced : Literal
  rowID : Nat
deriving Repr, DecidableEq

structure IndexedRupStep where
  clause : List Literal
  units : List UnitReason
  conflictID : Nat
deriving Repr, DecidableEq

private theorem selected_row_mem
    {α : Type} (xs : List α) (idx : Nat) (row : α)
    (h : xs[idx]? = some row) : row ∈ xs := by
  induction xs generalizing idx with
  | nil =>
      cases idx <;> simp at h
  | cons head tail ih =>
      cases idx with
      | zero =>
          have heq : head = row := by simpa using h
          subst row
          simp
      | succ n =>
          have ht : tail[n]? = some row := by simpa using h
          simp [ih n ht]

/-- A unit reason must point to a present clause whose every other literal
    is falsified by prior assumptions. -/
def checkReason (database : CNF) (assumptions : List Literal)
    (reason : UnitReason) : Bool :=
  match database[reason.rowID]? with
  | none => false
  | some row =>
      decide (reason.forced ∈ row) &&
        row.all (fun lit =>
          decide (lit = reason.forced) || decide (flip lit ∈ assumptions))

/-- A conflict reason must point to a present, fully falsified clause. -/
def checkConflictAt (database : CNF) (assumptions : List Literal)
    (rowID : Nat) : Bool :=
  match database[rowID]? with
  | none => false
  | some row => row.all (fun lit => decide (flip lit ∈ assumptions))

theorem checkReason_implies_reference
    (database : CNF) (assumptions : List Literal)
    (reason : UnitReason)
    (h : checkReason database assumptions reason = true) :
    checkUnit database assumptions reason.forced = true := by
  unfold checkReason at h
  cases hr : database[reason.rowID]? with
  | none =>
      simp [hr] at h
  | some row =>
      have hparts :
          (decide (reason.forced ∈ row) &&
            row.all (fun lit =>
              decide (lit = reason.forced) ||
                decide (flip lit ∈ assumptions))) = true := by
        simpa [hr] using h
      have hmem := selected_row_mem database reason.rowID row hr
      exact List.any_eq_true.mpr ⟨row, hmem, hparts⟩

theorem checkConflictAt_implies_reference
    (database : CNF) (assumptions : List Literal)
    (rowID : Nat)
    (h : checkConflictAt database assumptions rowID = true) :
    checkConflict database assumptions = true := by
  unfold checkConflictAt at h
  cases hr : database[rowID]? with
  | none =>
      simp [hr] at h
  | some row =>
      have hchecked :
          row.all (fun lit => decide (flip lit ∈ assumptions)) = true := by
        simpa [hr] using h
      have hmem := selected_row_mem database rowID row hr
      exact List.any_eq_true.mpr ⟨row, hmem, hchecked⟩

def checkIndexedPropagation (database : CNF) :
    List Literal → List UnitReason → Nat → Bool
  | assumptions, [], conflictID =>
      checkConflictAt database assumptions conflictID
  | assumptions, reason :: rest, conflictID =>
      checkReason database assumptions reason &&
        checkIndexedPropagation database (reason.forced :: assumptions)
          rest conflictID

theorem checkIndexedPropagation_implies_reference
    (database : CNF) (assumptions : List Literal)
    (units : List UnitReason) (conflictID : Nat)
    (h : checkIndexedPropagation database assumptions units conflictID = true) :
    checkPropagation database assumptions (units.map UnitReason.forced) = true := by
  induction units generalizing assumptions with
  | nil =>
      exact checkConflictAt_implies_reference database assumptions
        conflictID (by simpa [checkIndexedPropagation] using h)
  | cons reason rest ih =>
      have hparts :
          checkReason database assumptions reason = true ∧
            checkIndexedPropagation database (reason.forced :: assumptions)
              rest conflictID = true := by
        simpa [checkIndexedPropagation, Bool.and_eq_true] using h
      have hstep :=
        checkReason_implies_reference database assumptions reason hparts.1
      have htail := ih (reason.forced :: assumptions) hparts.2
      simp [checkPropagation, hstep, htail]

def checkIndexedRupStep (database : CNF) (step : IndexedRupStep) : Bool :=
  checkIndexedPropagation database (step.clause.map flip)
    step.units step.conflictID

def eraseReasonIndices (step : IndexedRupStep) : RupStep :=
  { clause := step.clause, units := step.units.map UnitReason.forced }

theorem checkIndexedRupStep_implies_reference
    (database : CNF) (step : IndexedRupStep)
    (h : checkIndexedRupStep database step = true) :
    checkRupStep database (eraseReasonIndices step) = true := by
  exact checkIndexedPropagation_implies_reference
    database (step.clause.map flip) step.units step.conflictID h

/-- Indexed RUP proof checker; all unit and conflict references are exact
    zero-based row IDs, including rows appended by earlier checked steps. -/
def checkIndexedRup : CNF → List IndexedRupStep → Bool
  | database, [] => decide (([] : List Literal) ∈ database)
  | database, step :: rest =>
      if checkIndexedRupStep database step then
        checkIndexedRup (database ++ [step.clause]) rest
      else false

theorem checkIndexedRup_implies_reference
    (database : CNF) (trace : List IndexedRupStep)
    (h : checkIndexedRup database trace = true) :
    checkRup database (trace.map eraseReasonIndices) = true := by
  induction trace generalizing database with
  | nil =>
      simpa [checkIndexedRup, checkRup] using h
  | cons step rest ih =>
      cases hs : checkIndexedRupStep database step with
      | false =>
          simp [checkIndexedRup, hs] at h
      | true =>
          have htail :
              checkIndexedRup (database ++ [step.clause]) rest = true := by
            simpa [checkIndexedRup, hs] using h
          have hstep :=
            checkIndexedRupStep_implies_reference database step hs
          have href := ih (database ++ [step.clause]) htail
          simpa [checkRup, hstep] using href

/-- Universally sound for all signed CNFs, with no affine or separator
    assumptions and no trusted external proof-producer verdict. -/
theorem signedIndexedRup_unsat
    (raw : List (List Int)) (trace : List IndexedRupStep)
    (h : checkIndexedRup
      (Witnora.SignedSerialization.decodeCNF raw) trace = true) :
    ¬ ∃ a, Witnora.SignedSerialization.signedCNFHolds raw a :=
  signedRup_unsat raw (trace.map eraseReasonIndices)
    (checkIndexedRup_implies_reference _ trace h)

example :
    checkIndexedRup [[(1, true)], [(1, false)]]
      [{clause := [], units := [{forced := (1, true), rowID := 0}],
        conflictID := 1}] = true := by decide

example :
    checkIndexedRup [[(1, true)], [(1, false)]]
      [{clause := [], units := [{forced := (1, true), rowID := 5}],
        conflictID := 1}] = false := by decide

example :
    checkIndexedRup [[(1, true)], [(1, false)]]
      [{clause := [], units := [{forced := (1, true), rowID := 0}],
        conflictID := 5}] = false := by decide

#print axioms Witnora.GeneralRUPIndexed.signedIndexedRup_unsat

end Witnora.GeneralRUPIndexed
