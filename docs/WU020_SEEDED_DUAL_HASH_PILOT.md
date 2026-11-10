# WU-020 — seeded non-coordinate duals recover sparse coverage, not yet solve time

**Status: pilot implementation, mathematical tests, local native screening,
and one independent native UNSAT proof pair complete.** This is a
distribution-specific engineering experiment stacked on WU-019, **not**
a new random-hashing theorem, general SAT runtime result or P=NP claim.

## The unknown being tested

WU-019 found that four coordinate duals certify roughly 79% of candidate
watch inspections on dense wide random formulas, but just 0.8–6.1% on sparse
wide random formulas. Those sparse tests all timed out, so this was a
coverage observation only.

**Question:** Can four other linear measurements of the same quotient
space recover safe skip coverage on sparse inputs, and does the additional
mask-building work pay off in actual solver time?

Our comparison uses the *same* Xorcle solver source, test corpus and
search counters as WU-019. Relevant prior research is Beame–Sun's original
Xorcle and LRUP(⊕) formalism (<https://doi.org/10.4230/LIPIcs.SAT.2026.5>),
Laitinen–Junttila–Niemelä's complete parity reasoning
(<https://arxiv.org/abs/1207.0988>) and Carter–Wegman's universal hashing
(<https://research.ibm.com/publications/universal-classes-of-hash-functions--1>).
Random linear maps and their basic probability properties are *established
mathematics*; no novelty is claimed for them.

## Exact method and mathematical safety

In the WU-019 multiword gate, replace four *coordinate* free-column masks
with four **seeded non-coordinate masks**. For each nonpivot column `j`,
calculate the lower four bits of a fixed SplitMix64-style mix of
`j + 0x9e3779b97f4a7c15`. Set that column in mask `d_k` if bit `k` is 1.
Then perform the **same** reverse-pivot back substitution as WU-019, so
every mask annihilates the trail span `U` exactly.

For any watched parity equation `a`, its four-bit signature
`H(a)=(a·d_0,...,a·d_3)` is identical to applying the selected linear
hash to its quotient class `[a]` modulo `U`. In particular,

- if `H(a)` and `H(b)` are both nonzero and different, `[a]` and `[b]`
  are independent over GF(2) and the original no-hint watch check is
  unnecessary;
- otherwise, execute Xorcle's published propagator unchanged.

There are **no false-positive skips** from hash collisions: a collision
causes only a missed opportunity to skip. Each trail change invalidates
all four masks, as in WU-019. The seeded mapping is fixed per column and
independent of the watched equations; it is **not** adaptive learning.

For a truly uniform random linear map from a vector space with dimension
at least two into `GF(2)^4`, two fixed independent inputs have independent
uniform four-bit outputs. Hence the probability that both outputs are
nonzero and unequal is `(15/16)*(14/16) = 210/256 ≈ 82.03%`.
**This does not provide a probability guarantee for our fixed,
pseudorandom SplitMix-style column map.** Its coverage must be measured.

## Reproducibility and verification

- Pinned untouched Xorcle commit:
  `af93ea646a4237958e9925bc684dcd545e68de30`.
- Build the WU-018, WU-019, then
  `research_patches/wu020_seeded_noncoordinate_duals.patch` incremental
  patch in that order, with the same `-O3 -DNDEBUG -std=c++23` options.
  The last patch applies with `patch -p1` to the full original-style
  `src/...` layout and passed a local dry run. The untouched native
  baseline and WU-019 coordinate binaries are separate.
- Independent Rust test:
  `rust/witnora-ve/src/bin/wu020_seeded_dual_certificate.rs`, including
  random echelon trails and backtrack/extend cases at widths 1–257,
  checking that dual signatures match an independently reduced quotient;
  plus a sparse-pair coverage sanity test. Two tests passed locally.
- Reuse the **preexisting** WU-019 12-instance corpus with base seed
  `910019` and unchanged original manifest; no post-hoc instance
  selection. Sparse/dense genuinely wide planted families use all
  independent variables with no unary tying equations. Bench scripts:
  `scripts/wu019_benchmark_wide.py` and
  `scripts/wu019_check_native_proofs.py`.
- Every **completed** coordinate/seeded pair had identical six native
  solver search counters, and SAT assignments were independently checked
  against the XNF formula. UNSAT claims are reserved for independent
  LRUP(⊕) proof checking.

## Main observation: sparse random coverage restored

All dense and sparse genuinely wide random trials **timed out** at the
same per-process budget (3 seconds at width 80, 2 seconds at widths 129
and 192). These are diagnostic snapshots of the last *complete million*
inspections, **not** normalized throughput or solved-runtime comparisons.

| Width | Dense coordinate | Dense seeded | Sparse coordinate | Sparse seeded |
| ---: | ---: | ---: | ---: | ---: |
| 80 | 78.8% | 79.8% | 5.7% | **78.5%** |
| 129 | 78.6% | 79.6% | 6.1% | **77.1%** |
| 192 | 79.0% | 80.3% | 0.8% | **75.1%** |

The fixed four-coordinate projection misses nearly every wide sparse
support at width 192; four seeded full-span duals can identify most of
the same potentially unnecessary inspections. This is the **actual
empirical gain**. These figures are from **one** generated formula per
width/family and **one** fixed hash seed; they are not confidence
intervals or distributional guarantees.

## Completed solve-time control: benefit is unresolved

For embedded formulas with a 22-variable hard core, compaction disabled,
we compared the **WU-019 coordinate binary directly to WU-020 seeded**.
Rows are one paired run each and all published search counters agreed.

| Width / family | Coordinate | Seeded | Seeded vs coordinate |
| --- | ---: | ---: | ---: |
| 80 / unplanted UNSAT | 2.208 s | 2.881 s | slower |
| 129 / unplanted UNSAT | 3.798 s | 3.940 s | slower |
| 192 / unplanted UNSAT | 6.103 s | 6.148 s | near equal |
| 80 / planted SAT | 0.086 s | 0.073 s | faster, very short run |
| 129 / planted SAT | 0.228 s | 0.241 s | slower, very short run |
| 192 / planted SAT | 3.641 s | 3.661 s | near equal |

**Important timing variability:** Three additional n=80 unplanted pairs
with order alternation gave coordinate/seeded seconds of
`2.500/2.076`, `2.186/2.046`, and `2.064/2.598`. These disagree
about the direction of the timing effect. Do **not** claim that seeded
masks are either faster or slower without longer controlled replicates.
The extra free-column initialization and denser back-substitution may
cost enough to cancel the higher skip coverage. Sampled memory values
are lower bounds, not a peak-memory audit.

## Native proof-preservation control

On the 80-variable embedded-unplanted case, the WU-019 coordinate binary
and WU-020 seeded binary each produced an LRUP(⊕) proof that was
independently accepted by **untouched** Xorcle's
`tools/check_lrup_parity.py`:

- Both emitted **833,665-byte proofs** with identical SHA256
  `7a5cc7d99856354bc5fb13c64660687160bea0a6db178ca5c9b049ddda66f17e`.
- All six published search counters matched exactly.
- One paired proof-mode timing was 2.506 s (coordinate) and 2.034 s
  (seeded); this isolated timing is **not** a speedup claim, given the
  contradictory no-proof repeats above.

The independent checker and mathematical signature tests support
soundness in tested states; they are not formal verification of all
possible C++ solver paths.

## Next falsifiable experiment

Test a **hybrid gate** that first uses cheap coordinate bits, and
evaluates seeded full-span duals only where the coordinate certificates
fail *and* the observed reduction cost justifies it. Predefine a
selection rule before seeing outcomes; run several hash seeds and
independent held-out formulas; measure completed wall-clock plus
independent proofs under matching solver settings. If the extra
evaluation, initialization or memory cost erases the savings, record
that as a negative result rather than optimizing for skip percentage.
