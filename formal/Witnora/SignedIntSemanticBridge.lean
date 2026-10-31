import Witnora.CheckedXorOutput
import Witnora.SignedSerialization

/-!
# Signed integer semantic refinement

The serialized Int clauses use signed literal values and a deterministic
in-clause integer sort. This module proves that sorting and decoding these
integers preserve the Boolean meaning of each symbolic clause, provided
every variable ID is positive. Zero is not a valid DIMACS literal.
-/

namespace Witnora.SignedIntSemanticBridge

open Witnora.Concrete
open Witnora.Extraction
open Witnora.FiniteXor
open Witnora.ExactSignedXorCNF
open Witnora.SignedSerialization

theorem decode_signedLiteralToInt
    (lit : Literal) (hpos : 0 < lit.1) :
    decode (signedLiteralToInt lit) = lit := by
  obtain ⟨v, polarity⟩ := lit
  cases v with
  | zero => simp at hpos
  | succ n =>
      cases polarity <;>
        simp [signedLiteralToInt, decode]

theorem insertSignedInt_perm (x : Int) (xs : List Int) :
    (insertSignedInt x xs).Perm (x :: xs) := by
  induction xs with
  | nil => rfl
  | cons y ys ih =>
      by_cases h : decide (x ≤ y) = true
      · simp [insertSignedInt, h]
      · have hf : decide (x ≤ y) = false := by
          cases hh : decide (x ≤ y) <;> simp_all
        simp only [insertSignedInt, hf, ite_false]
        exact (List.Perm.cons y ih).trans
          (List.Perm.swap x y ys).symm

theorem sortSignedClause_perm (xs : List Int) :
    (sortSignedClause xs).Perm xs := by
  induction xs with
  | nil => rfl
  | cons x xs ih =>
      exact (insertSignedInt_perm x (sortSignedClause xs)).trans
        (List.Perm.cons x ih)

theorem any_perm {α : Type} (xs ys : List α)
    (p : α → Bool) (hperm : xs.Perm ys) :
    xs.any p = ys.any p := by
  apply Bool.eq_iff_iff.mpr
  constructor
  · intro h
    obtain ⟨x, hx, hp⟩ := List.any_eq_true.mp h
    exact List.any_eq_true.mpr
      ⟨x, hperm.mem_iff.mp hx, hp⟩
  · intro h
    obtain ⟨x, hx, hp⟩ := List.any_eq_true.mp h
    exact List.any_eq_true.mpr
      ⟨x, hperm.mem_iff.mpr hx, hp⟩

theorem signedClause_semantics (clause : List Literal)
    (a : Nat → Bool)
    (hpositive : ∀ lit, lit ∈ clause → 0 < lit.1) :
    (sortSignedClause (clause.map signedLiteralToInt)).any
      (fun z => signedLitTrue a (decode z)) =
        clause.any (signedLitTrue a) := by
  rw [any_perm _ _ _ (sortSignedClause_perm _)]
  induction clause with
  | nil => rfl
  | cons lit rest ih =>
      have hp : 0 < lit.1 := hpositive lit (by simp)
      have hr : ∀ x, x ∈ rest → 0 < x.1 := by
        intro x hx
        exact hpositive x (by simp [hx])
      simp only [List.map_cons, List.any_cons, List.any_map]
      rw [decode_signedLiteralToInt lit hp, ih hr]

theorem signForbiddenClause_positive
    (vars : List Nat) (bad : List Bool)
    (hpositive : ∀ v, v ∈ vars → 0 < v) :
    ∀ lit, lit ∈ signForbiddenClause (List.zip vars bad) → 0 < lit.1 := by
  induction vars generalizing bad with
  | nil =>
      intro lit hlit
      simp [signForbiddenClause] at hlit
  | cons v vs ih =>
      cases bad with
      | nil =>
          intro lit hlit
          simp [signForbiddenClause] at hlit
      | cons b bs =>
          intro lit hlit
          have hv : 0 < v := hpositive v (by simp)
          have hrest : ∀ x, x ∈ vs → 0 < x := by
            intro x hx
            exact hpositive x (by simp [hx])
          simp only [List.zip_cons_cons, signForbiddenClause, List.map_cons,
            List.mem_cons] at hlit
          rcases hlit with heq | htail
          · rw [← heq]
            exact hv
          · exact ih bs hrest lit htail

/-- Every normalized positive-ID clause is semantically unchanged by
    signed-Int conversion, in-clause sorting, and Int decoding. -/
theorem serializedSignedClauses_semantics
    (vars : List Nat) (rhs : Bool) (a : Nat → Bool)
    (hpositive : ∀ v, v ∈ vars → 0 < v) :
    signedCNFHolds (serializedSignedClauses vars rhs) a ↔
      generatedSignedHolds vars rhs a = true := by
  unfold signedCNFHolds serializedSignedClauses generatedSignedHolds
  simp only [List.all_map]
  apply Iff.intro
  · intro h
    apply List.all_eq_true.mpr
    intro bad hbad
    have hclause := List.all_eq_true.mp h bad hbad
    have hs := signedClause_semantics
      (signForbiddenClause (List.zip vars bad)) a
      (signForbiddenClause_positive vars bad hpositive)
    simpa only [Function.comp_apply, hs] using hclause
  · intro h
    apply List.all_eq_true.mpr
    intro bad hbad
    have hclause := List.all_eq_true.mp h bad hbad
    have hs := signedClause_semantics
      (signForbiddenClause (List.zip vars bad)) a
      (signForbiddenClause_positive vars bad hpositive)
    simpa only [Function.comp_apply, hs] using hclause

#print axioms Witnora.SignedIntSemanticBridge.serializedSignedClauses_semantics

end Witnora.SignedIntSemanticBridge
