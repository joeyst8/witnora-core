import Lean
import Witnora.NumericColorCertificate

/-!
# Kernel-reducible ASCII byte certificate checker

Input is a list of *raw byte values*, rather than Lean String.
Grammar: N|K|u,v;u,v|c0,c1,...|q0,q1,...
All numeric fields must be canonical ASCII decimal without leading zeros.
The parser is structurally recursive on byte lists so concrete tests may
use kernel reduction (`decide`), without `native_decide`.
-/ 

namespace Witnora.KernelAsciiNumericCertificate

open Witnora.NumericColorCertificate
open Witnora.ConcreteColorCertificate
open Witnora.ChromaticMinimum

def splitByte (delimiter : Nat) : List Nat → List (List Nat)
  | [] => [[]]
  | b :: bs =>
      let parts := splitByte delimiter bs
      if b == delimiter then [] :: parts
      else match parts with
        | [] => [[b]]
        | first :: rest => (b :: first) :: rest

def digitsValue : List Nat → Nat → Option Nat
  | [], acc => some acc
  | b :: bs, acc =>
      if 48 ≤ b ∧ b ≤ 57 then
        digitsValue bs (acc * 10 + (b - 48))
      else none

def parseNatBytes (bytes : List Nat) : Option Nat :=
  match bytes with
  | [] => none
  | [b] => digitsValue [b] 0
  | 48 :: _ => none
  | _ => digitsValue bytes 0

def parseNatBytesList (bytes : List Nat) : Option (List Nat) :=
  if bytes.isEmpty then some []
  else (splitByte 44 bytes).mapM parseNatBytes

def parseEdgeBytes (bytes : List Nat) : Option (Nat × Nat) := do
  match splitByte 44 bytes with
  | [u, v] =>
      let u ← parseNatBytes u
      let v ← parseNatBytes v
      return (u, v)
  | _ => none

def parseEdgeBytesList (bytes : List Nat) : Option (List (Nat × Nat)) :=
  if bytes.isEmpty then some []
  else (splitByte 59 bytes).mapM parseEdgeBytes

def parseAsciiCertificate (bytes : List Nat) :
    Option (Nat × Nat × List (Nat × Nat) × List Nat × List Nat) := do
  match splitByte 124 bytes with
  | [n, k, es, cs, qs] =>
      let n ← parseNatBytes n
      let k ← parseNatBytes k
      let edges ← parseEdgeBytesList es
      let colors ← parseNatBytesList cs
      let clique ← parseNatBytesList qs
      return (n, k, edges, colors, clique)
  | _ => none

def checkAsciiCertificate (bytes : List Nat) : Bool :=
  match parseAsciiCertificate bytes with
  | none => false
  | some (n, k, edges, colors, clique) =>
      checkNumeric n k edges colors clique

/-- Soundness relative to exactly the byte list that was parsed. -/
theorem checked_ascii_certificate_sound
    (bytes : List Nat) (N K : Nat) (edges : List (Nat × Nat))
    (colors clique : List Nat)
    (hParse : parseAsciiCertificate bytes = some (N, K, edges, colors, clique))
    (hCheck : checkAsciiCertificate bytes = true) :
    ∃ hNoLoops : ∀ u : Fin (N + 1),
        ¬ edgeAdj (decodedEdges N edges) u u,
      chromaticNumber (edgeAdj (decodedEdges N edges)) hNoLoops = K + 1 := by
  have hNumeric : checkNumeric N K edges colors clique = true := by
    simpa [checkAsciiCertificate, hParse] using hCheck
  exact checked_numeric_sound N K edges colors clique hNumeric

set_option maxRecDepth 4096
set_option maxHeartbeats 1600000

def triangleBytes : List Nat := [50, 124, 50, 124, 48, 44, 49, 59, 48, 44, 50, 59, 49, 44, 50, 124, 48, 44, 49, 44, 50, 124, 48, 44, 49, 44, 50]

theorem triangle_bytes_parse :
    parseAsciiCertificate triangleBytes =
      some (2, 2, [(0, 1), (0, 2), (1, 2)], [0, 1, 2], [0, 1, 2]) := by
  decide

theorem triangle_bytes_pass :
    checkAsciiCertificate triangleBytes = true := by
  decide

theorem triangle_bytes_optimal :
    ∃ hNoLoops : ∀ u : Fin 3,
        ¬ edgeAdj (decodedEdges 2 [(0, 1), (0, 2), (1, 2)]) u u,
      chromaticNumber (edgeAdj (decodedEdges 2 [(0, 1), (0, 2), (1, 2)]))
        hNoLoops = 3 := by
  exact checked_ascii_certificate_sound triangleBytes 2 2
    [(0, 1), (0, 2), (1, 2)] [0, 1, 2] [0, 1, 2]
    triangle_bytes_parse triangle_bytes_pass

theorem rejects_leading_zero :
    checkAsciiCertificate [48, 50, 124, 50, 124, 48, 44, 49, 59, 48, 44, 50, 59, 49, 44, 50, 124, 48, 44, 49, 44, 50, 124, 48, 44, 49, 44, 50] = false := by
  decide

theorem rejects_negative_endpoint :
    checkAsciiCertificate [50, 124, 50, 124, 45, 49, 44, 49, 59, 48, 44, 50, 59, 49, 44, 50, 124, 48, 44, 49, 44, 50, 124, 48, 44, 49, 44, 50] = false := by
  decide

theorem rejects_extra_separator :
    checkAsciiCertificate [50, 124, 50, 124, 48, 44, 49, 59, 59, 48, 44, 50, 59, 49, 44, 50, 124, 48, 44, 49, 44, 50, 124, 48, 44, 49, 44, 50] = false := by
  decide

theorem rejects_missing_field :
    checkAsciiCertificate [50, 124, 50, 124, 48, 44, 49, 59, 48, 44, 50, 59, 49, 44, 50, 124, 48, 44, 49, 44, 50] = false := by
  decide

theorem rejects_out_of_range :
    checkAsciiCertificate [50, 124, 50, 124, 48, 44, 51, 59, 48, 44, 50, 59, 49, 44, 50, 124, 48, 44, 49, 44, 50, 124, 48, 44, 49, 44, 50] = false := by
  decide

theorem rejects_bad_length :
    checkAsciiCertificate [50, 124, 50, 124, 48, 44, 49, 59, 48, 44, 50, 59, 49, 44, 50, 124, 48, 44, 49, 124, 48, 44, 49, 44, 50] = false := by
  decide

theorem rejects_nonascii_byte :
    checkAsciiCertificate [200, 124, 50, 124, 48, 44, 49, 59, 48, 44, 50, 59, 49, 44, 50, 124, 48, 44, 49, 44, 50, 124, 48, 44, 49, 44, 50] = false := by
  decide

end Witnora.KernelAsciiNumericCertificate

#print axioms Witnora.KernelAsciiNumericCertificate.checked_ascii_certificate_sound
#print axioms Witnora.KernelAsciiNumericCertificate.triangle_bytes_parse
#print axioms Witnora.KernelAsciiNumericCertificate.triangle_bytes_pass
#print axioms Witnora.KernelAsciiNumericCertificate.triangle_bytes_optimal
