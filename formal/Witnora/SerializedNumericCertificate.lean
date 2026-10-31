import Lean
import Witnora.NumericColorCertificate
import Witnora.NumericEdgeListBridge

/-!
# Canonical text adapter for numeric graph certificates

Wire format: N|K|u,v;u,v|c0,c1,...|q0,q1,...
Here N and K are the *largest* vertex/color indices (sizes are N+1 and K+1).
The empty edge field denotes no edges. All numerals must use canonical
base-ten spelling: no signs, spaces, or leading zeroes.
This checks Lean strings; a byte-level UTF-8 and Python refinement proof
remains outside this module.
-/

namespace Witnora.SerializedNumericCertificate

open Witnora.NumericColorCertificate
open Witnora.ConcreteColorCertificate
open Witnora.ChromaticMinimum

def parseCanonicalNat (s : String) : Option Nat := do
  let n ← s.toNat?
  if toString n == s then some n else none

def parseNatList (s : String) : Option (List Nat) :=
  if s.isEmpty then some []
  else (s.splitOn ",").mapM parseCanonicalNat

def parseEdge (s : String) : Option (Nat × Nat) := do
  match s.splitOn "," with
  | [u, v] =>
      let u ← parseCanonicalNat u
      let v ← parseCanonicalNat v
      return (u, v)
  | _ => none

def parseEdgeList (s : String) : Option (List (Nat × Nat)) :=
  if s.isEmpty then some []
  else (s.splitOn ";").mapM parseEdge

def parseCertificate (s : String) :
    Option (Nat × Nat × List (Nat × Nat) × List Nat × List Nat) := do
  match s.splitOn "|" with
  | [n, k, es, cs, qs] =>
      let n ← parseCanonicalNat n
      let k ← parseCanonicalNat k
      let edges ← parseEdgeList es
      let colors ← parseNatList cs
      let clique ← parseNatList qs
      return (n, k, edges, colors, clique)
  | _ => none

def checkSerialized (s : String) : Bool :=
  match parseCertificate s with
  | none => false
  | some (n, k, edges, colors, clique) =>
      checkNumeric n k edges colors clique

/-- A passing serialized certificate yields the exact chromatic-number
    theorem for the actual parsed, range-checked edge data. -/
theorem checked_serialized_sound
    (s : String) (N K : Nat) (edges : List (Nat × Nat))
    (colors clique : List Nat)
    (hParse : parseCertificate s = some (N, K, edges, colors, clique))
    (hCheck : checkSerialized s = true) :
    ∃ hNoLoops : ∀ u : Fin (N + 1),
        ¬ edgeAdj (decodedEdges N edges) u u,
      chromaticNumber (edgeAdj (decodedEdges N edges)) hNoLoops = K + 1 := by
  have hNumeric : checkNumeric N K edges colors clique = true := by
    simpa [checkSerialized, hParse] using hCheck
  exact checked_numeric_sound N K edges colors clique hNumeric

def triangleWire : String := "2|2|0,1;0,2;1,2|0,1,2|0,1,2"

theorem triangle_parses :
    parseCertificate triangleWire =
      some (2, 2, [(0, 1), (0, 2), (1, 2)], [0, 1, 2], [0, 1, 2]) := by
  decide

theorem triangle_serialized_passes :
    checkSerialized triangleWire = true := by
  decide

theorem triangle_serialized_optimal :
    ∃ hNoLoops : ∀ u : Fin 3,
        ¬ edgeAdj (decodedEdges 2 [(0, 1), (0, 2), (1, 2)]) u u,
      chromaticNumber (edgeAdj (decodedEdges 2 [(0, 1), (0, 2), (1, 2)]))
        hNoLoops = 3 := by
  exact checked_serialized_sound triangleWire 2 2
    [(0, 1), (0, 2), (1, 2)] [0, 1, 2] [0, 1, 2]
    triangle_parses triangle_serialized_passes

theorem rejects_leading_zero :
    checkSerialized "02|2|0,1;0,2;1,2|0,1,2|0,1,2" = false := by
  decide

theorem rejects_missing_field :
    checkSerialized "2|2|0,1;0,2;1,2|0,1,2" = false := by
  decide

theorem rejects_extra_edge_separator :
    checkSerialized "2|2|0,1;;0,2;1,2|0,1,2|0,1,2" = false := by
  decide

theorem rejects_negative_endpoint :
    checkSerialized "2|2|-1,1;0,2;1,2|0,1,2|0,1,2" = false := by
  decide

theorem rejects_out_of_range_endpoint :
    checkSerialized "2|2|0,3;0,2;1,2|0,1,2|0,1,2" = false := by
  decide

theorem rejects_wrong_color_length :
    checkSerialized "2|2|0,1;0,2;1,2|0,1|0,1,2" = false := by
  decide

end Witnora.SerializedNumericCertificate

#print axioms Witnora.SerializedNumericCertificate.checked_serialized_sound
#print axioms Witnora.SerializedNumericCertificate.triangle_serialized_optimal
