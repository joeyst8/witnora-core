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

## v2.4 Operator Genesis

v2.4 upgrades obstruction triage into candidate-schema generation. For each
selected family, the genesis engine records deterministic fingerprints,
candidate operator schemas, certificate obligations, promotion records, and
theorem-candidate queue entries.

The generated candidates are not implemented. The promotion queue only says
which schemas are eligible for prototype planning, and only when safety risks,
test families, and certificate sketches are explicit.

## v2.5 Hall/Capacity Promotion

v2.5 promotes the `ORBIT_COUNTING_COLLAPSE` schema into an implemented
prototype with a native checker. The obstruction it neutralizes is a local
capacity deficit: a demand subset can only use a resource neighborhood whose
total capacity is too small.

The checker rejects missing ALO clauses, missing capacity clauses, balanced
controls, and orbit-compressed certificates that are not expanded. This keeps
the operator from becoming a broad matching/allocation solver claim.

## v2.6 High-Arity Affine Promotion

v2.6 promotes the `MODULAR_RESIDUE_COLLAPSE` schema into
`G5_HIGH_ARITY_AFFINE_RESIDUE_PROTOTYPE`. The obstruction it neutralizes is a
bounded high-arity affine residue signal: an exact GF(2) equation is present as
a full forbidden-assignment CNF encoding, but the arity is beyond G1's lower
extraction cap.

The checker rejects incomplete encodings, wrong parity bits, over-cap rows, and
nontrivial row-scaling claims. This keeps the operator from becoming a broad
modular arithmetic solver, a CryptoMiniSat-style mining claim, or a fake DRAT
route.

## v2.7 Proof-Motif Promotion

v2.7 promotes the `PROOF_MOTIF_COMPRESSION` schema into
`G6_PROOF_MOTIF_COMPRESSION_PROTOTYPE`. The obstruction it addresses is repeated
proof structure: many local proof obligations share an isomorphic template, but
expanding each proof independently can exceed configured proof-size bounds.

The checker verifies the template and every reuse instantiation. This keeps the
operator from becoming a fake proof-compression claim or a fake DRAT route.

## Relationship to Verifier-to-Witness Research

The long-term program is to discover operators that turn verifier obstructions
into deterministic, replayable witness or proof routes. Witnora does not claim
P vs NP progress. It records bounded evidence and proof obligations so future
claims can be audited.
