# Collapse Obstruction Program

The obstruction program turns bounded non-collapse rows into research objects.
The goal is to learn which structural feature blocks the current grammar and
which certificate-backed operator could remove that obstacle.

## Obstruction Records

Each record contains:

- instance and family
- grammar and bound profile
- obstruction type
- evidence
- suggested next operator
- confidence
- certifiable next step

## Current Obstruction Types

- `TREEWIDTH_OVER_CAP`
- `XOR_ARITY_OVER_CAP`
- `NO_EXACT_XOR_PATTERN`
- `SYMMETRY_DETECTED_NO_CERTIFIED_QUOTIENT`
- `CARDINALITY_STRUCTURE_UNSUPPORTED`
- `HORN_STRUCTURE_UNSUPPORTED`
- `PROOF_EXPORT_BLOWUP`
- `SEARCH_BOUND_EXCEEDED`
- `OPERATOR_STUB`

## Operator Discovery

The discovery engine ranks candidate operators by obstruction evidence. Current
candidates include:

- `SYMMETRY_ORBIT`
- `HIGHER_ARITY_XOR`
- `CARDINALITY_PB`
- `HORN_RENAMABLE`
- `BACKDOOR_TO_TRACTABLE`
- `GRAPH_DECOMPOSITION`

The ranking is heuristic. It does not prove a theorem and does not certify that
the operator will collapse a family.

## v2.2 Symmetry Obstruction Split

v2.2 separates three cases that were previously bundled together:

- exact automorphism evidence: generators validate against the original CNF;
- native symmetry certification: a witness or preservation obligation is
  independently checked;
- diagnostic-only orbit signal: useful evidence, but not a collapse claim.

For pigeonhole, v2.2 records exact row/hole orbit evidence and cardinality/PB
signals, but keeps the result diagnostic-only until a preservation or proof
route exists.

v2.3 adds that route for recognized standard pigeonhole CNFs: exact
assignment-grid ALO/AMO detection plus a native counting contradiction. This
removes the `CARDINALITY_STRUCTURE_UNSUPPORTED` obstruction for those standard
rows, while leaving nonstandard encodings and DRAT export as future work.

## Relationship to Verifier-to-Witness Research

The long-term program is to discover operators that turn verifier obstructions
into deterministic, replayable witness or proof routes. Witnora does not claim
P vs NP progress. It records bounded evidence and proof obligations so future
claims can be audited.
