# Witnora-Core v0.5.0

Witnora-Core v0.5.0 is a certified collapse-path prototype for CNF SAT formulas. It is not a general SAT solver and makes no `P = NP` claim. Its primary artifact is a deterministic, replay-verifiable collapse path: a sequence of satisfiability-preserving transformations, tractable solves, SAT witness reconstruction, and final verification against the original CNF.

No external SAT solver, GNN, MCTS, LRAT/FRAT emitter, or brute-force solver for arbitrary formulas is included.

## Implemented Theorem Scope

For a fixed `c` with v0 support for `0 <= c <= 4`, Witnora implements the accepted 2-SAT collapse theorem route:

- apply a fixed deterministic simplifier `S`
- split disconnected incidence-graph components
- solve each component if it is 2-CNF or has primal graph treewidth at most `c`
- reconstruct a full original assignment for SAT results
- replay-verify the logged certificate

`S` is deterministic by implementation order, not mathematically canonical.

## Collapse Routes

The deterministic simplifier applies, in order:

- Unit Propagation
- Pure Literal Elimination
- Subsumption
- Blocked Clause Elimination
- Component Decomposition

Component decomposition uses the incidence graph. Bounded-width reasoning uses the primal graph only.

## COMPONENTS_SOLVED

If a formula splits into more than one component and every component is solved, the full result uses:

```json
"final_class": "COMPONENTS_SOLVED"
```

The output includes:

```json
"component_results": [
  {
    "component_id": "0",
    "status": "SAT",
    "final_class": "2SAT",
    "formula_hash": "...",
    "assignment": {"1": true}
  }
]
```

Status priority is:

- if any component is `UNSAT`, the full formula is `UNSAT`
- else if any component is `NO_COLLAPSE_FOUND_UNDER_CURRENT_GRAMMAR_AND_C`, the full formula returns that no-collapse status
- else all components are `SAT`, so the full formula is `SAT`

The runner never returns partial SAT for a failed component set.

## NO_COLLAPSE_FOUND Is Not HARD

`NO_COLLAPSE_FOUND_UNDER_CURRENT_GRAMMAR_AND_C` means only that the implemented grammar and current `c` budget did not find a certified collapse route. It is not a hardness claim and must not be read as `HARD`, `UNKNOWN`, or probabilistic UNSAT.

## Why W_c Is Not Just Raw Bounded Treewidth

Witnora-Core includes an explicit strictness family:

```text
F_n =
(x or y_1 or y_2 or ... or y_n)
and
AND_{i=1..n} (not x or not y_i)
```

The long clause creates a clique of size `n + 1` in the original primal graph,
so the original primal treewidth is at least `n`. That long clause is blocked
on `x`: resolving it with each `(not x or not y_i)` produces a tautological
resolvent containing both `y_i` and `not y_i`.

After BCE removes the long clause, the remaining primal graph is a star
centered at `x`, which has treewidth 1. Therefore `W_1` includes formulas with
unbounded original primal treewidth that collapse to treewidth 1 after certified
BCE. This is a strictness statement about the implemented preprocessing
collapse class; it is not a P vs NP claim, a general SAT hardness claim, or a
claim of full novelty over all preprocessing literature.

## Benchmarking Collapse Behavior

Witnora-Core includes a benchmark and measurement layer. It does not change
the certified solver; it runs the solver across synthetic or user-provided CNF
cases and records whether deterministic simplification and component solving
collapse formulas into:

- `EMPTY`
- `2SAT`
- `TREEWIDTH_LEQ_C`
- `COMPONENTS_SOLVED`
- `UNSAT`
- `NO_COLLAPSE`

Run the synthetic suite:

```bash
python -m witnora_core.benchmark --suite synthetic --scale small --c 1 --out results_c1.json --determinism-check
python -m witnora_core.benchmark --suite synthetic --scale medium --c 2 --out results_c2.json --determinism-check
```

Run a directory of DIMACS files:

```bash
python -m witnora_core.benchmark --dimacs-dir path/to/dimacs --c 4 --out dimacs_results.json --determinism-check
```

Export per-case CSV alongside JSON:

```bash
python -m witnora_core.benchmark --suite synthetic --scale medium --c 2 --out results.json --csv results.csv --determinism-check
```

Export per-case certificates:

```bash
python -m witnora_core.benchmark --suite synthetic --scale small --c 2 --out results.json --export-certs certs/
```

Generate a Markdown benchmark report:

```bash
python -m witnora_core.report results.json --out REPORT.md
```

Compare two benchmark runs:

```bash
python -m witnora_core.compare synthetic_c1.json synthetic_c2.json --out COMPARE.md
```

Per-case metrics include original and post-`S` variable count, clause count,
maximum clause width, primal edge count, max-clause clique lower bound,
certificate hash, collapse path length, BCE removals, UP/PLE assignments,
subsumption removals, VE eliminations, route, status, verification flag, and
runtime.

The `original_clique_lower_bound` is only the lower bound `max_clause_width - 1`.
It is not an exact treewidth claim. The `post_s_width_order_status` field is one
of:

- `FOUND`
- `NOT_FOUND`
- `SKIPPED_SIZE_CAP`

When width measurement is skipped, `post_s_width_order_skip_reason` records
`num_vars_exceeds_max_width_search_vars`. The benchmark can skip exact
post-simplification width search for large formulas using
`--max-width-search-vars`.

`NO_COLLAPSE` in benchmark output is still not a hardness claim. It means only
that the current grammar and `c` budget did not produce a certified collapse.

The v0 exact treewidth route remains scoped to `0 <= c <= 4`.

## Proof-Carrying Certificates

Witnora-Core v0.3.0 added portable certificate bundles. v0.4.0 added the
independent raw checker. v0.5.0 cleans up SAT/UNSAT certification metadata and
adds a Witnora-native UNSAT trace for supported explicit-empty-clause and
2-SAT-SCC contradictions.

A certificate can be exported as either a `.wcert` directory or a single
`.wcert.json` file.

Export a certificate:

```bash
python -m witnora_core.runner examples/bce_demo.dimacs --c 2 --export-cert out.wcert
python -m witnora_core.runner examples/bce_demo.dimacs --c 2 --export-cert out.wcert.json
```

Verify a saved certificate with the Witnora replay verifier:

```bash
python -m witnora_core.verify_certificate out.wcert
python -m witnora_core.verify_certificate out.wcert.json
```

Verify a saved certificate with the smaller independent raw checker:

```bash
python -m witnora_core.independent_check out.wcert
python -m witnora_core.independent_check out.wcert.json
```

A `.wcert` directory contains:

- `manifest.json`
- `original.dimacs`
- `normalized.dimacs`
- `result.json`
- `collapse_path.json`
- `reconstruction_trace.json`
- `component_results.json`
- `stats.json`
- `proof_trace.json`, only for supported native UNSAT traces
- `certificate_hash.txt`
- `verifier_version.txt`

The Witnora replay verifier checks file hashes, the deterministic certificate
hash, formula hashes, collapse-path replay, component decomposition replay,
reconstruction trace consistency, SAT assignment verification, and UNSAT
contradictions.

The independent raw checker in `witnora_core.independent_check` avoids importing
solver/collapse modules. It reparses DIMACS, canonicalizes raw clauses, replays
UP, PLE, SUB, BCE, VE, component decomposition, and 2-SAT checks from scratch,
and verifies SAT assignments against the original CNF. Publication-facing
claims should rely on the independent raw checker where possible.

UNSAT is independently accepted only when replay reaches an explicit empty
clause or when a 2-SAT SCC contradiction is independently checked. Other UNSAT
forms remain internal-replay only until LRAT/FRAT proof export exists.

## Certification Metadata

SAT certificates include a `sat_certification_level`:

- `NOT_SAT`
- `RECONSTRUCTED_ASSIGNMENT_VERIFIED_ORIGINAL`
- `INDEPENDENT_RAW_CHECKER_VERIFIED`

UNSAT certificates include an `unsat_certification_level`:

- `NOT_UNSAT`
- `EXPLICIT_EMPTY_CLAUSE`
- `INDEPENDENT_2SAT_SCC`
- `INTERNAL_REPLAY_ONLY`
- `EXTERNAL_DRAT_LRAT_FRAT_VERIFIED`
- `LRAT_FRAT_NOT_IMPLEMENTED`

Current v0.5 certificates use the most precise supported level. SAT results use
`NOT_UNSAT`. UNSAT results use `NOT_SAT` for the SAT level. No-collapse results
must not claim a SAT or UNSAT proof.

The manifest also keeps:

```json
"external_lrat_frat": false
```

unless a future release actually emits and checks a standard external proof.

## proof_trace_class

Certificate bundles include a `proof_trace_class`:

- `SAT_ASSIGNMENT_RECONSTRUCTION`
- `UNSAT_EXPLICIT_EMPTY_CLAUSE`
- `UNSAT_2SAT_SCC_CONTRADICTION`
- `UNSAT_INTERNAL_REPLAY_ONLY`
- `NO_COLLAPSE_REPORT`

Each collapse step also receives an `external_proof_status`, such as
`CHECKED_BY_WITNORA_REPLAY`, `RAT_COMPATIBLE`,
`LRAT_EXPORT_NOT_IMPLEMENTED`, or `NOT_A_CLAUSAL_REFUTATION_STEP`.

This classification is deliberately conservative. v0.5.0 does not claim full
DRAT, LRAT, or FRAT support, and SAT certificates remain
assignment/reconstruction certificates rather than clausal refutations.

## Native UNSAT Trace

For supported UNSAT cases, v0.5.0 may include `proof_trace.json` with:

```json
{
  "proof_trace_format": "WITNORA_NATIVE_UNSAT_TRACE_V1",
  "external_standard": "NONE",
  "lrat_frat_status": "NOT_EXPORTED"
}
```

Supported native UNSAT trace reasons are:

- `EXPLICIT_EMPTY_CLAUSE`
- `INDEPENDENT_2SAT_SCC`

The independent raw checker verifies the native trace against its replayed final
state. For explicit empty-clause UNSAT it confirms the replayed final state
contains an empty clause. For 2-SAT SCC UNSAT it recomputes the implication graph
and SCC contradiction from raw clauses. This native trace is not DRAT, LRAT, or
FRAT.

See [PROOF_FORMAT_ROADMAP.md](PROOF_FORMAT_ROADMAP.md).

## certificate_hash

Every JSON result includes a deterministic `certificate_hash` computed from stable certificate fields:

- original formula hash
- `c`
- collapse path
- final class
- final assignment
- reconstructed original assignment
- original verification flag
- component results
- SAT and UNSAT certification levels
- proof trace class
- native UNSAT proof trace, when present

Runtime stats such as `stats.time_ms` are excluded.

## SAT Reconstruction

SAT reconstruction reverses the collapse path:

- UP and PLE assign their logged literals
- SUB needs no assignment action
- BCE sets the blocked literal to true if the removed clause is falsified
- VE uses the sign-correct reconstruction rule:
  - falsified `(x or ...)` requires `x = True`
  - falsified `(not x or ...)` requires `x = False`

Remaining original variables are filled deterministically as `False`. Every SAT result must verify against the original normalized CNF.

## Verifier

The verifier replays:

- formula hashes
- UP, PLE, SUB, BCE
- incidence-graph component splits
- component assignment merges
- exact primal-treewidth order verification
- VE resolvents and width caps
- 2-SAT SCC results
- final SAT assignment or UNSAT contradiction

## Adversarial Tests

`tests/test_adversarial_correctness.py` covers:

- non-blocked BCE rejection
- forced BCE reconstruction repair
- VE sign reconstruction
- VE reconstruction conflict detection
- fake cross-component split rejection
- empty formula SAT
- tautological clause normalization
- absent DIMACS variables
- `c=0` simplification behavior
- no-collapse without brute-force fallback
- verifier negative tests for corrupted hashes, BCE, VE, CD, and final assignment

## Run Tests

```bash
python -m unittest discover
```

Expected pass markers include:

- `BCE_RECONSTRUCTION_PASS`
- `TREEWIDTH_COLLAPSE_PASS`
- `RECONSTRUCTION_PASS`
- `UNSAT_PASS`
- `NO_COLLAPSE_PASS`
- `DETERMINISM_PASS`
- `COMPONENT_SOLVE_PASS`
- `COMPONENT_NO_COLLAPSE_PASS`
- `BLOCKED_CLIQUE_COLLAPSE_PASS`
- `STRICTNESS_TREEWIDTH_SIGNAL_PASS`
- `FAMILY_SCALING_PASS`
- `BENCHMARK_SYNTHETIC_PASS`
- `BENCHMARK_DETERMINISM_PASS`
- `BLOCKED_CLIQUE_METRICS_PASS`
- `RANDOM_3SAT_NO_COLLAPSE_SAFE_PASS`
- `DIMACS_DIR_BENCHMARK_PASS`
- `WIDTH_SKIP_REPORTING_PASS`
- `BENCHMARK_MEDIUM_SAFE_PASS`
- `BENCHMARK_CSV_EXPORT_PASS`
- `BENCHMARK_REPORT_GENERATION_PASS`
- `BENCHMARK_COMPARE_PASS`
- `CERT_EXPORT_SAT_PASS`
- `CERT_EXPORT_UNSAT_PASS`
- `CERT_EXPORT_COMPONENTS_PASS`
- `CERT_HASH_TAMPER_REJECT_PASS`
- `COLLAPSE_PATH_TAMPER_REJECT_PASS`
- `ASSIGNMENT_TAMPER_REJECT_PASS`
- `CERT_DETERMINISM_PASS`
- `BENCHMARK_CERT_EXPORT_PASS`
- `INDEPENDENT_CERT_SAT_PASS`
- `INDEPENDENT_CERT_COMPONENTS_PASS`
- `INDEPENDENT_CERT_UNSAT_EXPLICIT_PASS`
- `INDEPENDENT_BCE_CHECK_PASS`
- `INDEPENDENT_VE_CHECK_PASS`
- `INDEPENDENT_COMPONENT_CHECK_PASS`
- `INDEPENDENT_2SAT_CHECK_PASS`
- `INDEPENDENT_TAMPER_REJECT_PASS`
- `INDEPENDENT_UNSAT_LIMITATION_PASS`
- `CERTIFICATION_METADATA_CONSISTENCY_PASS`
- `NATIVE_UNSAT_TRACE_EMPTY_PASS`
- `NATIVE_UNSAT_TRACE_2SAT_PASS`
- `NATIVE_UNSAT_TRACE_TAMPER_REJECT_PASS`
- `PROOF_TRACE_CERT_BUNDLE_PASS`
- `NO_FALSE_LRAT_FRAT_CLAIM_PASS`
- adversarial markers from `tests/test_adversarial_correctness.py`

## Run Examples

```bash
python -m witnora_core.runner examples/bce_demo.dimacs --c 2
python -m witnora_core.runner examples/treewidth_demo.dimacs --c 2
python -m witnora_core.runner examples/treewidth_demo.dimacs --c 1
python -m witnora_core.runner examples/multi_component_demo.dimacs --c 2
python -m witnora_core.runner examples/unsat_demo.dimacs --c 2
```
