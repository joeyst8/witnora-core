# Planner-Guided Execution

## v2.21 Soundness Sketch

v2.21 records G13 planner-guided execution as a soundness theorem candidate
with a formal proof sketch and proof obligations. The sketch requires a
verified G12 plan, a separate verified execution certificate, checked actual
operator certificates, formula handoffs, recomputed planned-vs-actual
comparison, and final SAT/UNSAT result obligations.

This is not a proven theorem. Matching finite executions do not prove all
plans succeed, hierarchy completeness, DRAT status, or P-vs-NP progress.

v2.20 introduces `G13_PLANNER_GUIDED_EXECUTION_PROTOTYPE`.

## Purpose

G13 checks finite executions guided by verified G12 plans. It does not make a
plan into a proof. It checks a separate execution certificate.

## Checker Obligations

The checker verifies:

- original formula hash;
- referenced G12 plan certificate;
- plan-only and execution-required status;
- actual operator step certificates;
- formula-hash handoffs between steps;
- planned-vs-actual comparison;
- SAT witness verification against the original CNF;
- UNSAT preservation or equisatisfiability obligations;
- rejection of fake execution, fake SAT/UNSAT, fake DRAT, unchecked steps,
  bad handoffs, diagnostic steps used as results, and HARD/UNKNOWN sentinels.

## Claim Boundary

`FINITE_PLANNER_EXECUTION_VERIFIED` says only that a finite plan/execution pair
was checked. It is not a theorem, not planner completeness, not DRAT, not a
strictness result, and not P-vs-NP progress.

## CLI

```bash
python -m witnora_core.planner_execution run --instances projected_affine_plan_execution circuit_plan_execution proof_motif_plan_execution graph_separator_plan_execution composed_plan_execution mismatch_control failed_execution_control --out-root outputs/v2.20-planner-guided-execution --strict
```
