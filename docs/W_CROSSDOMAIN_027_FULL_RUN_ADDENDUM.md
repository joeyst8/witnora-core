# W027 full-study execution addendum (frozen before first timing)

The primary protocol is
[`W_CROSSDOMAIN_027_COST_INCLUSIVE_SOLVER_PROTOCOL.md`](W_CROSSDOMAIN_027_COST_INCLUSIVE_SOLVER_PROTOCOL.md).
This note specifies the previously-unspecified deterministic near-XOR controls
and concrete runner implementation. **It does not revise the primary
decision rule or the first 6-case exploratory smoke results.**

## Frozen input strata and order

1. All W026 96 generator/seed/noise combinations, each with SAT and UNSAT
   partner: **192 CNFs**. Their noise fingerprints must match the archived
   W026 source records.
2. All eight externally sourced W022 VLSAT2 CNFs in the original W022
   archive order, with original compressed and decompressed SHA-256 hashes
   checked before timing. No source-based outcome replacement.
3. Four planted-SAT near-XOR decoys: partial and mixed 3-cube polarity
   patterns, each with either 64 signed triple supports or 256 supports
   plus 4096 independent noise clauses. Extra duplicate clauses and a
   deterministic full-clause permutation are included. All seeds, lengths,
   and byte-exact input SHA-256 digests are in
   [`w027_full_decoy_manifest.json`](../research/results/w027_full_decoy_manifest.json).
   Require zero complete parity tetrahedra, zero certificate shortcuts,
   and a verified planted all-false satisfying assignment.

Total: **204 CNFs**. No additional XOR-rich heldout source is claimed;
that optional stratum is unavailable unless separately pinned first.

## Frozen timing and checking

For every instance: three repetitions, 30-second **end-to-end** limit
and 2 GiB address-space limit, rotating arm order between repetitions.
Arms are plain Kissat rel-4.0.4 (`8af8e56f174b778aef3aa45af9f739b2a5f492c2`),
Witnora's Rust exact-source precheck plus unchanged CNF Kissat fallback,
and CryptoMiniSat release/v5.17.0 (`03954f7f7815ea3984774c95a66e7c224cd25952`)
when buildable. Default solver settings; record host and compiler versions.

Each solver's SAT witness must satisfy *every original clause*; each
Witnora UNSAT shortcut must carry independently audited source-clause
provenance. A source label is not itself a proof. Timeouts are censored,
not solutions. Only complete-case timings can contribute to an unqualified
paired-ratio summary; report wins, losses, timeouts, preprocessing cost,
and failures by stratum. Keep all raw repetitions.

If a runner correctness or build defect requires a fix after measurement
starts, preserve its original logs and identify every corrected run as
such. Do not alter sources, seeds, caps, or decision rule based on
timing outcomes.
