# Proof Motif Compression

v2.7 introduces `G6_PROOF_MOTIF_COMPRESSION_PROTOTYPE`, the scoped prototype of
the v2.4-generated `PROOF_MOTIF_COMPRESSION` candidate.

## Scope

G6 studies proof reuse. It looks for repeated local proof motifs, verifies one
native template proof, verifies each instantiation map against original CNF
clauses, and records a compressed macro-proof certificate.

G6 does not claim:

- DRAT verification;
- proof-compression completeness;
- all structured formulas are handled;
- Tseitin formulas are newly solved by G6;
- a G6 strictness theorem;
- P vs NP progress.

## Native Macro-Proof Certificate

The certificate records:

- motif templates;
- native resolution or unit-propagation steps;
- reuse sites;
- substitution maps;
- source clause IDs;
- instantiated proof hashes;
- derived instantiated lemmas;
- compressed and expanded proof-step counts.

Every reuse site must verify independently. A repeated pattern is not proof
unless the checker expands and verifies the instantiated proof against original
clauses.

## Optional Tseitin Handling

Tseitin/XOR-like rows are not counted as novel G6 deltas when previous XOR
grammars may already collapse them. They are duplicate controls unless the
configured G0-G5 profile demonstrably fails and G6 supplies a distinct native
proof-motif certificate.

## Public Category

G6 may emit:

- `UNSAT_PROOF_MOTIF_NATIVE_CERTIFIED`;
- diagnostic/no-collapse rows for duplicate or unverified controls.

These are native categories, not DRAT categories.
