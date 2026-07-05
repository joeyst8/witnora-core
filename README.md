# Witnora-Core v0.9.7

Witnora-Core v0.9.7 is a certified collapse-path prototype for CNF SAT formulas. It is not a general SAT solver and makes no `P = NP` claim. Its primary artifact is a deterministic, replay-verifiable collapse path: a sequence of satisfiability-preserving transformations, tractable solves, SAT witness reconstruction, and final verification against the original CNF. v0.9.3 adds a bounded XOR-to-DRAT bridge for detected-CNF XOR contradictions verified by real `drat-trim`; v0.9.3.1 clarifies public UNSAT status/category metadata; v0.9.4 adds an official CNFgen XOR diagnostic artifact runner; v0.9.5 externally certifies official CNFgen `tseitin_10`; v0.9.6 diagnoses the `tseitin_15` proof blowup; v0.9.7 makes the sparse/min-fill XOR elimination trace deterministic, certificate-recorded, independently replayable, and usable for DRAT export.

No external SAT solver, GNN, MCTS, LRAT/FRAT emitter, full XOR extractor, or brute-force solver for arbitrary formulas is included.

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

## Explicit XOR / Affine Prototype

v0.9.3 adds a conservative XOR route over GF(2). It supports explicit sidecar
equations and exact full-CNF XOR patterns only; it is not a CryptoMiniSat-style XOR
extractor and does not claim to detect arbitrary algebraic structure hidden in
CNF.

An XOR sidecar file uses lines such as:

```text
xor 1 2 3 = 0
xor 4 5 = 1
```

Run with:

```bash
python -m witnora_core.runner input.dimacs --xor input.xor --c 2
python -m witnora_core.runner input.dimacs --detect-xor --c 2
python -m witnora_core.runner input.dimacs --detect-xor --detect-xor-max-k 6 --c 2
python -m witnora_core.runner input.dimacs --detect-xor --export-cert out.wcert --export-drat --xor-drat --drat-trim path/to/drat-trim --c 2
```

Sidecar XOR equations define the combined problem `CNF and XOR`; they are not
claimed to be implied by the CNF alone. Detected CNF XOR patterns are different:
they are accepted only when the source clauses exactly equal a full
forbidden-assignment encoding of an XOR equation.

The Gaussian elimination routine canonicalizes equations, cancels duplicate
variables mod 2, assigns free variables deterministically `False`, and records
rank, pivot variables, free variables, and an elimination trace.

The CNF pattern detector is deliberately narrow:

- `(not x or y) and (x or not y)` gives `x xor y = 0`,
- `(x or y) and (not x or not y)` gives `x xor y = 1`,
- exact 3-variable parity encodings are detected only when all four required
  clauses are present,
- exact k-variable parity encodings are detected up to `--detect-xor-max-k`
  when all `2^(k-1)` required forbidden-assignment clauses are present.

The default exact pattern cap is `k <= 6`. Witnora groups only by the exact
variable set appearing in full-width clauses. It does not search arbitrary
subsets and does not perform heuristic XOR mining.

Detected pattern clauses are left in the CNF in v0.9.3. XOR equations are used
as additional implied constraints, not as replacements for CNF clauses. Any SAT
result must still verify the original CNF and all XOR equations.

Every detected XOR equation records:

- `detection_mode: "IMPLIED_CONSTRAINT_ONLY"`,
- `source_clauses_removed: false`,
- exact source clauses,
- `exact_full_encoding: true`,
- extra clauses touching the same variables,
- `safe_use: true`.

Extra clauses touching the same variables are allowed only because the source
CNF remains in force and final SAT assignments are checked against the original
CNF. If local equivalence/replacement is added in a future release, it needs a
separate explicit proof; v0.9.3 does not remove or replace XOR source clauses.

XOR-aware final classes may use:

- `final_class: "XOR_AFFINE"`,
- `final_class: "CNF_XOR_COMBINED"`,
- internal `status: "UNSAT_XOR_NATIVE"` with `final_class: "XOR_UNSAT_NATIVE"`.

Public reports separate logical result, discovery route, and certification:

- logical `status`: `SAT`, `UNSAT`, `NO_COLLAPSE_FOUND`, `TIMEOUT`, or `ERROR`,
- `discovery_route`: for example `XOR_NATIVE_CONTRADICTION` or `XOR_SIDECAR_CONTRADICTION`,
- `certification_level`: for example `EXTERNAL_DRAT_VERIFIED` or `NATIVE_XOR_ONLY`,
- `public_category`: the benchmark/reporting bucket.

XOR-native UNSAT is native-only unless the bounded XOR-to-DRAT bridge succeeds.
v0.9.3 can export a DRAT/RUP proof for detected-CNF XOR contradictions only
when the exact source clauses are already present in `original.dimacs` and real
`drat-trim` verifies `proof.drat` against that original CNF. In that case
metadata records `xor_drat_status: "VERIFIED"`, `proof_base: "original_cnf"`,
and `drat_claim: "EXPORTED_VERIFIED"`.

If the bridge is disabled, over cap, fails, or real `drat-trim` is unavailable,
the result remains native-only and public reporting must classify it as
`UNSAT_XOR_NATIVE_ONLY`. Sidecar XOR contradictions define the combined
problem `CNF and XOR-sidecar`; v0.9.3 does not claim original-CNF DRAT for
sidecar-only contradictions.

If detected-CNF XOR UNSAT is externally verified by real `drat-trim` against
`original.dimacs`, public reporting uses `public_category:
"UNSAT_DRAT_EXPORTED_VERIFIED"` with `discovery_route:
"XOR_NATIVE_CONTRADICTION"` and `certification_level:
"EXTERNAL_DRAT_VERIFIED"`. It is not reported as native-only.

v0.9.5 improves the detected-CNF XOR proof bridge by deriving a bounded
resolution proof through variable elimination over detected XOR source clauses,
instead of attempting an unbounded generic resolution closure. The bridge
records row-width, proof-size, proof-byte, timeout, internal RUP, and
`drat-trim` status metadata in `xor_drat_status.json`.

For official CNFgen `tseitin_10`, the v0.9.5 focused diagnostic can export
`proof.drat` and verify it with real `drat-trim` against `original.dimacs`,
classifying that row as `UNSAT_DRAT_EXPORTED_VERIFIED`. Larger Tseitin rows are
attempted only under explicit caps and remain native-only or skipped if the
proof exceeds the configured limits. Parity support and broader XOR extraction
remain deferred.

v0.9.6 diagnosed the scaling blocker for official CNFgen `tseitin_15`: the
Gaussian-certified path reached peak XOR row width 14, while a deterministic
sparse/min-fill diagnostic reached peak width 8. v0.9.7 makes that
sparse/min-fill order certificate-recorded and independently replayable, and
uses the recorded row-operation trace for XOR-to-DRAT export. When real
`drat-trim` verifies the exported `proof.drat` against `original.dimacs`,
`tseitin_15 c=2` is reported as `UNSAT_DRAT_EXPORTED_VERIFIED`.

This is still a proof-engineering scaling result, not parity support, broad
XOR extraction, a CryptoMiniSat-style claim, or a competitive SAT claim.

## Official CNFgen XOR Diagnostic

v0.9.4 adds a reproducible diagnostic runner for official CNFgen parity,
Tseitin, and pigeonhole instances:

```bash
python -m witnora_core.xor_diagnostic \
  --out-root outputs/v0.9.4-official-xor-diagnostic \
  --c-values 2 3 4 \
  --sensitivity-max-k 4 5 6 \
  --drat-trim path/to/drat-trim \
  --zip witnora-core-v0.9.4-official-xor-diagnostic.zip
```

The diagnostic compares against the v0.8.4 official CNFgen matrix summary and
reports public categories separately. It is not a competitive SAT benchmark.
If a detected XOR contradiction is over the configured diagnostic proof cap, it
is reported as `UNSAT_XOR_NATIVE_ONLY`; it is not counted as externally
verified. No `UNSAT_DRAT_EXPORTED_VERIFIED` row is produced unless real
`drat-trim` verifies `proof.drat` against `original.dimacs`.

The focused v0.9.7 Tseitin proof/scaling diagnostic can be run with:

```bash
python -m witnora_core.xor_drat_diagnostic \
  --family tseitin \
  --instances tseitin_10 tseitin_15 \
  --c-values 2 \
  --detect-xor-max-k 6 \
  --xor-drat \
  --elim-orders gaussian sparse-min-fill \
  --drat-trim path/to/drat-trim \
  --profiles conservative \
  --out-root outputs/v0.9.7-minfill-xor-drat \
  --zip witnora-core-v0.9.7-minfill-xor-drat.zip
```

This command is a proof-engineering diagnostic. It does not add new XOR
detection, does not target parity, and does not use any external SAT solver.
The native XOR row-operation trace is replayable by the independent checker;
the original-CNF UNSAT claim is accepted only when real `drat-trim` verifies
`proof.drat`.

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
python -m witnora_core.benchmark --dimacs-dir path/to/dimacs --c 4 --out dimacs_results.json
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

## Public Benchmark Evaluation

v0.8.2 and later include official public benchmark integration and artifact writing. It
supports:

- `--public-suite cnfgen-official`, using an official `cnfgen` CLI on PATH,
- `--public-suite satlib --dimacs-dir path/to/satlib_subset`,
- `--public-suite satcomp --dimacs-dir path/to/satcomp_subset`,
- `--public-suite demo-cnfgen-artifact`, a built-in demo suite for harness validation only,
- `--public-suite cnfgen-small`, a small built-in demo suite for unit tests,
- `--dimacs-dir path/to/satlib_subset` for user-provided SATLIB CNFs,
- `--dimacs-dir path/to/satcomp_subset` for user-provided SAT Competition CNFs.

The built-in demo suites are not official benchmark evidence. Reports label
them with `suite_source_type: BUILT_IN_DEMO` and must say they are built into
Witnora for harness validation only.

Official CNFgen is not bundled. If `cnfgen` is missing, Witnora reports
`suite_status: NOT_RUN` and `not_run_reason: OFFICIAL_CNFGEN_NOT_AVAILABLE`
instead of silently falling back to built-in formulas. Install official CNFgen
with:

```bash
pip install cnfgen
```

SATLIB and SAT Competition inputs are not bundled. Download or unpack public
DIMACS CNFs separately, then point `--dimacs-dir` at a selected subset.

Example public benchmark commands:

```bash
python -m witnora_core.benchmark --public-suite cnfgen-official --c 2 --out results.json --csv results.csv --report REPORT.md --export-certs certs/ --strict-unsat-external --drat-trim path/to/drat-trim --timeout-seconds 300
python -m witnora_core.benchmark --public-suite satlib --dimacs-dir path/to/satlib_subset --c 2 --out satlib_results.json --csv satlib.csv --report SATLIB_REPORT.md --export-certs certs_satlib/ --strict-unsat-external --drat-trim path/to/drat-trim --max-instances 100
python -m witnora_core.benchmark --public-suite satcomp --dimacs-dir path/to/satcomp_subset --c 2 --out satcomp_results.json --csv satcomp.csv --report SATCOMP_REPORT.md --export-certs certs_satcomp/ --strict-unsat-external --drat-trim path/to/drat-trim --timeout-seconds 300 --max-instances 50
python -m witnora_core.benchmark --public-suite demo-cnfgen-artifact --c 2 --out demo_results.json --csv demo.csv --report DEMO_REPORT.md --export-certs demo_certs/ --strict-unsat-external --drat-trim path/to/drat-trim
```

Benchmark outputs should be packaged separately from source archives.
The artifact writer creates `README.md`, `config.json`, `results.csv`,
`results.json`, `REPORT.md`, `selected_instances.txt`, `environment.txt`,
`strict_verification_summary.json`, `benchmark_manifest.json`, `drat_logs/`,
`generated_dimacs/`, `raw_outputs/`, and `certs/` under an output directory such
as `outputs/v0.9.1-public-benchmark/<suite_name>/`.

Each public benchmark instance receives exactly one category:

- `SAT_ASSIGNMENT_VERIFIED`
- `UNSAT_DRAT_EXPORTED_VERIFIED`
- `UNSAT_XOR_NATIVE_ONLY`
- `UNSAT_NOT_EXTERNALLY_VERIFIED`
- `UNSUPPORTED_DRAT`
- `NO_COLLAPSE_FOUND`
- `TIMEOUT`
- `ERROR`

Strict public reports should use `--strict-unsat-external`. In that mode, the
CLI exits nonzero if any UNSAT result is not externally verified by real
`drat-trim`. `UNSAT_NOT_EXTERNALLY_VERIFIED`, `UNSUPPORTED_DRAT`, and
`UNSAT_XOR_NATIVE_ONLY` must not be aggregated with
`UNSAT_DRAT_EXPORTED_VERIFIED`. `NO_COLLAPSE_FOUND` is still not a hardness
claim.

## Official CNFgen Diagnostic Matrix

v0.8.4 and later include an official CNFgen diagnostic matrix runner. It is intended to
measure the current collapse boundary across formula family and `c` value, not
to make a broad solver-performance claim.

Example:

```bash
python -m witnora_core.cnfgen_matrix --out-root outputs/v0.9.1-cnfgen-diagnostic --families pigeonhole tseitin parity --c-values 2 3 4 --timeout-seconds 300 --strict-unsat-external --drat-trim path/to/drat-trim --zip witnora-core-v0.9.1-cnfgen-diagnostic-benchmark.zip
```

The matrix uses official CNFgen commands when available:

- pigeonhole: `cnfgen php 3 2` through `cnfgen php 10 9`
- Tseitin: deterministic seeded `cnfgen --seed N tseitin N`
- parity: deterministic seeded `cnfgen --seed N parity N`

The artifact includes `matrix_summary.json`, `matrix_summary.csv`,
`MATRIX_SUMMARY.md`, per-family/per-`c` JSON/CSV/Markdown reports, generated
DIMACS files, certificate bundles, DRAT logs, environment metadata, and the
exact commands run. Unsupported or unavailable families are marked `NOT_RUN`
with a reason. The runner must not fall back to built-in demo formulas and call
them official.

Allowed interpretation: the diagnostic matrix reports where the current
collapse grammar succeeds, fails to collapse, times out, or produces externally
verified UNSAT certificates. Forbidden interpretation: it does not prove
hardness, does not claim Witnora solves pigeonhole generally, does not claim
XOR/affine collapse is necessary from parity failures, and does not imply P vs
NP progress.

## Exact Treewidth / VE Ordering Audit

v0.8.5 and later include a diagnostic exact-width audit tool:

```bash
python -m witnora_core.treewidth_audit --out-dir outputs/v0.9.1-treewidth-audit --timeout-seconds 60 --zip witnora-core-v0.9.1-treewidth-audit.zip
```

The audit builds the primal graph of selected small CNFs, searches for exact
bounded-width elimination orders from `c = 0` up to a chosen cap, independently
verifies any order it finds, and compares the result with Witnora's normal
solver output. It is used to distinguish:

- `EXPECTED_NO_COLLAPSE_WIDTH_LIMIT`: no-collapse is explained by the tested
  width budget,
- `VE_ORDER_SEARCH_BUG`: an order exists within `c`, but the solver failed to
  use it,
- `AUDIT_INCONCLUSIVE`: the diagnostic timed out, skipped the formula, or did
  not test a high enough cap.

The audit is exponential and intended only for small formulas. It is not part of
the main solver route, does not claim hardness for skipped/no-collapse formulas,
and treats outside claims such as "php_4_3 has treewidth 3" as hypotheses to
verify rather than facts to assume.

## Proof-Carrying Certificates

Witnora-Core v0.3.0 added portable certificate bundles. v0.4.0 added the
independent raw checker. v0.5.0 cleaned up SAT/UNSAT certification metadata and
added a Witnora-native UNSAT trace for supported explicit-empty-clause and
2-SAT-SCC contradictions. v0.5.1 hardens the UNSAT path dependency: a native
UNSAT trace is checked only after the independent raw checker replays the full
collapse path from `original.dimacs`. v0.6.0 added a minimal DRAT-style bridge
as an initial final-state experiment. v0.6.1 hardens that bridge: exported
`proof.drat` files are supported only when the internal RUP-subset checker
validates them end-to-end from `original.dimacs`. v0.6.2 adds an optional
`drat-trim` adapter for external verification of exported `proof.drat` files.
v0.6.3 adds real `drat-trim` smoke tests that run when a real checker is
available on PATH or through `WITNORA_DRAT_TRIM`. v0.6.4 records real
`drat-trim` verification passing for the supported smoke examples when the
checker is built from upstream source. v0.7.0 adds DRAT-style export for
supported 2-SAT SCC contradictions by deriving complementary units from logged
implication paths, then deriving the empty clause. v0.7.1 adds pre-benchmark
proof-coverage smoke tests for subsumption, pure literal elimination, and
multi-component UNSAT certificates. v0.8.0 added public benchmark categories,
CSV/JSON/Markdown public reports, per-instance timeout handling, and strict
UNSAT external verification mode. v0.8.1 packaged a built-in public-style
benchmark artifact separately from the source release. v0.8.2 demotes that
built-in suite to demo status and adds official CNFgen, SATLIB-directory, and
SAT-Competition-directory integration with NOT_RUN reporting. v0.8.4 added an
official CNFgen diagnostic matrix over pigeonhole, Tseitin, and parity families
for `c = 2, 3, 4`. v0.8.5 adds an exact treewidth / VE-ordering audit for small
diagnostic CNFs. v0.9.0 adds explicit XOR sidecars and exact small CNF XOR
pattern detection as a prototype affine route. v0.9.1 hardens exact pattern
metadata and independent checking for extra-clause and malformed-pattern cases.
v0.9.2 extends exact CNF XOR detection to full k-variable parity encodings up
to a configurable cap, default `k <= 6`, while retaining all source clauses.
v0.9.3 adds bounded XOR-to-DRAT export for detected-CNF XOR contradictions
only when real `drat-trim` verifies the proof against `original.dimacs`.

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
- `proof.drat`, only when `--export-drat` succeeds for a supported UNSAT path
- `drat_status.json`, when `--export-drat` is requested
- `xor_system.json`, `xor_trace.json`, and `xor_status.json`, only when XOR
  reasoning is used
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

UNSAT is independently accepted only when independent replay from the original
formula reaches an explicit empty clause or when a 2-SAT SCC contradiction is
independently checked in the replayed final state. For public benchmarks, UNSAT
is counted as externally certified only when `proof.drat` is exported and real
`drat-trim` accepts it.

## Minimal DRAT Bridge

v0.9.1 can export a DRAT-style proof for supported end-to-end
RUP-checkable UNSAT paths:

```bash
python -m witnora_core.runner examples/unsat_demo.dimacs --c 2 --export-cert out.wcert --export-drat
python -m witnora_core.drat_check out.wcert/original.dimacs out.wcert/proof.drat
```

Optionally run an installed `drat-trim` checker:

```bash
python -m witnora_core.runner examples/unsat_demo.dimacs --c 2 --export-cert out.wcert --export-drat --drat-trim path/to/drat-trim
python -m witnora_core.drat_check out.wcert/original.dimacs out.wcert/proof.drat --drat-trim path/to/drat-trim
```

The bridge is intentionally narrow. It supports:

- explicit unit-propagation conflict to an empty clause,
- UP-shortened clauses that are RUP-checkable,
- PLE, subsumption, and BCE clause deletion lines,
- VE resolvent additions when the logged resolvents exactly match recomputation,
- VE deletions after resolvent additions,
- 2-SAT SCC contradictions by extracting paths `x -> -x` and `-x -> x`,
  deriving `(-x)` and `(x)`, then deriving the empty clause,
- final explicit empty clause.

The proof is generated from the original CNF proof state. VE resolvents are
emitted before deleting their parent clauses, and the final empty clause must be
RUP-checkable from the active clause database reached by processing the proof
from `original.dimacs`. A proof containing only a final-state `0` is rejected
for nontrivial transformed paths unless `0` is already RUP from the original
CNF.

It does not implement full DRAT/RAT checking. The included checker is an
internal RUP-subset checker:

```json
{
  "checker": "witnora_internal_rup_subset_checker_v0.9.3",
  "checked_against": "original.dimacs"
}
```

For supported 2-SAT SCC contradictions, `drat_status.json` records
`supported_reason: "2SAT_SCC_TO_DRAT_EXPORTED"` and includes the extracted
paths and derived clauses under `two_sat_scc_proof`. If a path cannot be
extracted or the derived clauses are not RUP-checkable from the active proof
state, the export is marked unsupported instead of being overclaimed.

`drat_status.json` records whether `proof.drat` was exported, whether the
internal RUP-subset checker verified it, and whether an optional external
checker was run. Supported exports use:

```json
{
  "proof_scope": "END_TO_END_FROM_ORIGINAL_CNF",
  "checked_against": "original.dimacs",
  "internal_rup_subset_checker_verified": true,
  "requires_external_checker": false
}
```

Unsupported or final-state-only paths are marked with
`proof_scope: "FINAL_STATE_ONLY_UNSUPPORTED"`. External verification is `false`
unless an external checker is actually provided and succeeds.

`drat-trim` is not bundled and is not used to solve formulas. It is only an
optional proof checker for a `proof.drat` file that Witnora already exported
and internally checked. `drat_status.json` records
`external_checker: "DRAT_TRIM"`, `external_checker_ran: true`, and
`external_checker_verified: true` only when the provided process actually runs
and exits successfully. If no path is provided, the status remains
`external_checker: "NOT_RUN"` and `external_checker_verified: false`.

Install/build `drat-trim` from upstream if it is not available:

```bash
git clone https://github.com/marijnheule/drat-trim.git
cd drat-trim
make
./drat-trim path/to/original.dimacs path/to/proof.drat
```

On Windows, build it in WSL, MSYS2, MinGW, or another environment with `make`
and a C compiler, then pass the resulting executable with `--drat-trim` or set:

```bash
WITNORA_DRAT_TRIM=/path/to/drat-trim python -m unittest tests.test_real_drat_trim_smoke -v
```

If no real checker is found, the real smoke tests are skipped and external
verification remains `NOT_RUN`.

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

Current certificates use the most precise supported level. SAT results use
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

This classification is deliberately conservative. v0.8.2 does not claim full
DRAT, LRAT, or FRAT support, and SAT certificates remain
assignment/reconstruction certificates rather than clausal refutations.

## Pre-Benchmark UNSAT Verification Guard

Public benchmark reporting must separate UNSAT results that have real external
proof checking from UNSAT results that are native-only or internally checked
only. v0.8.2 exposes public benchmark categories:

- `UNSAT_DRAT_EXPORTED_VERIFIED` when `proof.drat` exists and real
  `drat-trim` ran successfully,
- `UNSAT_NOT_EXTERNALLY_VERIFIED` when an UNSAT result lacks successful external
  `drat-trim` verification,
- `UNSUPPORTED_DRAT` when Witnora reports UNSAT but cannot export supported
  end-to-end DRAT-style proof for that path.

When `--strict-unsat-external` is set, the benchmark fails strict mode for
`UNSAT_NOT_EXTERNALLY_VERIFIED` and `UNSUPPORTED_DRAT`. SAT benchmark results
remain assignment verified against the original CNF.

## Native UNSAT Trace

For supported UNSAT cases, v0.5.1 may include `proof_trace.json` with:

```json
{
  "proof_trace_format": "WITNORA_NATIVE_UNSAT_TRACE_V1",
  "depends_on_replayed_collapse_path": true,
  "external_standard": "NONE",
  "lrat_frat_status": "NOT_EXPORTED"
}
```

Supported native UNSAT trace reasons are:

- `EXPLICIT_EMPTY_CLAUSE`
- `INDEPENDENT_2SAT_SCC`

The native trace is not a standalone proof. It is valid only together with
`original.dimacs`, `collapse_path.json`, `component_results.json` when present,
and independent replay from the original formula. The manifest records:

```json
"native_unsat_trace_scope": "END_TO_END_WITH_COLLAPSE_REPLAY"
```

The independent raw checker verifies every collapse-path step first, including
BCE blockedness, VE resolvents, and incidence-graph component decomposition.
Only after that replay reaches the final formula state does it check the native
trace against that replayed final state. For explicit empty-clause UNSAT it
confirms the replayed final state contains an empty clause. For 2-SAT SCC UNSAT
it recomputes the implication graph and SCC contradiction from raw clauses. This
native trace is not DRAT, LRAT, or FRAT and does not replace standard UNSAT
proof formats.

When `proof.drat` is exported, it is an additional bridge artifact. Native
certificate verification remains required and still replays the collapse path
from the original formula.

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
- `DRAT_EXPORT_EMPTY_CONFLICT_PASS`
- `DRAT_EXPORT_VE_UNSAT_PASS`
- `DRAT_2SAT_SCC_EXPORTED_PASS`
- `TWO_SAT_SCC_DRAT_EXPORT_PASS`
- `TWO_SAT_SCC_DRAT_TRIM_PASS` when real `drat-trim` is available
- `TWO_SAT_SCC_PATH_EXTRACTION_PASS`
- `TWO_SAT_SCC_FAKE_EDGE_REJECT_PASS`
- `TWO_SAT_SCC_FINAL_STATE_ONLY_REJECT_PASS`
- `TWO_SAT_SCC_AFTER_VE_DRAT_PASS`
- `DRAT_STATUS_2SAT_NO_LONGER_UNSUPPORTED_PASS`
- `REAL_DRAT_TRIM_SUBSUMPTION_PASS`
- `REAL_DRAT_TRIM_PLE_PASS`
- `REAL_DRAT_TRIM_MULTI_COMPONENT_UNSAT_PASS`
- `BENCHMARK_UNSAT_EXTERNAL_VERIFICATION_GUARD_PASS`
- `DRAT_TAMPER_REJECT_PASS`
- `DRAT_STATUS_NO_FALSE_CLAIM_PASS`
- `DRAT_CERT_BUNDLE_PASS`
- `UNSAT_REJECTS_FAKE_BCE_EVEN_WITH_VALID_FINAL_TRACE_PASS`
- `UNSAT_REJECTS_MISSING_VE_RESOLVENT_EVEN_WITH_VALID_FINAL_TRACE_PASS`
- `UNSAT_REJECTS_FAKE_2SAT_SCC_TRACE_PASS`
- `UNSAT_REJECTS_FAKE_COMPONENT_SPLIT_WITH_VALID_TRACE_PASS`
- `UNSAT_EMPTY_FROM_VE_UNSUPPORTED_OR_DERIVED_PASS`
- adversarial markers from `tests/test_adversarial_correctness.py`

## Run Examples

```bash
python -m witnora_core.runner examples/bce_demo.dimacs --c 2
python -m witnora_core.runner examples/treewidth_demo.dimacs --c 2
python -m witnora_core.runner examples/treewidth_demo.dimacs --c 1
python -m witnora_core.runner examples/multi_component_demo.dimacs --c 2
python -m witnora_core.runner examples/unsat_demo.dimacs --c 2
```
