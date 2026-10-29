import Witnora.G5Extraction

/-!
# Signed integer DIMACS literals and Lean literal representation

Python uses nonzero signed integers, while the Lean CNF checker uses pairs
(variable ID, positive polarity). The two representations are equivalent
for every nonzero signed literal; zero is deliberately rejected as a literal.

No semantics of the CPython interpreter are assumed or claimed here.
-/

namespace Witnora.SignedSerialization

open Witnora.Concrete
open Witnora.FiniteXor
open Witnora.G5Extraction

def decode : Int → Literal
  | .ofNat 0 => (0, false)
  | .ofNat (n + 1) => (n + 1, true)
  | .negSucc n => (n + 1, false)

def encode (literal : Literal) : Int :=
  if literal.2 then Int.ofNat literal.1
  else match literal.1 with
    | 0 => 0
    | n + 1 => Int.negSucc n

def validSigned (z : Int) : Bool := decide (z ≠ 0)

theorem encode_decode (z : Int) (hz : z ≠ 0) :
    encode (decode z) = z := by
  cases z with
  | ofNat n =>
      cases n with
      | zero => contradiction
      | succ n => simp [decode, encode]
  | negSucc n => simp [decode, encode]

theorem decode_encode (v : Nat) (hv : v > 0) (positive : Bool) :
    decode (encode (v, positive)) = (v, positive) := by
  obtain ⟨n, rfl⟩ := Nat.exists_eq_succ_of_ne_zero (Nat.ne_of_gt hv)
  cases positive <;> simp [decode, encode]

def decodeCNF (cnf : List (List Int)) : CNF :=
  cnf.map (fun clause => clause.map decode)

def signedCNFHolds (cnf : List (List Int)) (a : Nat → Bool) : Prop :=
  cnf.all (fun clause => clause.any (fun lit => signedLitTrue a (decode lit))) = true

theorem signedCNFHolds_iff (cnf : List (List Int)) (a : Nat → Bool) :
    signedCNFHolds cnf a ↔ CNFHolds (decodeCNF cnf) a := by
  simp [signedCNFHolds, CNFHolds, decodeCNF, List.all_map, List.any_map]

example : decode (-3) = (3, false) := by decide
example : decode (3) = (3, true) := by decide
example : validSigned 0 = false := by decide
example : validSigned (-3) = true := by decide

#print axioms Witnora.SignedSerialization.encode_decode
#print axioms Witnora.SignedSerialization.decode_encode
#print axioms Witnora.SignedSerialization.signedCNFHolds_iff

end Witnora.SignedSerialization
