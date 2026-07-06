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
