import Witnora.TC063SourceVertexCuts
import Witnora.DIMACSDocument
import Witnora.DIMACSTokens

/-!
# TC-063: source-ASCII-bound two-vertex-cut certificates

A valid claim is now checked against the *actual source document bytes*:
Lean parses the ASCII DIMACS input, proves equality with the exact
zero-delimited signed clause stream, decodes the signed clauses, derives
the primal graph from their clause co-occurrences, and independently
checks every two-vertex cut with G14's finite DFS oracle.

No Python-supplied graph, token stream, or clause segmentation is trusted:
each proposed artifact is checked against the source bytes in Lean.
This is a structural separator theorem, not an UNSAT proof or a universal
theorem about Python execution or the efficiency of discovery.
-/

namespace Witnora.TC063AsciiSourceVertexCuts

open Witnora.TC063SourceVertexCuts
open Witnora.TC063VertexCouplingFiniteOracle
open Witnora.G14DFSSeenEnqueue

/-- Source bytes, proposed tokens, proposed signed clauses and proposed
    separator pairs must agree with *independent* Lean verification. -/
def checkAsciiTwoCuts (source : List Nat) (tokens : List Int)
    (raw : List (List Int)) (claimed : List (Nat × Nat)) : Bool :=
  Witnora.DIMACSDocument.checkDocument source tokens &&
    Witnora.DIMACSTokens.checkStream tokens raw &&
    checkSignedTwoCuts raw claimed

theorem checked_ascii_parts
    (source : List Nat) (tokens : List Int)
    (raw : List (List Int)) (claimed : List (Nat × Nat))
    (hAccepted : checkAsciiTwoCuts source tokens raw claimed = true) :
    Witnora.DIMACSDocument.checkDocument source tokens = true ∧
    Witnora.DIMACSTokens.checkStream tokens raw = true ∧
    checkSignedTwoCuts raw claimed = true := by
  simpa [checkAsciiTwoCuts, Bool.and_eq_true, and_assoc] using hAccepted

/-- The claimed signed clause list reconstructs the original ASCII
    source stream exactly, including delimiters, header and ASCII lexemes. -/
theorem checked_ascii_source_matches_clauses
    (source : List Nat) (tokens : List Int)
    (raw : List (List Int)) (claimed : List (Nat × Nat))
    (hAccepted : checkAsciiTwoCuts source tokens raw claimed = true) :
    Witnora.DIMACSDocument.parseDocument source =
      some (Witnora.DIMACSTokens.serialize raw) := by
  obtain ⟨hDoc, hStream, _⟩ :=
    checked_ascii_parts source tokens raw claimed hAccepted
  have hd := Witnora.DIMACSDocument.checkDocument_sound source tokens hDoc
  have hs := (Witnora.DIMACSTokens.checkStream_sound tokens raw hStream).1
  rw [hs] at hd
  exact hd

/-- The exact original ASCII source is linked to a sound *and complete*
    two-cut graph certificate.  This conclusion is relative to source
    primal adjacency and the finite G14 DFS component-count semantics. -/
theorem checked_ascii_source_exact_cuts
    (source : List Nat) (tokens : List Int)
    (raw : List (List Int)) (claimed : List (Nat × Nat))
    (hAccepted : checkAsciiTwoCuts source tokens raw claimed = true) :
    Witnora.DIMACSDocument.parseDocument source =
      some (Witnora.DIMACSTokens.serialize raw) ∧
    claimed.Nodup ∧
    (∀ pair ∈ claimed,
      pair ∈ orderedPairs
        (canonicalSourceVertices (Witnora.SignedSerialization.decodeCNF raw))) ∧
    (∀ pair ∈ orderedPairs
        (canonicalSourceVertices (Witnora.SignedSerialization.decodeCNF raw)),
      residualComponentCount
        (canonicalSourceVertices (Witnora.SignedSerialization.decodeCNF raw))
        (clauseNeighbors (Witnora.SignedSerialization.decodeCNF raw))
        [pair.1, pair.2] > 1 ↔ pair ∈ claimed) := by
  have hSigned :=
    (checked_ascii_parts source tokens raw claimed hAccepted).2.2
  have hCuts := checked_signed_source_exact_cuts raw claimed hSigned
  exact ⟨checked_ascii_source_matches_clauses source tokens raw claimed
    hAccepted, hCuts.1, hCuts.2.1, hCuts.2.2⟩

#print axioms Witnora.TC063AsciiSourceVertexCuts.checked_ascii_source_matches_clauses
#print axioms Witnora.TC063AsciiSourceVertexCuts.checked_ascii_source_exact_cuts

end Witnora.TC063AsciiSourceVertexCuts
