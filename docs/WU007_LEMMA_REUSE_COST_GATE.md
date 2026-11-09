# WU-007 — Amortization is real, but eager global lemma caching can lose

**Research status:** bounded deterministic synthetic cost accounting;
proof-checking tests and diagnostic Rust microbenchmarks. **No** claimed
new inference rule, novel complexity theorem, or SAT solver performance
breakthrough.

## Established prior work and narrow question

- Beame & Sun, *Extending CDCL to Disjunctions of Parity Equations*, SAT
  2026, DOI [10.4230/LIPIcs.SAT.2026.5](https://doi.org/10.4230/LIPIcs.SAT.2026.5):
  existing CDCL(⊕) and LRUP(⊕) framework used by WU-004–006.
- Pollitt et al., *Factoring Learned Clauses*, SAT 2026,
  DOI [10.4230/LIPIcs.SAT.2026.28](https://doi.org/10.4230/LIPIcs.SAT.2026.28):
  established global factoring of repeated learned-clause substructure,
  including XOR and ITE gates, with actual CaDiCaL experiments.
  **Reusing globally discovered XOR structure is not an original idea.**

WU-006 verified a two-stage procedure: derive guarded-XNF unit parity
lemmas with a known special case of affine resolution, independently
RUP(⊕)-certify each lemma, then use unit-only Gaussian closure to
propose rank-two strengthenings of sound rank-three target clauses.

WU-007 asks whether *keeping these verified intermediate lemmas*
amortizes their proof cost across multiple distinct target clauses, and
whether irrelevant lemmas or a global proof database can defeat the
savings. This is a deliberately narrower test than solver speed.

## Protocol and cost definitions

The Rust diagnostic `rust/witnora-ve/src/bin/wu007_lemma_amortization.rs`
reuses the independently tested WU-006 GF(2), two-clause consensus and
RUP(⊕) replay. It constructs rank-three target falsity spaces
`span(x=1,y=1,a_j=1)` with **distinct** `a_j` for each cut. For each
target, the bounded exact oracle enumerates its seven rank-two equation
subspaces, while the staged method nominates three and independently
RUP-certifies every one. It never enumerates Boolean assignments.

Three policies are compared:

1. **Global cached:** search for and certify all rank-one consensus lemmas
   once; retain all original and derived clauses globally; verify three
   candidates for each target in that full database.
2. **Repeated global:** rederive and recertify those same lemmas separately
   for *every* target, with the same full-database candidate verification.
   This deliberately measures the benefit of avoiding duplicate work.
3. **Privileged relevance oracle:** for each target, know exactly which
   subset of original clauses suffices; derive and verify only from that
   subset. Proofs from a subset remain sound for the full formula. The
   oracle incurs **no discovery cost** in these figures and is *not* an
   implemented scalable selection policy. It is an optimistic yardstick.

Counts are RUP(⊕) **clause scans**, including failed checks, but they do
not count pairwise-consensus or Gaussian-construction CPU work. The
microbenchmark below measures those extra costs with elapsed time,
but still does not measure SAT search, propagation in a production
solver, proof serialization, or memory/cache pressure.

## Experiment A: legitimate shared reuse

Four guarded parity edges (8 original XNF clauses) imply `x⊕y=1`.
Multiple distinct targets use that same parity core and distinct fresh
`a_j`. Four independently proved unit lemmas can be reused. Every cut
has three certified rank-two strengthenings; no target passes RUP(⊕)
directly without the staged lemmas.

| Number of targets | Certified strengthenings | Repeated global scans | Global cached scans | Scans saved by sharing |
| ---: | ---: | ---: | ---: | ---: |
| 1 | 3 | 56 | 56 | 0 |
| 2 | 6 | 112 | 92 | 20 |
| 4 | 12 | 224 | 164 | 60 |
| 8 | 24 | 448 | 308 | 140 |

The saved scans are precisely `(targets−1) × 20` because lemma
certification costs 20 scans once. This amortization identity is not a
new scientific theorem, and it says nothing by itself about solver gain.

## Experiment B: disjoint components defeat an indiscriminate cache

Each target has its **own** 3-edge guarded parity component and no
shared useful lemmas. Nevertheless the global-cache procedure scans
all components' input and lemma clauses during verification. The
privileged relevance oracle considers each independent component alone.

| Independent targets | Certified strengthenings | Global cached scans | Component-scoped scans | Extra global scans |
| ---: | ---: | ---: | ---: | ---: |
| 2 | 6 | 141 | 78 | 63 |
| 3 | 9 | 306 | 117 | 189 |
| 4 | 12 | 534 | 156 | 378 |
| 5 | 15 | 825 | 195 | 630 |

This is a **counterexample to an unconditional caching policy** on the
tested proof-replay implementation. Discovering disconnected components
is a well-known and relatively easy preprocessing task; the comparison
does not claim that production solvers cannot perform it.

## Experiment C: connected but irrelevant parity leaves

Return to four target cuts sharing the 4-edge useful path. Add guarded
unit parity equations `x⊕wi=0` for otherwise unconstrained leaves `wi`.
These lemmas are syntactically *connected to x*, so simple variable
connectivity alone does not eliminate them. They do not change the
three certified hyperplanes per target.

| Irrelevant leaf equations | Verified unit lemmas retained | Certified strengthenings | Global cached scans | Privileged path-only scans |
| ---: | ---: | ---: | ---: | ---: |
| 0 | 4 | 12 | 164 | 224 |
| 2 | 6 | 12 | 258 | 224 |
| 4 | 8 | 12 | 360 | 224 |
| 8 | 12 | 12 | 588 | 224 |

At 8 leaves, global caching performs **364 extra** verifier scans
versus the path-only proof, yet certifies zero additional candidates.
This tests connected noise, not just disconnected components. The
path-only comparator already knows the useful path, so its selection
cost is not represented.

## Actual diagnostic Rust elapsed times (not SAT solver runtime)

One local `cargo run --release` measured the median of seven batches,
25 full proof-pipeline executions per batch, after four warmups.
Numbers in microseconds per pipeline execution; operating-system and
CPU noise apply and independent hardware replication is still needed.

| Scenario | Global cached | Repeated global | Privileged relevance |
| --- | ---: | ---: | ---: |
| Shared 4-edge core, 8 cuts | 83.6 µs | 193.0 µs | 193.5 µs |
| Five independent 3-edge components | 694.4 µs | 2378.0 µs | 170.3 µs |
| Four cuts, 8 connected irrelevant leaves | 382.7 µs | 985.8 µs | 121.2 µs |

The timing excludes the expensive diagnostic exact oracle and tests,
but includes candidate generation, proof-reason pairing, and repeated
RUP replay of the selected policy. It is reproducible in the Rust
binary and measures *this prototype only*. Even the favorable case
does **not** imply improved SAT solver wall time because the no-
minimization baseline has **zero minimization overhead**, and the
downstream search benefit has not been measured.

## Falsification gates passed / failed

- All nominated subspaces are within the bounded exact hyperplane oracle.
- All nominations are independently verified by RUP(⊕); every tested
  target has exactly three verified, among seven oracle hyperplanes.
- The no-lemma direct RUP check certifies zero targets in these families.
- All three independently executed pipelines match the reported scan
  totals on representative instances.
- **Rejected:** indiscriminate global lemma caching is a uniformly
  favorable policy. Both disjoint and connected-noise cases lose.
- **Not established:** novel reusable parity structure beyond known
  factoring/inprocessing; proof benefit in a real CDCL search, or a
  predictor that chooses useful lemmas without privileged relevance.

## Research decision / WU-008 target

The relevant unknown is *selection under uncertainty*: can an
inexpensive, sound, gauge-invariant estimator forecast a lemma's future
usefulness across **unseen** conflicts well enough to beat (a) no
minimization, (b) eager caching, and (c) existing factoring/vivification
approaches? The next milestone should train/evaluate on separated
generators and then integrate with actual solver events and wall time.
Do not call a reduction in proof-checker scans a solver speedup.

## Reproduction

```sh
cd rust/witnora-ve
cargo test --release --bin wu007_lemma_amortization
cargo run --release --quiet --bin wu007_lemma_amortization
cargo test --release --all-targets --quiet
```

WU-007 changes WU-006's helper function visibility only so that the
new diagnostic imports the exact same independently validated subspace
and RUP implementation. The substantive experiment lives in the new
Rust binary. These local microbenchmarks are not intended to compare
against Xorcle or CaDiCaL; only a future solver-integrated study can.
