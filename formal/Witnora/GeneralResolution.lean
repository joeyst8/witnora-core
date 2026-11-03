import Witnora.SignedSerialization

/-!
# Universal resolution certificate checking for arbitrary CNFs

Unlike the bounded-separator / certified-affine TC-063 family, this kernel
has no promise restriction on its source CNF. A certificate consists of
ordinary binary-resolution additions. It may be exponentially large.

Every accepted step names two *existing* clauses and a pivot. The checker
recomputes the exact resolvent; the claim is not trusted. Reaching the empty
clause proves UNSAT under every assignment, without exhaustive enumeration.
This first reference format carries clauses by value, not row indices; an
indexed DAG/wire-format refinement is a separate scaling obligation.
-/

namespace Witnora.GeneralResolution

open Witnora.Concrete
open Witnora.FiniteXor
open Witnora.G5Extraction

structure Step where
  left : List Literal
  right : List Literal
  pivot : Nat
  output : List Literal
deriving Repr, DecidableEq

/-- A resolvent preserves every non-pivot literal from each parent. -/
def resolvent (left right : List Literal) (pivot : Nat) : List Literal :=
  left.filter (· != (pivot, true)) ++
    right.filter (· != (pivot, false))

/-- Only already-derived clauses can be used, and the resolvent is
    recomputed exactly from the claimed parents. -/
def checkStep (database : CNF) (s : Step) : Bool :=
  decide (s.left ∈ database ∧
    s.right ∈ database ∧
    (s.pivot, true) ∈ s.left ∧
    (s.pivot, false) ∈ s.right ∧
    s.output = resolvent s.left s.right s.pivot)

/-- A finite proof is accepted only when its last database contains the
    empty clause. It never uses a SAT oracle or a Python-produced verdict. -/
def checkResolution : CNF → List Step → Bool
  | database, [] => decide (([] : List Literal) ∈ database)
  | database, s :: rest =>
      if checkStep database s then
        checkResolution (database ++ [s.output]) rest
      else false

/-- Binary resolution is sound for *every* assignment and clause size. -/
theorem resolvent_sound
    (left right : List Literal) (pivot : Nat)
    (a : Nat → Bool)
    (hl : left.any (signedLitTrue a) = true)
    (hr : right.any (signedLitTrue a) = true) :
    (resolvent left right pivot).any (signedLitTrue a) = true := by
  cases hb : a pivot with
  | false =>
      obtain ⟨lit, hmem, htrue⟩ := List.any_eq_true.mp hl
      have hneq : lit ≠ (pivot, true) := by
        intro heq
        subst lit
        simp [signedLitTrue, hb] at htrue
      apply List.any_eq_true.mpr
      refine ⟨lit, ?_, htrue⟩
      simp [resolvent, List.mem_filter, hmem, hneq]
  | true =>
      obtain ⟨lit, hmem, htrue⟩ := List.any_eq_true.mp hr
      have hneq : lit ≠ (pivot, false) := by
        intro heq
        subst lit
        simp [signedLitTrue, hb] at htrue
      apply List.any_eq_true.mpr
      refine ⟨lit, ?_, htrue⟩
      simp [resolvent, List.mem_filter, hmem, hneq]

/-- Adding a checked resolution step cannot eliminate a source model. -/
theorem checkStep_preserves_models
    (database : CNF) (s : Step) (a : Nat → Bool)
    (hstep : checkStep database s = true)
    (hmodel : CNFHolds database a) :
    CNFHolds (database ++ [s.output]) a := by
  have hvalid :
      s.left ∈ database ∧
      s.right ∈ database ∧
      (s.pivot, true) ∈ s.left ∧
      (s.pivot, false) ∈ s.right ∧
      s.output = resolvent s.left s.right s.pivot := by
    simpa [checkStep] using hstep
  have hl : s.left.any (signedLitTrue a) = true :=
    List.all_eq_true.mp hmodel s.left hvalid.1
  have hr : s.right.any (signedLitTrue a) = true :=
    List.all_eq_true.mp hmodel s.right hvalid.2.1
  have hout : s.output.any (signedLitTrue a) = true := by
    rw [hvalid.2.2.2.2]
    exact resolvent_sound s.left s.right s.pivot a hl hr
  have hdb : database.all (fun clause => clause.any (signedLitTrue a)) = true := hmodel
  change (database ++ [s.output]).all (fun clause => clause.any (signedLitTrue a)) = true
  simp [List.all_append, hdb, hout]

/-- Universal soundness: an accepted derivation of the empty clause
    refutes any finite CNF, even outside every TC-063 promise family. -/
theorem checkResolution_sound
    (database : CNF) (steps : List Step)
    (hcheck : checkResolution database steps = true)
    (a : Nat → Bool) :
    ¬ CNFHolds database a := by
  induction steps generalizing database with
  | nil =>
      intro hmodel
      have hempty : ([] : List Literal) ∈ database := by
        simpa [checkResolution] using hcheck
      have hfalse : ([] : List Literal).any (signedLitTrue a) = true :=
        List.all_eq_true.mp hmodel [] hempty
      simp at hfalse
  | cons s rest ih =>
      cases hs : checkStep database s with
      | false =>
          simp [checkResolution, hs] at hcheck
      | true =>
          have htail :
              checkResolution (database ++ [s.output]) rest = true := by
            simpa [checkResolution, hs] using hcheck
          intro hmodel
          exact ih (database ++ [s.output]) htail
            (checkStep_preserves_models database s a hs hmodel)

/-- The same theorem starts with arbitrary signed-integer CNF clauses.
    Source-text/DIMACS byte identity must be checked independently. -/
theorem signedResolution_unsat
    (raw : List (List Int)) (steps : List Step)
    (hcheck :
      checkResolution (Witnora.SignedSerialization.decodeCNF raw) steps = true) :
    ¬ ∃ a, Witnora.SignedSerialization.signedCNFHolds raw a := by
  rintro ⟨a, ha⟩
  exact checkResolution_sound _ steps hcheck a
    ((Witnora.SignedSerialization.signedCNFHolds_iff raw a).mp ha)

example :
    checkResolution [[(1,true)], [(1,false)]]
      [{ left := [(1,true)], right := [(1,false)], pivot := 1,
         output := [] }] = true := by decide

example :
    checkResolution [[(1,true)], [(1,true)]] [] = false := by decide

#print axioms Witnora.GeneralResolution.signedResolution_unsat

end Witnora.GeneralResolution
