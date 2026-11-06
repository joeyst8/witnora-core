# W030 cost-inclusive exploratory smoke — frozen before execution

**Phase:** exploratory smoke, not a representative SAT or P-vs-NP benchmark.

## Objective

Compare a new incremental Rust source-XOR certificate scanner against the
finished W027 whole-file Rust scanner and plain Kissat, paying the complete
precheck and subprocess overhead. Both Rust scanners return a source-auditable
UNSAT proof or `NO_CERTIFICATE`, never SAT. Kissat receives **unchanged CNF**.

## Frozen benchmark and controls

Exactly eight unique CNFs, enumerated with byte-level SHA-256 in
`research/results/w030_smoke_case_manifest.json`:

- 2 W026 SAT/UNSAT parity-matched CNFs with 20 core clauses, no noise;
- 2 W026 SAT/UNSAT CNFs with the same core **first** and 8192 noise clauses;
- 2 W026 SAT/UNSAT CNFs with the same core **last** and 8192 noise clauses;
- 2 independently constructed planted-SAT near-XOR decoys reused verbatim
  from W027 (`partial_256_noise4096`, `mixed_256_noise4096`).

The core-last condition is a deliberate countercontrol: it preserves the
multiset of clauses and truth status but prevents a premature prefix proof.
Manifest and clause-order equality are unit-tested before timing. The first
and last source order are *not* interchangeable for time measurement.

## Arms, caps, and measurement

- A: pinned Kissat `rel-4.0.4`, commit
  `8af8e56f174b778aef3aa45af9f739b2a5f492c2`;
- B: frozen W027 all-clauses-first Rust scanner, then unchanged-CNF Kissat;
- C: W030 streaming Rust scanner, then unchanged-CNF Kissat.

Three repetitions per case and arm, rotating arm order by case index and
repeat: **72 timed end-to-end invocations**, 6-second cap and 2 GiB address
space limit each. This is a short pilot cap only, **not** the previous full
W027 30-second performance protocol. The Python harness invokes programs,
measures whole subprocess and checking time, independently verifies source
parity proofs and SAT models, and rejects source label contradictions. Rust
remains the solver-side proof implementation.

One *additional, untimed* W030 call per case measures `read_clauses` and checks
proof provenance; it is diagnostic only, never substituted for measured
per-arm latency. Identical three-repeat case/arm medians are reported even
if the hypothesis fails. The raw JSON and all per-case rows are retained.

## Falsification criteria

1. Any incorrect verdict, failed independent XOR proof, failed SAT model,
   missing arm, unverified source hash, or missing measurement fails CI.
2. If W030 remains slower than Kissat on both SAT and UNSAT, its prefix-proof
   optimization has failed even on favorable examples.
3. If core-first shows a speedup but core-last does not, the gain must be
   stated as **clause-order sensitive**, not a general solver advance.
4. If SAT or adversarial decoys incur more overhead, report that explicitly;
   do not suppress negative controls or assume beneficial UNSAT prevalence.

## Next step after smoke

Only if correctness and some cost advantage survive the exploratory controls,
freeze a larger full W030 benchmark with multiple deterministic shuffled
clause orders, exact source hashes and external test domains before running.
No claim about P = NP, algorithmic polynomial complexity, or modern
solver superiority is licensed by this smoke test.
