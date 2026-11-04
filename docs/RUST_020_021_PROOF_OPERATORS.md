# Witnora R-020/R-021: Native Proof-Aware Elimination and 2-SAT

Branch: `research/w-crc-001-asymmetric-v1`, unmerged PR #122.
Formal TC-063/Lean PR #121 remains unchanged.

## R-020: verified resolution/variable-elimination proof events

`rust/witnora-ve/src/ve_proof.rs` implements source-CNF
Davis–Putnam resolution and the exact recorded history of every
positive/negative source-clause pair, including:

- discarded tautological resolvents;
- generated non-tautological resolvents (with duplicates retained
  in the event log but deduplicated in the formula output);
- deterministic source clause order and removed/added proof clauses;
- exact width-cap refusals returning the original formula, without
  emitting a false certificate event;
- reconstruction metadata and full elimination-order replay.

The existing API opt-in is
`eliminate_variable(..., backend="rust")` or
`run_variable_elimination(..., backend="rust")`.

[Green R-020 CI #41752174357](https://github.com/joeyst8/witnora-core/actions/runs/41752174357)
passed **1,000 exact single-step proof-event comparisons**
and **300 full elimination-order replays**, matching the
original Python final formulas, decisions, details and every
`StepLogger` event. Rust unit tests also passed.

This is the proof-producing *resolution* operator, distinct from
the exact model-counting VE kernel ported in R-001/R-002.

## R-021: verified complete 2-SAT SCC certificate metadata

The original native R-010 SCC solver returned exact SAT/UNSAT and
witnesses but deliberately refused Python certificate logging.

The new `rust/witnora-ve/src/two_sat_proof.rs` reconstructs the
legacy sorted signed implication graph, Kosaraju component visit
order, exact edge list, conflict variable, and witness assignment.
It is exposed as
`solve_2sat(formula, logger, backend="rust_proof")`,
with the original Python `StepLogger` still handling hashes and
event serialization.

[Green R-021 CI #41752584529](https://github.com/joeyst8/witnora-core/actions/runs/41752584529)
passed **1,000 full randomized 2-CNF comparisons**, confirming exact
SAT/UNSAT outcomes, implication-edge order, Kosaraju SCC component
order, assignments, conflict data, and every existing Python
certificate-log record. The earlier Rust proof-free solver remains
available separately.

## Scope limits

The Rust algorithms are standard exact CNF resolution and SCC
analysis. Experimental parity is not a Lean soundness proof;
TC-063 retains its formal checker. Full migration must still
port the remaining formal certificate serialization, reconstruction,
the higher-level runner and planner, research scripts, tests,
and release/CI infrastructure. See the file-level original
Python inventory in
`research/python_to_rust_manifest.json`.
