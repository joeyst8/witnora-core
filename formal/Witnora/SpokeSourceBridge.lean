import Witnora.SpokeCollapse
import Witnora.G5Extraction
import Witnora.SignedSerialization
import Witnora.DIMACSDocument
import Witnora.DIMACSTokens

/-!
# CNF-source-backed parity-spoke contradiction

The detector must exhibit four complete binary XOR encodings inside an
arbitrary original CNF. G5Extraction.checkPattern soundness transfers each
encoding into a true GF(2) equation under every CNF model. The spoke
endpoint theorem then rejects conflicting syndromes. Additional clauses
in the source formula are harmless; no exact-family assumption is needed.

The strongest theorem also checks the original ASCII DIMACS document.
-/

namespace Witnora.SpokeSourceBridge

open Witnora.G5Extraction
open Witnora.Extraction
open Witnora.SpokeCollapse
open Witnora.SignedSerialization

theorem pair_parity_eq (u v : Nat) (a : Nat → Bool) :
    parityVars [u, v] a = (a u != a v) := by
  cases hu : a u <;> cases hv : a v <;>
    simp [parityVars, hu, hv]

def checkSpokeConflict (cnf : Witnora.Concrete.CNF)
    (x z : Nat) (s t : Spoke) : Bool :=
  checkPattern cnf [x, s.middle] s.left &&
  checkPattern cnf [s.middle, z] s.right &&
  checkPattern cnf [x, t.middle] t.left &&
  checkPattern cnf [t.middle, z] t.right &&
  (syndrome s != syndrome t)

/-- Four verified pattern extractions and contradictory endpoint
    syndromes entail UNSAT of an otherwise arbitrary original CNF. -/
theorem checkSpokeConflict_unsat
    (cnf : Witnora.Concrete.CNF) (x z : Nat) (s t : Spoke)
    (hc : checkSpokeConflict cnf x z s t = true) :
    ¬ ∃ a, CNFHolds cnf a := by
  simp only [checkSpokeConflict, Bool.and_eq_true] at hc
  rcases hc with ⟨⟨⟨⟨hsl, hsr⟩, htl⟩, htr⟩, hneq⟩
  rintro ⟨a, ha⟩
  have hsl' := checkPattern_sound cnf [x, s.middle] s.left hsl a ha
  have hsr' := checkPattern_sound cnf [s.middle, z] s.right hsr a ha
  have htl' := checkPattern_sound cnf [x, t.middle] t.left htl a ha
  have htr' := checkPattern_sound cnf [t.middle, z] t.right htr a ha
  rw [pair_parity_eq] at hsl' hsr' htl' htr'
  have hs := spoke_endpoint (a x) (a z) (a s.middle)
    s.left s.right hsl' hsr'
  have ht := spoke_endpoint (a x) (a z) (a t.middle)
    t.left t.right htl' htr'
  have heq : syndrome s = syndrome t := by
    unfold syndrome
    exact hs.symm.trans ht
  simp [heq] at hneq

/-- One kernel-checked route from exact ASCII source text to an UNSAT
    conclusion using automatically discovered parity-spoke evidence. -/
theorem checked_ascii_dimacs_spoke_unsat
    (source : List Nat) (tokens : List Int) (raw : List (List Int))
    (hdocument : Witnora.DIMACSDocument.checkDocument source tokens = true)
    (hstream : Witnora.DIMACSTokens.checkStream tokens raw = true)
    (x z : Nat) (s t : Spoke)
    (hspoke : checkSpokeConflict (decodeCNF raw) x z s t = true) :
    Witnora.DIMACSDocument.parseDocument source =
      some (Witnora.DIMACSTokens.serialize raw) ∧
    ¬ ∃ a, signedCNFHolds raw a := by
  constructor
  · have hd := Witnora.DIMACSDocument.checkDocument_sound source tokens hdocument
    have hs := (Witnora.DIMACSTokens.checkStream_sound tokens raw hstream).1
    simpa [hs] using hd
  · intro ⟨a, ha⟩
    have hcnf := (signedCNFHolds_iff raw a).mp ha
    exact checkSpokeConflict_unsat (decodeCNF raw) x z s t hspoke
      ⟨a, hcnf⟩

#print axioms Witnora.SpokeSourceBridge.checked_ascii_dimacs_spoke_unsat

end Witnora.SpokeSourceBridge
