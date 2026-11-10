# WU-021 — selective sparse-dual fallback: proof-safe, not faster

**Status:** native C++ pilot compiled; independent Rust soundness of both
constituent dual gates inherited from WU-019 and WU-020; Python profiler
tests passed; native solver search counters and SAT assignments checked;
two independently checked identical UNSAT proof pairs. **This pilot is a
negative performance result on its chosen sparse holdout.**

## The unknown and the predeclared hybrid rule

WU-020's seeded non-coordinate masks recovered 75–79% of unnecessary
watch inspections on sparse wide random XNF but did not establish a
completed-runtime advantage; rebuilding full masks across changing
trail spans might erase the gain. Can we avoid building that extra
dual state unless the clause looks sparse and the cheap coordinate
certificate has failed?

We froze the following rule **before generating or benchmarking the
WU-021 holdout**:

1. For active equations wider than one 64-bit word, build and try
   WU-019's four coordinate duals first.
2. On a coordinate miss, compute each watched equation's raw popcount
   over all packed words, **including the affine constant bit**.
3. If **both** weights are at most **8**, lazily build WU-020's four
   seeded full-span duals for the current trail and test them. Otherwise
   fall through to the published Xorcle propagator immediately.
4. Invalidate *both* dual caches on the same trail mutation boundary.
   Neither cache survives compaction, restarts or backjumps.

This is a deliberately simple **structural** trigger, not a learned
policy, trained threshold, or post-hoc parameter search. The original
single-word gate remains unchanged. The extra seeded dual can only
skip if its two four-bit signatures are nonzero and distinct; it therefore
preserves exactly the quotient-independence certificate of WU-020.
Combining two individually sufficient certificates with logical OR
cannot create an unsafe skip. A missed certificate always calls the
untouched published propagator.

Foundational research is Beame–Sun's *Extending CDCL to Disjunctions
of Parity Equations*, SAT 2026, including Xorcle and LRUP(⊕),
<https://doi.org/10.4230/LIPIcs.SAT.2026.5>;
Laitinen–Junttila–Niemelä's complete parity reasoning,
<https://arxiv.org/abs/1207.0988>. Elementary dual linear algebra and
random linear hashing are **not** claimed to be new mathematics here.

## Source and independent controls

- Untouched pinned Xorcle source
  `af93ea646a4237958e9925bc684dcd545e68de30`; unchanged GF2
  dependency `0b09e44fd2c6615a6a1958c480650e207703b84c`.
- Reproducible sequence of **separate** experimental source patches:
  WU-018 one-word, WU-019 multiword, WU-020 seeded full-span, followed by
  `research_patches/wu021_lazy_sparse_dual_fallback.patch`. The last
  incremental patch passed a native dry run on the exact WU-020 source.
  All native builds used the same optimized `-O3 -DNDEBUG -std=c++23`.
- New unchanged generator, **fresh base seed 910021** *after rule freeze*,
  with widths 80, 129, 192 and four families. Stored manifest
  `research_data/wu021/manifest.tsv`; SHA256
  `a563e5e8650dd4aae8deffc2320b3ce1b4572e12aa34dbf78463b05eae85937a`.
  Generate with `wu019_generate_wide_xnf OUT_DIR 910021`.
- Pilot wrapper `scripts/wu021_benchmark_hybrid.py` reuses WU-019's
  strict XNF parser, independent planted-witness and returned SAT-model
  checker, six-search-counter paired comparisons, and right-censoring.
  Added counters for seeded fallback invocations, successful fallback
  skips, lazy rebuilds, and seeded row-word operations. Missing or
  corrupted diagnostic fields fail closed; see
  `scripts/test_wu021_benchmark_hybrid.py`.
- Primary tests use **`--compact=false`** to preserve wide active
  dimension. Benchmarks alternate implementation execution order.
  Saved sampled RSS is merely a lower bound, not a memory-peak audit.
- The prior WU-019 and WU-020 Rust mathematical certificate tests
  independently verify the two constituent maps across widths, trail
  extensions/backtracking and full quotient reduction. These and the
  native proof checks do **not** formally verify every C++ execution path.

## Fresh random holdout: denser watch traffic defeats the heuristic

All paired runs on the fully wide random planted formulas **timed out**
at 2-second per-process limits. The following are *last complete-million
diagnostic snapshots*, **not** solved-runtime or average-throughput
estimates. Do not compare snapshot numerators as though both programs
had stopped at the same search state.

| Width | Sparse coordinate | Sparse always seeded | Sparse hybrid |
| ---: | ---: | ---: | ---: |
| 80 | 33.5% | 79.5% | 46.0% |
| 129 | 0.3% | 77.8% | 40.4% |
| 192 | 0.6% | 74.8% | 48.8% |

The fresh n=80 coordinate-only rate (33.5%) differs substantially from
WU-020's prior seed (5.7%); this warns against extrapolating from one
synthetic formula per width. Always-seeded coverage stays high, but
the structurally gated hybrid discards much of it.

For all three **dense random** formulas, the hybrid behaved as intended:
there were **zero** seeded fallback checks or rebuilds in the observed
snapshots, and the coordinate skip fraction remained approximately 79%.

However, on sparse formulas the lazy path still rebuilt the extra dual
masks **16,865** times by the n=80 three-million-attempt snapshot,
**8,990** times by n=129 one-million-attempt snapshot, and **7,046**
times by n=192 one-million-attempt snapshot. At n=192 it performed
20,275,088 extra seeded row-word tests on top of 22,021,232 coordinate
row-word tests in that snapshot. The combined construction work is not
actually rare on a sparse distribution.

The last-complete-million *attempts* snapshots within 2 seconds were:

| Width | Coordinate | Always seeded | Hybrid |
| ---: | ---: | ---: | ---: |
| 80 | 3 million | 6 million | 3 million |
| 129 | 1 million | 4 million | 1 million |
| 192 | 1 million | 2 million | 1 million |

This indicates no observed throughput gain over coordinate-only and
considerably less observed activity than always-seeded on the chosen
random sparse holdout. The snapshot sampling interval is coarse,
different solvers may reach different partial states, and none solved:
**do not interpret these numbers as exact throughput ratios or overall
solver speedup measurements.**

## Completed embedded controls: no reliable full-solve improvement

The independent fresh *embedded* families contain a 22-variable hard
core tied across 80–192 variable columns. All six coordinate/hybrid
paired runs **finished** with the same SAT/UNSAT status, exactly equal
native six search counters, and independently validated SAT assignments.
Wall-clock timings (seconds):

| Width / result | Coordinate | Hybrid |
| --- | ---: | ---: |
| 80 / UNSAT | 2.280 | 2.237 |
| 129 / UNSAT | 2.822 | 2.886 |
| 192 / UNSAT | 4.780 | 4.817 |
| 80 / planted SAT | 0.412 | 0.398 |
| 129 / planted SAT | 2.020 | 2.105 |
| 192 / planted SAT | 0.094 | 0.092 |

These are very small samples. All improvements/regressions are near the
scale of ordinary timing noise, and this test family has **low intrinsic
dimension**. There is **no reliable measured end-to-end speedup** here.
Three additional order-alternating n=80 UNSAT repetitions recorded
coordinate/hybrid times `2.115/2.272`, `2.225/2.454`, and
`2.633/2.274` seconds. They reverse the apparent winner across runs,
reinforcing that the small completed-time differences above are noisy.

## Native UNSAT proof checks

Both baseline coordinate and hybrid produced independent checker-accepted
LRUP(⊕) proof files on the fresh embedded-unplanted **n=80** and
**n=192** inputs. Within each pair, all search counters, proof lengths,
and SHA256 hashes matched exactly:

- n=80: 862,748 bytes; SHA256
  `62081d393201903f46a48571814cc00012e21f04cd483bb9d77f1836351c736b`.
- n=192: 1,031,442 bytes; SHA256
  `f9c6f38d5bbb8d522821dc95228ac9eba6e256219d45ecfb57aed437b29c1029`.

Both proofs were independently checked with unmodified upstream
`tools/check_lrup_parity.py`. As before, proof checker time is recorded
separately from solver time. The exact results reside in
`research_data/wu021/wu021_proofs*.csv`.

## Conclusion and next unknown

**Do not promote the sparse popcount≤8 lazy fallback as a performance
improvement.** It remains proof-safe on tested cases, but the heuristic
misses many seeded certificates while still rebuilding the costly
full-span seeded masks frequently. It has not improved solved runtime
or random-censored diagnostic throughput.

Next research question: can the four seeded duals be **updated
incrementally** as the trail span changes, instead of paying the
full O(rank × word_count × 4) reconstruction on each new span?
Specify correctness under row insertion, backtrack, restarts and
compaction, and count actual operations as well as completed
proof-checked runtime before calling it a gain. This is an algorithmic
engineering hypothesis, not a claim of novel complexity theory.
