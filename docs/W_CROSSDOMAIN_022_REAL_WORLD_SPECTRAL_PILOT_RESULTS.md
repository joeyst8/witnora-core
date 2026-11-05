# W-CROSSDOMAIN-022: real-world spectral pilot, independent Rust controls

Protocol: `docs/W_CROSSDOMAIN_022_REAL_WORLD_SPECTRAL_PILOT_PROTOCOL.md`.
Raw measurements, source SHA-256 fingerprints and publisher labels:
`research/results/w022_external_vlsat2.json`.

## Verification and provenance

- **Dedicated GitHub Actions run: passed**
  [42123416642](https://github.com/joeyst8/witnora-core/actions/runs/42123416642).
- Rust release build and Rust unit tests passed; separate Python matrix
  arithmetic controls (three nontrivial cases plus empty source) passed.
- All eight frozen VLSAT-2 files downloaded from their publisher,
  decompressed, were checked independently for source dimensions and
  literal universes, and were processed by the Rust profiler.
- Kissat upstream release `rel-4.0.4` built from Git commit
  `8af8e56f174b778aef3aa45af9f739b2a5f492c2`.
- Kissat returned three UNSAT decisions matching INRIA's published
  labels, and five censored TIMEOUTs. It returned no contrary decision.
  **We have not independently checked UNSAT proof artifacts.**
- GitHub's first attempt `42123108557` failed because the independent
  parser assumed ASCII comments, while real VLSAT-2 metadata contains
  UTF-8. The frozen sample was unchanged; a UTF-8 decoding fix and rerun
  yielded the successful final workflow.

## Complete observed cases

All times measured on the same GitHub Linux runner. Rust feature time is
one pass of parse plus fixed-eight-iteration spectral profiling, excluding
disk input read and JSON rendering. Kissat time is wall clock, with a
**15-second right-censoring cap**; a timeout is not evidence of SAT or
UNSAT. Neither code path receives its counterpart's result.

| VLSAT-2 name | Publisher label | Kissat result | Kissat (s) | Rust profiler (ms) | Rayleigh score | Polarity conflict |
| --- | --- | --- | ---: | ---: | ---: | ---: |
| 544_8738 | UNSAT | TIMEOUT | >15 | 1.663 | 0.9999988874 | 0.047555 |
| 600_11440 | UNSAT | TIMEOUT | >15 | 2.038 | 0.9999995210 | 0.042498 |
| 684_9417 | UNSAT | UNSAT | 0.727 | 1.746 | 0.9999857323 | 0.063916 |
| 684_13953 | UNSAT | UNSAT | 0.835 | 2.502 | 0.9999998322 | 0.043506 |
| 708_10259 | UNSAT | UNSAT | 0.598 | 1.853 | 0.9999859394 | 0.061021 |
| 736_11022 | UNSAT | TIMEOUT | >15 | 2.011 | 0.9999991872 | 0.054591 |
| 1000_22250 | SAT | TIMEOUT | >15 | 3.985 | 0.9999996537 | 0.035833 |
| 3456_192912 | SAT | TIMEOUT | >15 | 35.832 | 0.9999999945 | 0.016362 |

## Important mathematical explanation: the trivial leading mode

Write the signed incidence matrix using one edge for each literal
occurrence:

`B[c,v] = sum_{e=(c,v)} sign(e) / sqrt(length(c)*degree(v))`.

For any real x, Cauchy-Schwarz bounds the row energy:

`(Bx)[c]^2 <= sum_{e=(c,v)} x[v]^2 / degree(v)`.

Summing over clauses counts each variable exactly `degree(v)` times,
so `||Bx||_2^2 <= ||x||_2^2`. Thus every eigenvalue of `B^T B` is
in `[0,1]`.

If every occurrence of each variable has one consistent polarity,
choose `x[v] = sign(v)*sqrt(degree(v)/E)` where E is the total number
of literal occurrences. Each clause then has
`(Bx)[c]=sqrt(length(c)/E)`, so `||Bx||_2=||x||_2=1`.
Consequently, **the top eigenvalue is exactly 1** in this perfectly
sign-consistent case. This is an elementary property of normalized
signed incidence matrices, **not a newly discovered theorem**.

Our external inputs have low but nonzero polarity conflict fractions
of 1.6%--6.4%, plausibly leaving the top mode very close to this
trivial upper bound. This offers a concrete mathematical explanation
for the observed score range 0.99998573--0.99999999; it is a
**hypothesis about why these examples saturate**, not a proved
quantitative stability result.

## What the measurements do and do not support

1. The Rust linear-time-style diagnostic is cheap even on CNFs with
   hundreds of thousands of clauses (1.7--35.8 ms on this runner).
2. The top Rayleigh score is numerically saturated on this family and
   is not useful by itself for discriminating easy from hard cases.
3. This runner does **not** compare an improved SAT solver against
   Kissat. It compares standalone feature overhead with bare Kissat.
   Merely adding profiling before Kissat would make end-to-end time
   worse; no acceleration has been demonstrated.
4. Eight non-random inputs (six UNSAT, two SAT) and five censored
   solve times cannot identify a reliable hardness-prediction effect.
   The sample also confounds size, satisfiability, and family structure.

## Actionable W-023 research direction

Test **deflation of the near-trivial polarity/gauge mode**, signed
frustration localization, and the *spectral gap* on size-matched held-out
datasets. Predeclare hypotheses and compare predictive value against
simple features such as clause count and polarity conflict. Ensure any
future solver-guidance experiment measures complete end-to-end cost
against pinned Kissat, and preserves correctness independently.

W-022 gives no proof about P versus NP and no new complexity theorem.
