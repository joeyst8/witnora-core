# Proof Motif Native Certificate

This note records the proof-sketch shape for
`G6_PROOF_MOTIF_COMPRESSION_PROTOTYPE`.

## Template Soundness

A motif template is a small native proof. v2.7 supports:

- resolution steps;
- unit-propagation steps;
- local contradiction templates.

The checker validates each template step before any reuse is trusted.

## Reuse Soundness

Each reuse site provides a substitution map from template variables to concrete
formula variables. The checker verifies:

- the substitution is valid;
- source clause IDs point to original CNF clauses;
- instantiated source clauses match the template under substitution;
- instantiated proof hashes match deterministic expansion;
- the derived instantiated lemma is correct.

## Macro Contradiction

The compressed proof may use original clauses and verified instantiated motif
lemmas. UNSAT is native-certified only when the macro proof reaches a verified
empty clause.

## Boundary

This is a native certificate, not DRAT. It does not claim proof-compression
completeness, a G6 strictness theorem, Tseitin novelty when prior XOR grammars
already apply, or P vs NP progress.
