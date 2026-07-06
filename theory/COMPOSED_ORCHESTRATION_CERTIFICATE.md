# Composed Orchestration Certificate

The v2.16 composed-orchestration certificate is a native certificate-chain
object for `G9_COMPOSED_OPERATOR_ORCHESTRATION_PROTOTYPE`.

## Certificate Shape

`ComposedOrchestrationCertificate` records:

- `type: COMPOSED_ORCHESTRATION_CERTIFICATE`
- original formula hash
- final formula hash
- ordered operator application records
- final result: `SAT`, `UNSAT`, or `DIAGNOSTIC_ONLY`
- final witness or native UNSAT certificate
- lift trace
- conservative chain claim boundary
- checker status
- public category

Each `OperatorApplicationRecord` records:

- step id
- operator name
- input formula hash
- output formula hash
- input and output formula summaries
- preservation type
- step certificate
- checker status
- optional witness lift rule
- optional UNSAT lift rule
- handoff verification

## Soundness Sketch

For SAT chains, if every step certificate verifies, every formula handoff hash
matches, every witness lift rule verifies, and the final lifted assignment
satisfies the original CNF directly, then the SAT result is sound for the
original formula.

For UNSAT chains, if every step certificate verifies, every formula handoff hash
matches, every step is UNSAT-preserving or has a native UNSAT lift rule, and the
final native UNSAT certificate verifies against the original CNF, then the
native UNSAT result is sound for the checked finite row.

## Non-Claims

This is not a DRAT proof unless an external proof against the original CNF is
actually exported and checked. v2.16 does not do that.

This is not a theorem, not a composition-completeness result, not a lower bound
against prior grammars, and not a P-vs-NP result.
