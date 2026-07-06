# Operator Genesis Engine

Witnora-Core v2.4 starts the transition from hand-named operators to generated
operator schemas.

The engine studies failed or non-collapsed rows, extracts obstruction
fingerprints, proposes candidate collapse operators, records certificate
obligations, and builds a theorem-candidate queue.

It does not implement the generated operators.

## What It Generates

- obstruction fingerprints
- generated operator candidates
- certificate obligation sketches
- promotion records
- theorem-candidate queue entries
- novelty, evidence, and risk scores

## What It Does Not Claim

- no generated candidate is implemented
- no generated candidate solved a formula
- no generated theorem candidate is a theorem
- no P vs NP progress claim
- no lower bound against previous grammars
- no fake DRAT or native certificate claim

## Promotion Discipline

A candidate can become promotion-eligible only when it has:

- a trigger signature
- an intended transformation
- a certificate obligation sketch
- at least one predicted test family
- explicit safety risks
- forbidden interpretations

Promotion eligibility means prototype planning only. A candidate is not trusted
until it is implemented, checked, tested, red-teamed, and frozen.

## Scoring

Novelty is tracked separately from evidence.

Evidence comes from reproducible fingerprints. Risk comes from missing checker
paths, preservation obligations, and proof-export requirements.

The ranking is a research-planning heuristic, not a theorem and not a solver
result.

## v2.5 Promotion: Orbit Capacity Counting

v2.5 promotes the generated `ORBIT_COUNTING_COLLAPSE` candidate into the
prototype grammar `G4_ORBIT_CAPACITY_COUNTING_PROTOTYPE`.

The promoted prototype is deliberately narrower than a general matching or
allocation solver. It detects exact assignment/resource formulas with variables
`x[item,resource]`, verifies demand clauses and capacity clauses against the
original CNF, and emits a native certificate only when a concrete subset `S`
has `|S| > capacity(N(S))`.

Standard complete matching examples that reduce to the G3 pigeonhole pattern
are recorded as duplicate controls. They are not counted as a new G4 delta.

Generated-operator promotion still follows the same rule: a prototype is not a
theorem, not DRAT, and not trusted beyond the certificates its checker expands
and verifies.

## v2.6 Promotion: High-Arity Affine Residue

v2.6 promotes `MODULAR_RESIDUE_COLLAPSE` into
`G5_HIGH_ARITY_AFFINE_RESIDUE_PROTOTYPE`.

The promoted prototype is not a broad modular arithmetic solver. It accepts
only exact full CNF encodings of GF(2) affine equations up to a configured arity
cap and emits native Gaussian-elimination certificates. It does not perform
heuristic XOR mining and does not claim CryptoMiniSat-style extraction.

As with G4, generated-operator promotion remains evidence-bounded: native
certificates are trusted only after the checker verifies source clauses,
deterministic row operations, SAT witnesses, or UNSAT contradiction rows.

## v2.7 Promotion: Proof Motif Compression

v2.7 promotes `PROOF_MOTIF_COMPRESSION` into
`G6_PROOF_MOTIF_COMPRESSION_PROTOTYPE`.

This promoted prototype is proof-structural rather than semantic. It detects
repeated native proof motifs, verifies one motif template, verifies every reuse
instantiation against original clauses, and emits a compressed native
macro-proof certificate.

The promotion remains bounded: G6 is not DRAT, not a proof-compression
complete system, and not a theorem. Optional Tseitin/XOR-like rows are
duplicate controls unless prior XOR grammars demonstrably fail under the
configured profile and G6 supplies distinct verified proof-motif evidence.
