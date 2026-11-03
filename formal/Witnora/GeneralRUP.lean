import Witnora.GeneralResolutionAscii

/-!
# Witness-carrying reverse unit propagation (RUP) over arbitrary CNFs

A RUP clause C is entailed by a current clause database F if assuming the
negation of every literal of C allows unit propagation to derive a conflict.
This reference checker accepts explicit unit-propagation witnesses so each
local transition can be audited without trusting any external SAT solver.

It is a strict RUP subset (additions only; no deletion/RAT/DRAT yet).
An accepted empty-clause addition proves UNSAT for arbitrary source CNFs,
including non-affine formulas with no useful separators.
-/

namespace Witnora.GeneralRUP

open Witnora.Concrete
open Witnora.FiniteXor
open Witnora.G5Extraction

def flip (lit : Literal) : Literal := (lit.1, !lit.2)

/-- Any literal is the negation of its flipped counterpart. -/
theorem flip_true_of_false (a : Nat → Bool) (lit : Literal)
    (h : signedLitTrue a lit = false) :
    signedLitTrue a (flip lit) = true := by
  rcases lit with ⟨v, polarity⟩
  cases polarity <;> cases hb : a v <;>
    simp_all [flip, signedLitTrue]

theorem false_of_flip_true (a : Nat → Bool) (lit : Literal)
    (h : signedLitTrue a (flip lit) = true) :
    signedLitTrue a lit = false := by
  rcases lit with ⟨v, polarity⟩
  cases polarity <;> cases hb : a v <;>
    simp_all [flip, signedLitTrue]

def assumptionsHold (assumptions : List Literal)
    (a : Nat → Bool) : Prop :=
  ∀ lit ∈ assumptions, signedLitTrue a lit = true

/-- A forced unit is justified by a source clause whose other literals are
    all false under the accumulated assumptions. -/
def checkUnit (database : CNF) (assumptions : List Literal)
    (forced : Literal) : Bool :=
  database.any (fun clause =>
    decide (forced ∈ clause) &&
    clause.all (fun lit =>
      decide (lit = forced) || decide (flip lit ∈ assumptions)))

/-- A contradiction is present if one database clause is falsified by
    all of the accumulated assumptions. -/
def checkConflict (database : CNF)
    (assumptions : List Literal) : Bool :=
  database.any (fun clause =>
    clause.all (fun lit => decide (flip lit ∈ assumptions)))

/-- Recheck an explicit deterministic sequence of unit propagations. -/
def checkPropagation (database : CNF) :
    List Literal → List Literal → Bool
  | assumptions, [] => checkConflict database assumptions
  | assumptions, forced :: tail =>
      checkUnit database assumptions forced &&
        checkPropagation database (forced :: assumptions) tail

theorem checkUnit_sound
    (database : CNF) (assumptions : List Literal)
    (forced : Literal) (a : Nat → Bool)
    (hstep : checkUnit database assumptions forced = true)
    (hmodel : CNFHolds database a)
    (hassumptions : assumptionsHold assumptions a) :
    signedLitTrue a forced = true := by
  obtain ⟨clause, hmem, hchecked⟩ := List.any_eq_true.mp hstep
  have hparts : decide (forced ∈ clause) = true ∧
      clause.all (fun lit =>
        decide (lit = forced) || decide (flip lit ∈ assumptions)) = true := by
    simpa [checkUnit, Bool.and_eq_true] using hchecked
  have hsatisfied : clause.any (signedLitTrue a) = true :=
    List.all_eq_true.mp hmodel clause hmem
  obtain ⟨lit, hlit, htrue⟩ := List.any_eq_true.mp hsatisfied
  have hp := List.all_eq_true.mp hparts.2 lit hlit
  have hcases : lit = forced ∨ flip lit ∈ assumptions := by
    simpa [Bool.or_eq_true] using hp
  rcases hcases with heq | hneg
  · simpa [heq] using htrue
  · have hfalse :=
      false_of_flip_true a lit (hassumptions (flip lit) hneg)
    rw [hfalse] at htrue
    cases htrue

theorem checkConflict_sound
    (database : CNF) (assumptions : List Literal)
    (a : Nat → Bool)
    (hconflict : checkConflict database assumptions = true)
    (hmodel : CNFHolds database a)
    (hassumptions : assumptionsHold assumptions a) :
    False := by
  obtain ⟨clause, hmem, hchecked⟩ := List.any_eq_true.mp hconflict
  have hsatisfied : clause.any (signedLitTrue a) = true :=
    List.all_eq_true.mp hmodel clause hmem
  obtain ⟨lit, hlit, htrue⟩ := List.any_eq_true.mp hsatisfied
  have hflip : flip lit ∈ assumptions := by
    have hp := List.all_eq_true.mp hchecked lit hlit
    simpa using hp
  have hfalse :=
    false_of_flip_true a lit (hassumptions (flip lit) hflip)
  rw [hfalse] at htrue
  cases htrue

theorem checkPropagation_sound
    (database : CNF) (assumptions units : List Literal)
    (a : Nat → Bool)
    (hcheck : checkPropagation database assumptions units = true)
    (hmodel : CNFHolds database a)
    (hassumptions : assumptionsHold assumptions a) :
    False := by
  induction units generalizing assumptions with
  | nil =>
      exact checkConflict_sound database assumptions a
        (by simpa [checkPropagation] using hcheck)
        hmodel hassumptions
  | cons forced tail ih =>
      have hparts :
          checkUnit database assumptions forced = true ∧
          checkPropagation database (forced :: assumptions) tail = true := by
        simpa [checkPropagation, Bool.and_eq_true] using hcheck
      have hforced :=
        checkUnit_sound database assumptions forced a
          hparts.1 hmodel hassumptions
      have hnew : assumptionsHold (forced :: assumptions) a := by
        intro lit hmem
        rcases List.mem_cons.mp hmem with rfl | htail
        · exact hforced
        · exact hassumptions lit htail
      exact ih (forced :: assumptions) hparts.2 hnew

structure RupStep where
  clause : List Literal
  units : List Literal
deriving Repr, DecidableEq

def checkRupStep (database : CNF) (step : RupStep) : Bool :=
  checkPropagation database (step.clause.map flip) step.units

theorem checkRupStep_sound
    (database : CNF) (step : RupStep) (a : Nat → Bool)
    (hcheck : checkRupStep database step = true)
    (hmodel : CNFHolds database a) :
    step.clause.any (signedLitTrue a) = true := by
  cases hb : step.clause.any (signedLitTrue a) with
  | true => rfl
  | false =>
      have hassumptions : assumptionsHold (step.clause.map flip) a := by
        intro lit hlit
        obtain ⟨original, horiginal, rfl⟩ := List.mem_map.mp hlit
        have hfalse : signedLitTrue a original = false :=
          List.any_eq_false.mp hb original horiginal
        exact flip_true_of_false a original hfalse
      exact False.elim
        (checkPropagation_sound database (step.clause.map flip)
          step.units a hcheck hmodel hassumptions)

/-- Additions only: the checker never accepts a bare solver verdict. -/
def checkRup : CNF → List RupStep → Bool
  | database, [] => decide (([] : List Literal) ∈ database)
  | database, step :: rest =>
      if checkRupStep database step then
        checkRup (database ++ [step.clause]) rest
      else false

theorem checkRup_sound
    (database : CNF) (trace : List RupStep)
    (hcheck : checkRup database trace = true) (a : Nat → Bool) :
    ¬ CNFHolds database a := by
  induction trace generalizing database with
  | nil =>
      intro hmodel
      have hempty : ([] : List Literal) ∈ database := by
        simpa [checkRup] using hcheck
      have hfalse : ([] : List Literal).any (signedLitTrue a) = true :=
        List.all_eq_true.mp hmodel [] hempty
      simp at hfalse
  | cons step rest ih =>
      cases hs : checkRupStep database step with
      | false =>
          simp [checkRup, hs] at hcheck
      | true =>
          have htail :
              checkRup (database ++ [step.clause]) rest = true := by
            simpa [checkRup, hs] using hcheck
          intro hmodel
          have hclause := checkRupStep_sound database step a hs hmodel
          have hdb :
              database.all (fun c => c.any (signedLitTrue a)) = true := hmodel
          have hnext : CNFHolds (database ++ [step.clause]) a := by
            change (database ++ [step.clause]).all
              (fun c => c.any (signedLitTrue a)) = true
            simp [List.all_append, hdb, hclause]
          exact ih (database ++ [step.clause]) htail hnext

theorem signedRup_unsat
    (raw : List (List Int)) (trace : List RupStep)
    (h : checkRup (Witnora.SignedSerialization.decodeCNF raw) trace = true) :
    ¬ ∃ a, Witnora.SignedSerialization.signedCNFHolds raw a := by
  rintro ⟨a, ha⟩
  exact checkRup_sound _ trace h a
    ((Witnora.SignedSerialization.signedCNFHolds_iff raw a).mp ha)

example :
    checkRup [[(1, true)], [(1, false)]]
      [{clause := [], units := []}] = true := by decide

example :
    checkRup [[(1, true)]]
      [{clause := [], units := []}] = false := by decide

#print axioms Witnora.GeneralRUP.signedRup_unsat

end Witnora.GeneralRUP
