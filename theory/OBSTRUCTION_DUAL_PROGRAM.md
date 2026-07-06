# Obstruction Dual Program

The obstruction-dual program asks whether failure under a bounded collapse
grammar can become useful evidence for the next operator.

The v2.14 prototype does not solve resistant formulas. It records a bounded
G0-G6 non-certification trace, extracts obstruction fingerprints, checks the
source evidence, and recommends a missing operator class.

## Certificate Shape

An obstruction-dual certificate contains:

- original formula hash
- grammars attempted from G0 through G6
- non-certification result for each grammar
- failed-route evidence hashes
- obstruction fingerprints
- feature evidence
- missing operator hypothesis
- proof obligations
- recommended next operator
- claim boundary

## Research Role

The certificate is a bridge from operator discovery to operator invention. It
answers:

- why the current grammar ladder did not certify a collapse;
- which structural fingerprint appears;
- which operator class might neutralize it;
- what checker obligations must exist before that operator can be trusted.

## Boundary

This is not a lower-bound certificate. It does not prove that no algorithm, or
even no future Witnora grammar, can collapse the instance. It is bounded,
empirical obstruction evidence used for next-operator selection.

It does not claim P vs NP progress, hierarchy completeness, satisfiability, or
unsatisfiability.
