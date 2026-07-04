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

Witnora-Core v0.6.0 adds a minimal DRAT-style bridge for supported
RUP-checkable UNSAT paths. It does not implement full DRAT/RAT checking, LRAT,
or FRAT output.

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
- `2SAT_SOLVE`: internally checked SCC result; future UNSAT branch could emit a
  clausal refutation, but v0.5 does not.

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

## v0.6 Minimal DRAT Bridge

v0.6 exports `proof.drat` only for supported UNSAT paths whose proof additions
are accepted by Witnora's internal RUP-subset checker. It also writes
`drat_status.json`.

Supported proof lines:

- RUP additions for UP-shortened clauses,
- an empty-clause addition for explicit unit conflicts,
- RUP additions for VE-generated resolvents,
- deletion lines for BCE, PLE, subsumption, and VE clause removals.

Unsupported in v0.6:

- conversion of arbitrary 2-SAT SCC contradictions to DRAT,
- full RAT checking,
- LRAT export,
- FRAT export,
- claims of external verification unless an external checker actually ran.

The checker is named:

```text
witnora_internal_rup_subset_checker_v0.6
```

It is an internal RUP-subset proof checker, not a replacement for `drat-trim`
or a formally verified proof checker.

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
proof checking. v0.6.0 only claims DRAT-style proof export for supported
RUP-checkable UNSAT paths. External verification is claimed only if an external
checker actually ran and passed.

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

v0.7 should focus on a conservative external proof bridge:

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

Witnora-Core v0.6.0 does not claim:

- full DRAT/RAT support,
- full LRAT support,
- full FRAT support,
- external checker validation unless an external checker actually ran,
- independent third-party proof checking,
- general SAT-community UNSAT certification,
- standalone native UNSAT proofs,
- P = NP,
- industrial SAT solver competitiveness,
- hardness of no-collapse formulas.
