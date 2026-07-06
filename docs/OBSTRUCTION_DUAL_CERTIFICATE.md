# Obstruction Dual Certificate

v2.14 adds `G7_OBSTRUCTION_DUAL_CERTIFICATE_PROTOTYPE`, a diagnostic grammar
layer for turning bounded non-collapse into a checkable research object.

When G0-G6 do not emit a certified collapse under the configured diagnostic
profile, G7 records:

- the formula hash
- the G0-G6 attempt trace
- per-grammar non-certification evidence
- obstruction fingerprints
- source feature evidence
- missing-operator recommendations
- proof obligations
- an obstruction-to-operator queue

## What G7 Claims

G7 claims that the obstruction-dual certificate is internally checkable: the
formula hash matches, every G0-G6 attempt is recorded as bounded
non-certification, fingerprints have source feature evidence, and the
recommended operator has checker requirements before any promotion.

## What G7 Does Not Claim

G7 does not claim a satisfiability result, an unsatisfiability proof, hardness,
lower bounds, P vs NP progress, hierarchy completeness, or a complete
obstruction theory.

The G0-G6 attempt trace is not a lower-bound proof. It is bounded diagnostic
evidence used to guide the next operator.

## Outputs

The v2.14 runner emits:

- `obstruction_dual_certificates.json`
- `obstruction_dual_checker_summary.json`
- `missing_operator_recommendations.json`
- `obstruction_to_operator_queue.json`
- `g7_obstruction_dual_summary.json`
- `OBSTRUCTION_DUAL_CERTIFICATE_REPORT.md`

## Example

```bash
python -m witnora_core.obstruction_dual run --out-root outputs/v2.14-obstruction-dual-certificate --strict
python -m witnora_core.operator_genesis run-obstruction-dual-lab --out-root outputs/v2.14-obstruction-dual-certificate --strict
```

The resulting queue is a planning artifact. It is not an implemented operator,
not a theorem, and not a solver result.

## v2.15 Promotion

v2.15 promotes the `GRAPH_SEPARATOR_OBSTRUCTION` recommendation into
`G8_GRAPH_SEPARATOR_LIFT_PROTOTYPE`.

This promotion keeps G7 and G8 distinct:

- G7 records obstruction-dual evidence and queues missing operators.
- G8 implements one queued recommendation with a native graph-separator
  certificate.

The promotion does not retroactively turn G7 no-collapse traces into lower
bounds.

## v2.18 Promotion

v2.18 promotes the `PROOF_MOTIF_NEAR_MISS` recommendation into
`G11_PROOF_MOTIF_GENERALIZATION_CHECKER_PROTOTYPE`.

Near motif similarity remains obstruction evidence until the G11 checker
verifies a generalized template and every concrete instantiation. The
promotion does not turn G7 diagnostic traces into lower bounds and does not
claim proof-pattern learning completeness.

## v2.16 Promotion

v2.16 promotes the `COMPOSED_OBSTRUCTION` recommendation into
`G9_COMPOSED_OPERATOR_ORCHESTRATION_PROTOTYPE`.

This promotion keeps the obstruction-dual boundary intact:

- G7 records composed-obstruction evidence and queues orchestration as a missing
  operator class.
- G9 implements a bounded native certificate-chain checker for selected
  controlled rows.

G9 does not trust arbitrary operator sequences. Each step must carry a checked
input formula hash, output formula hash, step certificate, preservation type,
and witness/proof lift rule. A missing handoff or diagnostic-only step fails the
composed certificate.

## v2.17 Promotion

v2.17 promotes the `CIRCUIT_PROJECTION_SIGNAL` recommendation into
`G10_CIRCUIT_PROJECTION_LIFT_PROTOTYPE`.

G10 turns circuit-projection evidence into a native checker-backed operator
prototype. The promotion is deliberately narrow: only exact definitional gate
encodings are projected, SAT lifts must satisfy the original CNF directly, and
UNSAT preservation requires an equisatisfiability-preserving projection chain.

This promotion does not make arbitrary auxiliary projection sound, and it does
not claim a complete circuit-SAT method.
