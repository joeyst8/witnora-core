# Witnora Proof Format Roadmap

## Scope

Witnora-Core v0.3.0 added a proof-carrying certificate bundle and standalone
Witnora replay verifier for saved collapse paths. Witnora-Core v0.4.0 adds a
smaller independent raw checker that avoids importing solver/collapse modules
and recomputes supported checks from raw clauses.

v0.4.0 does not implement full LRAT or FRAT output.

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

Current v0.3 certificate bundles classify each step with
`external_proof_status`.

- `UP`: checked by Witnora replay; future LRAT-compatible for UNSAT branches.
- `PLE`: model-extension preprocessing; not a pure clausal refutation step.
- `SUB`: checked by Witnora replay; deletion is straightforward to audit.
- `BCE`: RAT-compatible in spirit, but v0.3 does not emit LRAT.
- `CD`: decomposition bookkeeping; not a clausal refutation step.
- `TREEWIDTH_SOLVE`: tractable solver boundary; not a clausal refutation step.
- `VE`: resolution-style transformation; LRAT export is not implemented.
- `2SAT_SOLVE`: internally checked SCC result; future UNSAT branch could emit a
  clausal refutation, but v0.3 does not.

## SAT Certificates

SAT certificates are not pure LRAT refutations. A SAT result is certified by:

1. the original CNF,
2. the collapse path,
3. the reconstruction trace,
4. the reconstructed assignment,
5. direct assignment verification against the original formula.

This is why v0.3 uses `SAT_ASSIGNMENT_RECONSTRUCTION` as a proof trace class for
SAT results.

## UNSAT Certificates

UNSAT certificates in v0.3 were certified by internal replay of transformations
and a final contradiction or 2-SAT SCC conflict. v0.4 accepts UNSAT in the
independent raw checker only when replay reaches an explicit empty clause or an
independently checked 2-SAT SCC contradiction.

This is not a claim of external LRAT or FRAT support.

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

v0.5 should focus on an LRAT/FRAT bridge:

1. Map explicit UNSAT branches to DRAT/LRAT-compatible proof fragments.
2. Add FRAT-style annotated transformation traces for preprocessing-heavy
   certificates.
3. Integrate an external checker for emitted refutation proofs.
4. Keep SAT certificates assignment/reconstruction based.
5. Optionally add Lean or Coq export for the structural replay layer.

## Forbidden Claims

Witnora-Core v0.4.0 does not claim:

- full LRAT support,
- full FRAT support,
- external checker validation,
- independent third-party proof checking,
- general UNSAT certification,
- P = NP,
- industrial SAT solver competitiveness,
- hardness of no-collapse formulas.
