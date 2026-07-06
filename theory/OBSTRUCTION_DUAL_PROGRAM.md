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

## v2.15 Promotion Example

The first promoted obstruction-dual recommendation is:

`GRAPH_SEPARATOR_OBSTRUCTION -> GRAPH_SEPARATOR_LIFT`

v2.15 implements this as `G8_GRAPH_SEPARATOR_LIFT_PROTOTYPE`, not as another G7
mode. G7 remains the obstruction-dual recorder; G8 is a native separator-lift
prototype with its own checker.

The promotion is still bounded. It verifies separator decomposition, SAT
witness lifting, and UNSAT separator cover for selected finite rows. It does
not claim a family theorem, graph-separator completeness, lower bounds, or
P vs NP progress.

## v2.16 Promotion Example

The second promoted obstruction-dual recommendation is:

`COMPOSED_OBSTRUCTION -> COMPOSED_OPERATOR_ORCHESTRATION`

v2.16 implements this as `G9_COMPOSED_OPERATOR_ORCHESTRATION_PROTOTYPE`. G9 is
a native certificate-chain checker. It verifies step certificates, formula
hash handoffs, preservation declarations, and witness/proof lift traces across
multiple operator applications.

This promotion does not make orchestration universal. A chain fails if a
handoff hash is broken, a step certificate is missing, a diagnostic-only step
is used as a proof, a SAT witness fails the original CNF, or an UNSAT step lacks
preservation.

## v2.17 Promotion Example

The next promoted obstruction-dual recommendation is:

`CIRCUIT_PROJECTION_SIGNAL -> CIRCUIT_PROJECTION_LIFT`

v2.17 implements this as `G10_CIRCUIT_PROJECTION_LIFT_PROTOTYPE`. G10 verifies
exact definitional gate clauses, projects only safe auxiliary variables,
recomputes the projected core, and checks SAT or UNSAT lift evidence.

This promotion does not authorize arbitrary projection. If a projected variable
has an incomplete definition, polluted definition, unsafe outside use, bad SAT
lift, or missing UNSAT equisatisfiability evidence, the certificate fails.
