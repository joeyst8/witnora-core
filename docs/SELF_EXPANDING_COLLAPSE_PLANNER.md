# Self-Expanding Collapse Planner

## v2.21 Soundness Sketch

v2.21 records G12 plan-only verification as a soundness theorem candidate with
a formal proof sketch and proof obligations. A verified plan is structurally
valid, operator-compatible, claim-boundary safe, and execution-required; it is
not SAT/UNSAT evidence and not a proof.

This is not a proven theorem, not planner completeness, not DRAT, and not
P-vs-NP progress.

v2.19 introduces `G12_SELF_EXPANDING_COLLAPSE_PLANNER_PROTOTYPE`.

## v2.20 Planner-Guided Execution

v2.20 adds `G13_PLANNER_GUIDED_EXECUTION_PROTOTYPE` as a separate execution
layer over verified G12 plans. G12 still emits plan-only certificates. G13
checks whether a selected finite plan was actually executed by a separate
operator certificate chain.

A plan/execution match does not prove all plans succeed. It only records that
the specific planned chain, actual certificates, formula handoffs, and result
obligations verified for the checked finite instance.

## What It Does

G12 consumes:

- formula metadata;
- obstruction fingerprints;
- the known operator portfolio;
- prior bounded replay or diagnostic summaries where available.

It emits a `CollapsePlanCertificate` containing a proposed operator sequence,
missing-operator hypothesis, or review/theoremization plan.

## What It Does Not Do

A plan is not a collapse. A plan is not execution. A plan is not SAT/UNSAT
evidence. A plan is not DRAT. A plan is not a proof. A plan is not a theorem.

Execution requires later certified operator runs.

## Checker Obligations

The checker verifies:

- formula hash;
- recognized obstruction fingerprint;
- known operator portfolio membership;
- expected certificate type for every planned step;
- handoff requirements for every adjacent step;
- SAT witness and UNSAT preservation obligations where relevant;
- missing-operator soundness obligations and negative controls;
- execution-required status;
- absence of fake SAT/UNSAT, DRAT, theorem, completeness, and P vs NP claims.

## Evidence Grade

G12 uses `FINITE_PLANNER_CERTIFICATE_VERIFIED`. It does not use
`FINITE_EMPIRICAL_EDGE_DELTA_CERTIFIED`, because no operator chain has executed
yet.

## CLI

```bash
python -m witnora_core.collapse_planner run --instances composed_obstruction_plan circuit_projection_plan proof_motif_near_plan graph_separator_plan near_affine_missing_operator_plan no_confident_fingerprint_plan --out-root outputs/v2.19-self-expanding-collapse-planner --strict
```
