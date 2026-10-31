# Multi-component native G14/G5 checked UNSAT (v46)

Draft PR #47. CI: https://github.com/joeyst8/witnora-core/actions/runs/41241197070

## Experiment

The Python emitter calls Witnora's actual `make_separator_affine_instance("saf_unsat_cover_2")`, computes separator assignments via `_all_assignments`, partitions through `_component_dicts` and `_condition_by_separator`, and requires **two** residual components per branch. For each branch, it selects a component whose genuine `build_affine_residue_certificate` output is natively validated as UNSAT, requiring a nonempty indexed row-operation trace. The chosen components differ between the false and true selector branches.

The emitted Lean source checks raw canonical DIMACS ASCII bytes, signed tokens, both branch partitions, selected-component membership, actual native G5 initial rows/compiled DAG references, and the G14/G5 source-level UNSAT theorem.

Negative controls are also kernel checked:
- a partition containing only the selected component when a second residual component was required is rejected;
- a G5 DAG with an invalid `(999, 0)` reference is rejected.

CI passed. The final `GeneratedPythonG14.python_g14_g5_dimacs_unsat` theorem axiom audit is `[propext, Classical.choice, Quot.sound]`, with no `sorry`/native evaluation. Measured Lean verification: **0.57 seconds**, peak **346,048 KiB** in one GitHub runner job.

## Limits

This is a specific structured UNSAT-cover instance with two branches and two components. It validates exact emitted artifacts in Lean; it does not formally refine the Python interpreter or prove arbitrary production G14 outputs are accepted. In particular it does not use original TC-063 source bytes, partitions or certificates, and does not establish any P-versus-NP theorem.

The next evidence milestone is multi-size structured cases and actual TC-063 artifact/source identity. Only after genuine target artifacts pass the full checker should we claim a TC-063-specific formal theorem.
