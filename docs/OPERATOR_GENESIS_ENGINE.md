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
