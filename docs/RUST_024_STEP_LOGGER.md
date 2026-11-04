# R-024 — Rust certificate StepLogger record construction

Status: **GREEN** in dedicated native Rust gate
[GitHub Actions #41756207305](https://github.com/joeyst8/witnora-core/actions/runs/41756207305).

The Python default `StepLogger()` remains unchanged. An explicit
`StepLogger(backend="rust")` now uses the Rust PyO3
`build_step_record_native` constructor for the nine canonical step-record
fields: step ID, type, input formula SHA-256, output formula SHA-256,
details, removed clauses, added clauses, assigned literals and
reconstruction data. Python's `CollapseStep` remains the boundary class.
The native code rejects invalid signed-CNF inputs and step ID zero.

## Differential verification

`tests/test_step_logger_rust.py` runs **1,200 seeded random comparisons**
against the original Python StepLogger, with independently generated
before/after CNF formulas, nested metadata, clause removals/additions,
assigned literals and reconstruction data. Exact `to_dict()` values,
field insertion order, and sequential IDs must match.
Empty/default payload and invalid input controls also run.

All previously migrated Rust counting, proof, hash and independent
Ganak comparisons remain enabled in the same green workflow.

## Limits and trust

This port constructs **step records**; it does not yet replace Python's
full certificate path, stable JSON serialization, certificate bundle
export, or independent verification. No Lean proof is modified, and the
native record constructor is not itself a mathematical proof.
The original Python implementation remains the default and the
independent reference. No Python files have been deleted.

Next migration target: reproducible certificate-level serialization and
hashing, independently verified against the original Python bundle
format, before enabling a Rust-default certificate pipeline.
