# Witnora Proof Format Roadmap

## Scope

Witnora-Core v0.3.0 added a proof-carrying certificate bundle and standalone
Witnora replay verifier for saved collapse paths. Witnora-Core v0.4.0 adds a
smaller independent raw checker that avoids importing solver/collapse modules
and recomputes supported checks from raw clauses.

Witnora-Core v0.5.0 adds precise SAT/UNSAT certification metadata and a
Witnora-native UNSAT trace for explicit-empty-clause and independently checked
2-SAT SCC contradictions. Witnora-Core v0.5.1 hardens the path dependency:
native UNSAT traces are checked only against the final state obtained by
independent replay of the collapse path from the original formula.

Witnora-Core v0.6.0 added an initial DRAT-style final-state experiment.
Witnora-Core v0.6.1 hardens this bridge: `proof.drat` is supported only when
it is checked end-to-end from `original.dimacs` by the internal RUP-subset
checker. v0.6.1 still does not implement full DRAT/RAT checking, LRAT, or FRAT
output. Witnora-Core v0.6.2 adds an optional `drat-trim` adapter and records
external DRAT verification only when the provided checker process actually runs
and accepts the exported proof. Witnora-Core v0.6.3 adds skipped-unless-present
real `drat-trim` smoke tests for exported unit-conflict, VE-derived, and
BCE+VE-derived UNSAT proofs. Witnora-Core v0.6.4 records these smoke examples
passing with a real `drat-trim` binary built from the upstream source.
Witnora-Core v0.7.0 adds DRAT-style export for supported 2-SAT SCC
contradictions by deriving complementary units from implication paths and then
deriving the empty clause. Witnora-Core v0.7.1 adds pre-benchmark real
`drat-trim` smoke coverage for subsumption, pure literal elimination, and
multi-component UNSAT certificates.

Witnora-Core v0.8.0 adds the public benchmark evaluation harness. Public
benchmark reports use strict categories that separate SAT assignment-verified
results, externally verified UNSAT results, unverified/native UNSAT results,
unsupported DRAT exports, no-collapse cases, timeouts, and errors.
Witnora-Core v0.8.1 packages a built-in public-style benchmark artifact
separately from the source archive without adding solver logic. Witnora-Core
v0.8.2 demotes that built-in suite to demo status and adds official CNFgen,
SATLIB-directory, and SAT-Competition-directory integration with explicit
NOT_RUN reporting when sources are unavailable. Witnora-Core v0.8.4 adds an
official CNFgen diagnostic matrix over pigeonhole, Tseitin, and parity families
for `c = 2, 3, 4`. Witnora-Core v0.8.5 adds an exact treewidth / VE-ordering
audit for small diagnostic CNFs.

Witnora-Core v0.9.0 adds a conservative explicit XOR/affine reasoning
prototype. Witnora-Core v0.9.1 hardens its soundness metadata and independent
checking. Witnora-Core v0.9.2 extends exact CNF XOR detection to full
k-variable forbidden-assignment encodings up to a configurable cap, default
`k <= 6`. It accepts sidecar XOR equations and exact CNF-encoded XOR patterns,
solves the resulting affine system by Gaussian elimination over GF(2), and
verifies SAT assignments against both the original CNF and the XOR equations.
Sidecar XOR equations define the combined input problem `CNF and XOR`; detected
CNF patterns are implied constraints. XOR UNSAT is native-only in v0.9.2 and is
not exported as DRAT, LRAT, or FRAT.

Witnora-Core v0.9.3 adds a bounded XOR-to-DRAT bridge for detected-CNF XOR
contradictions. The bridge may claim original-CNF DRAT only when the exact XOR
source clauses are already present in `original.dimacs`, the generated proof is
internally RUP-subset checked, and real `drat-trim` accepts `proof.drat`
against `original.dimacs`. Sidecar XOR contradictions remain native-only for
the original CNF unless a future combined proof base is explicitly encoded and
checked.

## What LRAT Is Appropriate For

LRAT is appropriate for checkable UNSAT/refutation proof workflows. It extends
DRAT-style proof traces with extra checking information so proof checkers can
validate additions efficiently and deterministically.

For Witnora, LRAT is relevant to future UNSAT branches where the transformation
path can be expressed as clausal proof additions/deletions ending in an empty
clause.

## What FRAT Is Appropriate For

FRAT is a flexible proof trace format intended to carry richer solver
information and support elaboration toward LRAT. It is a better long-term target
for annotated preprocessing and transformation traces because Witnora steps are
not all plain clausal refutation steps.

## Witnora Step Classification

Current certificate bundles classify each step with
`external_proof_status`.

- `UP`: checked by Witnora replay; future LRAT-compatible for UNSAT branches.
- `PLE`: model-extension preprocessing; not a pure clausal refutation step.
- `SUB`: checked by Witnora replay; deletion is straightforward to audit.
- `BCE`: RAT-compatible in spirit, but v0.5 does not emit LRAT.
- `CD`: decomposition bookkeeping; not a clausal refutation step.
- `TREEWIDTH_SOLVE`: tractable solver boundary; not a clausal refutation step.
- `VE`: resolution-style transformation; LRAT export is not implemented.
- `2SAT_SOLVE`: internally checked SCC result. v0.7 can export supported
  UNSAT SCC contradictions as RUP-checkable path-derived unit clauses followed
  by the empty clause.
- `XOR`: v0.9 sidecar or exact-pattern affine reasoning. SAT is checked by
  assignment verification against CNF and XOR equations. XOR UNSAT is native
  only unless the v0.9.3 bounded detected-CNF XOR-to-DRAT bridge produces a
  proof accepted by real `drat-trim` against `original.dimacs`.

## SAT Certificates

SAT certificates are not pure LRAT refutations. A SAT result is certified by:

1. the original CNF,
2. the collapse path,
3. the reconstruction trace,
4. the reconstructed assignment,
5. direct assignment verification against the original formula.

This is why Witnora uses `SAT_ASSIGNMENT_RECONSTRUCTION` as a proof trace class for
SAT results.

## UNSAT Certificates

UNSAT certificates in v0.3 were certified by internal replay of transformations
and a final contradiction or 2-SAT SCC conflict. v0.4 accepts UNSAT in the
independent raw checker only when replay reaches an explicit empty clause or an
independently checked 2-SAT SCC contradiction.

This is not a claim of external LRAT or FRAT support.

## v0.9.1 End-to-End RUP-Subset DRAT Bridge

v0.9.1 exports `proof.drat` only for supported UNSAT paths whose proof
additions are accepted by Witnora's internal RUP-subset checker starting from
the original CNF clause database. It also writes `drat_status.json`.

Supported proof lines:

- RUP additions for UP-shortened clauses,
- an empty-clause addition for explicit unit conflicts,
- RUP additions for VE-generated resolvents,
- deletion lines for BCE, PLE, subsumption, and VE clause removals,
- RUP additions for supported 2-SAT SCC contradictions. The exporter extracts
  paths `x -> -x` and `-x -> x`, resolves the path clauses to derive `(-x)` and
  `(x)`, then emits the empty clause.

Proof generation walks the collapse path in order. VE resolvents are emitted
before deleting eliminated-variable parent clauses. The final empty clause is
accepted only if it is RUP-checkable from the active proof database obtained by
processing the proof from `original.dimacs`. A proof containing only `0` is
rejected for nontrivial transformed paths unless `0` is already RUP from the
original CNF.

Supported exports record:

```json
{
  "proof_scope": "END_TO_END_FROM_ORIGINAL_CNF",
  "checked_against": "original.dimacs",
  "internal_rup_subset_checker_verified": true,
  "requires_external_checker": false,
  "external_checker": "NOT_RUN",
  "external_checker_ran": false,
  "external_checker_verified": false
}
```

If `--drat-trim path/to/drat-trim` is provided, Witnora runs that process only
as a proof checker, never as a solver. External verification is recorded only
when it runs and exits successfully:

```json
{
  "external_checker": "DRAT_TRIM",
  "external_checker_ran": true,
  "external_checker_verified": true,
  "external_checker_exit_code": 0
}
```

Unsupported or final-state-only paths are marked:

```json
{
  "drat_export_status": "UNSUPPORTED",
  "proof_scope": "FINAL_STATE_ONLY_UNSUPPORTED"
}
```

Unsupported in v0.9.1:

- full RAT checking,
- LRAT export,
- FRAT export,
- claims of external verification unless an external checker actually ran.

The v0.9.1 checker string is:

```text
witnora_internal_rup_subset_checker_v0.9.3
```

It is an internal RUP-subset proof checker, not a replacement for `drat-trim`
or a formally verified proof checker. The `drat-trim` adapter is optional and
`drat-trim` is not bundled.

To enable real smoke verification:

```bash
git clone https://github.com/marijnheule/drat-trim.git
cd drat-trim
make
WITNORA_DRAT_TRIM=$PWD/drat-trim python -m unittest tests.test_real_drat_trim_smoke -v
```

If no real checker is found, the smoke tests are skipped and certificate status
remains `external_checker: "NOT_RUN"`.

## v0.5.1 Native UNSAT Trace vs Standard SAT Proofs

v0.5 introduces `WITNORA_NATIVE_UNSAT_TRACE_V1`. v0.5.1 makes the dependency
explicit with `depends_on_replayed_collapse_path: true` in `proof_trace.json`
and `native_unsat_trace_scope: END_TO_END_WITH_COLLAPSE_REPLAY` in the manifest.
It is a Witnora-native final-state trace, not DRAT, LRAT, or FRAT.

For explicit empty-clause UNSAT, the native trace records the unit propagation
conflict or VE empty resolvent that produced the empty clause. The independent
raw checker verifies that replay reaches an empty clause before checking the
native trace.

For 2-SAT SCC UNSAT, the native trace records the conflict variable, SCC
memberships for the positive and negative literals, and implication edges. The
independent raw checker recomputes the implication graph and SCC contradiction
from raw clauses after replay reaches the logged 2-SAT solve step.

The native trace is not a standalone proof. It is valid only with:

- `original.dimacs`,
- `collapse_path.json`,
- `component_results.json` when present,
- independent raw replay of every collapse-path step from the original formula.

A valid-looking `proof_trace.json` cannot rescue a corrupted BCE step, missing
VE resolvent, false component split, or forged 2-SAT SCC contradiction.

SAT results do not need an UNSAT refutation proof. They are certified through
collapse-path replay, reconstruction, and direct assignment verification against
the original CNF.

UNSAT results eventually need broader DRAT/LRAT/FRAT output for SAT-community
proof checking. v0.9.1 only claims DRAT-style proof export for supported
end-to-end RUP-checkable UNSAT paths, including supported 2-SAT SCC
contradictions. External verification is claimed only if `drat-trim` or another
recorded external checker actually ran and passed.

For public benchmarks, UNSAT result categories must distinguish successful
external proof checking from native-only or internally checked certificates.
v0.9.1 classifies an UNSAT result as
`UNSAT_DRAT_EXPORTED_VERIFIED` only when real `drat-trim` ran and accepted the
exported `proof.drat`. If Witnora reports UNSAT but `drat-trim` was not run or
did not accept the proof, the category is `UNSAT_NOT_EXTERNALLY_VERIFIED`. If
Witnora reports UNSAT but cannot export a supported end-to-end proof for that
path, the category is `UNSUPPORTED_DRAT`. Public benchmark claims should count
UNSAT as externally certified only in the first category.

With `--strict-unsat-external`, the benchmark records
`strict_unsat_external_pass: false` and the CLI exits nonzero when any UNSAT
case is not externally verified. This is a reporting guard, not a solver
feature.

## v0.9.1 Public Benchmark Reporting

The public benchmark harness supports a small in-repo `cnfgen-small` pilot
suite for unit tests, an in-repo `demo-cnfgen-artifact` suite for harness
validation only, official `cnfgen-official` CLI integration, and user-provided
DIMACS directories for SATLIB or SAT Competition subsets. Unit tests do not
download large public datasets. Public benchmark reports assign every case
exactly one category:

- `SAT_ASSIGNMENT_VERIFIED`
- `UNSAT_DRAT_EXPORTED_VERIFIED`
- `UNSAT_NOT_EXTERNALLY_VERIFIED`
- `UNSUPPORTED_DRAT`
- `NO_COLLAPSE_FOUND`
- `TIMEOUT`
- `ERROR`

`NO_COLLAPSE_FOUND` is not a hardness claim. `UNSAT_NOT_EXTERNALLY_VERIFIED`
and `UNSUPPORTED_DRAT` must not be counted as externally certified UNSAT.
Timeout and error cases are reported separately and are not partial results.

The v0.9.1 benchmark artifact writer creates a separate output tree with
`config.json`, `results.json`, `results.csv`, `REPORT.md`,
`selected_instances.txt`, `environment.txt`, `strict_verification_summary.json`,
`benchmark_manifest.json`, `generated_dimacs/`, `raw_outputs/`, `drat_logs/`,
and `certs/`. The artifact zip is separate from the source release zip.

Built-in demo suites must not be used as evidence of public benchmark
performance. Official CNFgen, SATLIB, and SAT Competition runs may be claimed
only when their corresponding suite status is `RUN`.

## v0.9.1 Official CNFgen Diagnostic Matrix

The v0.9.1 diagnostic matrix runner uses official CNFgen, when installed, to
generate pigeonhole, Tseitin, and parity formulas. It runs each available family
with `c = 2, 3, 4`, records strict public categories, and packages a separate
artifact containing `matrix_summary.json`, `matrix_summary.csv`,
`MATRIX_SUMMARY.md`, per-family/per-c reports, generated DIMACS files,
certificates, DRAT logs, commands, and environment metadata.

This matrix is a boundary diagnostic. It may support claims such as "this
official CNFgen family/c configuration produced these categories under strict
UNSAT external verification." It must not be used to claim general SAT solver
performance, pigeonhole scalability, hardness of no-collapse cases, XOR
necessity from parity failures, full DRAT/RAT/LRAT/FRAT support, or P vs NP
progress.

## v0.9.1 Exact Treewidth / VE Ordering Audit

The v0.9.1 treewidth audit is a diagnostic tool for small CNFs. It builds the
primal graph, searches exact bounded elimination orders from low `c` up to a
configured cap, independently verifies any order, and compares that result with
Witnora's normal solver output.

The audit is intended to distinguish:

- a real VE/order-search bug, when an order exists within the tested `c` but
  Witnora returns no-collapse,
- expected no-collapse under the current width budget,
- inconclusive cases caused by timeout, skip limits, or insufficient max `c`.

This audit may use exhaustive search or branch-and-bound on small graphs only.
It is not new solver logic, not a hardness oracle, and not evidence that larger
formulas are hard. Claims about specific formulas such as `php_4_3` are treated
as hypotheses to test against the actual CNF encoding and primal graph.

## v0.9.3 Explicit XOR / Affine Prototype

The v0.9.3 XOR route is intentionally conservative. It supports:

- explicit sidecar equations of the form `xor 1 2 3 = 0`,
- exact two-variable equality and disequality CNF patterns,
- exact three-variable parity CNF patterns when all four required clauses are
  present,
- exact k-variable full CNF parity encodings up to `--detect-xor-max-k`,
  default `k <= 6`,
- Gaussian elimination over GF(2) with deterministic free-variable assignment.
- bounded XOR-to-DRAT export for detected-CNF XOR contradictions when real
  `drat-trim` verifies the proof against `original.dimacs`.

It does not support:

- broad heuristic XOR extraction,
- CryptoMiniSat-style XOR discovery,
- arbitrary large or over-cap CNF-to-XOR recovery,
- DRAT/LRAT/FRAT export for sidecar-only XOR UNSAT as an original-CNF claim,
- full or heuristic XOR DRAT export.

For SAT, the certificate model is still assignment based: the reconstructed
assignment must satisfy the original CNF and every XOR equation. Certificate
bundles include `xor_system.json`, `xor_trace.json`, and `xor_status.json` when
XOR reasoning is used.

Detected CNF XOR patterns are used as implied constraints only. v0.9.3 records
`detection_mode: "IMPLIED_CONSTRAINT_ONLY"`,
`source_clauses_removed: false`, the exact source clauses, extra clauses
touching the same variables, `exact_full_encoding: true`, and `safe_use: true`.
The source clauses remain in the CNF. Extra clauses are safe only because
Witnora still verifies the original CNF; detected XOR is not a local
replacement.

The independent raw checker verifies that detected source clauses exist in the
original CNF, exactly equal the full forbidden-assignment encoding for the
claimed k-variable XOR relation, did not claim clause removal, and list the
extra touching clauses deterministically.

For UNSAT, v0.9.3 reports `UNSAT_XOR_NATIVE` first. If the bounded detected-CNF
XOR-to-DRAT bridge is disabled, over cap, unsupported, fails, or real
`drat-trim` is unavailable, benchmark/public reporting maps this to
`UNSAT_XOR_NATIVE_NOT_DRAT`. If the bridge verifies with real `drat-trim`
against `original.dimacs`, metadata records `xor_drat_status: "VERIFIED"`,
`proof_base: "original_cnf"`, and `drat_claim: "EXPORTED_VERIFIED"`.
Sidecar XOR contradictions define `CNF and XOR-sidecar`; they do not prove the
original CNF is UNSAT.

### XOR Exact Pattern Soundness

For variables `V = {x1, ..., xk}` and RHS `b`, the exact full CNF encoding of
`x1 xor ... xor xk = b` contains one clause for every assignment to `V` whose
parity is not `b`. Each such clause is falsified only by that forbidden
assignment. Therefore the conjunction of the source clauses is equivalent to
the XOR equation on `V`. Adding the detected XOR equation as an implied
constraint while retaining the source clauses is satisfiability-preserving for
SAT witnesses.

### Bounded XOR-to-DRAT Bridge Soundness

For detected-CNF XOR equations whose exact full CNF encodings are present in
the original formula, v0.9.3 may use Gaussian elimination to identify an
inconsistent detected subsystem and then build a bounded resolution/RUP proof
from the detected source clauses. Gaussian elimination is only a proof guide.
The proof claim is accepted only if the generated `proof.drat` is checked
internally and real `drat-trim` verifies it against `original.dimacs`.

Sidecar XOR equations are not necessarily implied by the original CNF. They
define a combined input problem. v0.9.3 does not claim original-CNF DRAT for
sidecar-only XOR contradictions.

Likely RAT-compatible or clausal-proof-compatible areas:

- `BCE`, through blocked/RAT-style deletion reasoning.
- Clause deletion and subsumption audit trails.
- Variable elimination through explicit resolvent additions.
- Unit propagation conflict to an empty clause.

Steps needing special handling:

- component decomposition,
- reconstruction traces,
- SAT assignments,
- bounded-treewidth solve summaries,
- non-refutational preprocessing that relies on model extension.

## v0.4 Independent Raw Checker

The independent raw checker:

- parses DIMACS without using Witnora CNF classes,
- recomputes canonical clause sets and formula hashes,
- independently checks BCE resolvents,
- independently checks VE resolvents and width caps,
- independently checks component splits through the incidence graph,
- independently checks SAT assignments for 2-SAT steps,
- independently checks 2-SAT UNSAT through SCCs,
- verifies reconstructed SAT assignments against the original formula.

It is not formally verified and is not an independent third-party checker.

## Future Plan

The next proof-format milestones should keep the bridge conservative:

1. Improve DRAT coverage while keeping internal proof checking honest.
2. Test emitted proofs with `drat-trim` or another external checker.
3. Add LRAT for supported DRAT/RUP fragments after external validation.
4. Add FRAT-style annotated transformation traces for preprocessing-heavy
   certificates.
5. Keep SAT certificates assignment/reconstruction based.
6. Only after external checker success, use
   `EXTERNAL_DRAT_LRAT_FRAT_VERIFIED`.
7. Optionally add Lean or Coq export for the structural replay layer.

## Forbidden Claims

Witnora-Core v0.9.3 does not claim:

- full DRAT/RAT support,
- full LRAT support,
- full FRAT support,
- full XOR extraction,
- CryptoMiniSat-style XOR discovery,
- DRAT/LRAT/FRAT support for XOR UNSAT,
- external checker validation unless an external checker actually ran,
- independent third-party proof checking,
- general SAT-community UNSAT certification,
- standalone native UNSAT proofs,
- P = NP,
- industrial SAT solver competitiveness,
- hardness of no-collapse formulas.
