import Witnora.ClauseViolationParity

/-!
# Universal clause-violation product semantics

For a Boolean assignment a, a signed clause is false precisely when
EVERY literal is false. In the Boolean ring F_2[x]/(x_i^2=x_i),
literal false-indicators multiply to the clause violation polynomial.

This proves the semantic product identity for every signed clause.
The concrete Python ANF monomial expansion / canonical serialization
is independently tested but is not refined into Lean by this theorem.
-/

namespace Witnora.ViolationProduct

open Witnora.SignedSerialization
open Witnora.ClauseViolationParity
open Witnora.G5Extraction

def falseProduct : List Int → (Nat → Bool) → Bool
  | [], _ => true
  | lit :: rest, a =>
      (!signedLitTrue a (decode lit)) && falseProduct rest a

theorem falseProduct_eq_not_any (clause : List Int)
    (a : Nat → Bool) :
    falseProduct clause a =
      !(clause.any (fun lit => signedLitTrue a (decode lit))) := by
  induction clause with
  | nil => rfl
  | cons lit rest ih =>
      simp only [falseProduct, List.any_cons]
      rw [← ih]
      cases h : signedLitTrue a (decode lit) <;> simp [h]

def productViolations (cnf : List (List Int))
    (a : Nat → Bool) : List Bool :=
  cnf.map (fun clause => falseProduct clause a)

theorem productViolations_eq_violationVector
    (cnf : List (List Int)) (a : Nat → Bool) :
    productViolations cnf a = violationVector cnf a := by
  simp [productViolations, violationVector, falseProduct_eq_not_any]

example : falseProduct [1, -1] (fun _ => true) = false := by decide
example : falseProduct [] (fun _ => false) = true := by decide

#print axioms Witnora.ViolationProduct.falseProduct_eq_not_any
#print axioms Witnora.ViolationProduct.productViolations_eq_violationVector

end Witnora.ViolationProduct
