# R-037: native 2-SAT SCC contradiction resolution certificates

**Verified green:** https://github.com/joeyst8/witnora-core/actions/runs/41769668057

## Actual Python-to-Rust module conversion

`witnora_core/two_sat_proof.py` was previously **not migrated**.
The new `rust/witnora-ve/src/two_sat_scc_witness.rs` implements the
original source-annotated implication graph, lexicographically
deterministic BFS witness paths in both directions of a conflicting
literal, path-edge provenance, sequential resolution and complementary
derived unit clauses.

`build_2sat_scc_resolution_native` exposes the result through PyO3,
and the opt-in `build_2sat_scc_proof_rust` adapter rebuilds the
original frozen Python proof dataclasses. Canonical `CNFFormula`
inputs are supported. The original Python function also accepts raw
iterables of clauses and those semantics remain authoritative.

## Differential and independent evidence

`tests/test_two_sat_scc_witness_rust.py` compares **1,600**
deterministic seeded unsatisfiable 2-CNF inputs against complete Python
`TwoSatSCCProof.to_dict()` records, including both paths, every
supporting clause, resolution sequence and chosen conflict variable.
It exercises explicitly requested conflict variables, SAT/no-witness
error cases, non-2-CNF rejection and a multi-step contradiction.
All prior Rust, Python and Ganak gates passed.

## Status / trust

One former `not_migrated` original Python core module advances to
`parallel_reference`: **25** parallel-reference, **535**
not-migrated, **0** originals retired. Python and Lean remain default
trust paths; no formal proof or global certificate semantics change.
