# WU-019 — multiword dual certificates in native Xorcle

**Status: experimental implementation and local replication complete.**
This extends the working WU-018 four-dual-mask gate from one 64-bit packed word
to arbitrary positive numbers of 64-bit words. It is an implementation result,
**not** a new SAT algorithmic complexity bound, general-speed claim, or
P-versus-NP result. The cross-width positive results are from low-dimensional
relational embeddings; the genuinely wide random cases **did not complete**.

## Research question and prior art

Can direct dual-vector dot products certify that two watched parity equations
remain independent modulo a changing trail, without executing the solver's
ordinary GF(2) reduction, even when the active equation width exceeds one
machine word? Does that help on genuinely wide interactions, as opposed to
merely padding a small hard core?

The algebra is elementary and **not claimed as novel**. Relevant established
research includes Laitinen, Junttila, Niemela, *Extending Clause Learning SAT
Solvers with Complete Parity Reasoning* (2012),
<https://arxiv.org/abs/1207.0988>, and Beame–Sun, *Extending CDCL to
Disjunctions of Parity Equations*, SAT 2026 (original Xorcle solver and its
LRUP(⊕) proof system), <https://doi.org/10.4230/LIPIcs.SAT.2026.5>.
WU-017 measured a quotient-signature oracle; WU-018 tested a real single-word
fast path. WU-019 measures the extra **multiword** work and its limitations.

## Exact certificate and safe fallback

Let `U` denote the span of current trail equations over GF(2), **including the
affine RHS/constant column**. Choose at most four distinct nonpivot columns
of the current echelon trail basis. For each such column `j`, create a dense
multiword dual vector `d_j` initially equal to the coordinate vector `e_j`.
Visit the trail rows in reverse pivot order and toggle each row's pivot bit
of `d_j` whenever the row–dual dot product is odd. Consequently,
`u · d_j = 0` for every `u` in `U` and the nonpivot coordinates of `d_j`
remain those of `e_j`.

For watched equations `a` and `b`, compute four-bit signatures
`s(a) = (a·d_j)_j` and `s(b) = (b·d_j)_j` by XOR-accumulating the parity of
64-bit popcounts across all packed words. If both signatures are nonzero and
unequal, their images in `GF(2)^4` are independent, so their original
quotient classes modulo `U` are independent. The no-trigger-hint watch
inspection cannot propagate or replace a watch and can be skipped **exactly**.
All other cases execute the original published propagation logic unchanged.

The dual basis is rebuilt only on first use after a trail mutation; its
lifetime is one `propagate_until_conflict` invocation, so it cannot survive
restarts, backtracking or compaction. The implementation uses the old
one-word path at <=64 columns and a vector of packed words beyond that.
All counters are diagnostic only. Only the native published UNSAT proof
emission and an independent checker are treated as UNSAT verification.

## Pinned implementation and independent controls

- Upstream **untouched Xorcle** commit:
  `af93ea646a4237958e9925bc684dcd545e68de30`; pinned GF2 dependency:
  `0b09e44fd2c6615a6a1958c480650e207703b84c`.
- Experimental build: apply
  `research_patches/wu018_four_dual_masks_propagator.patch`, then
  `research_patches/wu019_multiword_dual_mask_extension.patch` to an
  **independent** Xorcle source copy. Both baseline and modified binaries
  were built with the same optimized `g++ -O3 -DNDEBUG -std=c++23` flags.
- Rust certificate tests in
  `rust/witnora-ve/src/bin/wu019_wide_dual_certificate.rs` checked sizes
  1, 32, 63, 64, 65, 80, 129, 192, 257, random echelon trails, dual
  annihilation, signature equivalence to independent elimination and trail
  extension/backtracking. This is mathematical testing, not a proof of
  implementation-wide correctness.
- Native paired trials alternate baseline/experimental order and compare
  all six published solver search counters whenever **both** runs finish;
  every returned SAT assignment is checked against every source XNF clause.
  The UNSAT proof runs use untouched upstream `tools/check_lrup_parity.py`.
- The local 12-formula holdout corpus is reproducible from
  `wu019_generate_wide_xnf OUT_DIR 910019`; see
  `research_data/wu019/manifest.tsv`, SHA256
  `b3f123e41fe605c831a89cb3534ce062241eb125936d16911eb535566d36d909`.
  The generator contains a test for planted witnesses.
- All primary trials specify `--compact=false`, preserving the genuinely
  wide active representation. An additional **default-compaction** control
  is reported separately.

## Completed no-proof wall-clock pairs, compaction disabled

Times below are a single machine's paired runs, in seconds. All six
published search counters agree exactly across each completed pair.

| Width | Family | Selector | Baseline | Wide dual | Speedup |
| ---: | --- | --- | ---: | ---: | ---: |
| 80 | embedded unplanted | cyclic | 4.506 | 2.045 | 2.20× |
| 129 | embedded unplanted | cyclic | 6.426 | 2.815 | 2.28× |
| 192 | embedded unplanted | cyclic | 11.247 | 4.485 | 2.51× |
| 80 | embedded planted | cyclic | 0.106 | 0.076 | 1.39× |
| 129 | embedded planted | cyclic | 0.249 | 0.160 | 1.55× |
| 192 | embedded planted | cyclic | 5.830 | 2.545 | 2.29× |
| 80 | embedded unplanted | leading-term watchlist | 3.664 | 2.338 | 1.57× |
| 129 | embedded unplanted | leading-term watchlist | 3.499 | 2.484 | 1.41× |
| 192 | embedded unplanted | leading-term watchlist | 4.092 | 3.016 | 1.36× |

An n=80 repeat with the same seed and cyclic selector produced 4.499 versus
2.048 seconds on unplanted formulas (2.20×), and 0.110 versus 0.082 seconds
on planted formulas (1.35×). The sample is too small for variance or
statistical confidence claims. Sampled RSS lower-bound readings at width
192 unplanted cyclic were 6596 KiB (baseline) and 6608 KiB (wide); this is
**not** a complete peak-memory measurement.

**Critical limitation:** An `embedded_*` formula has only a **22-variable
hard core**. The additional variables occur throughout the XNF but are tied
by unary parity relations to that core. Thus the table establishes correct
multiword execution and speed on a particular **low-intrinsic-dimension**
family. It does not show solving arbitrary hard 192-variable instances.

## Certified native UNSAT controls (compaction disabled)

Both baseline and experimental solver emitted independently accepted
LRUP(⊕) proofs. In **all four** pairs, the proof files had identical SHA256
hashes *and* lengths, and all six search counters matched exactly.

| Width / selector | Baseline solve + verify | Wide solve + verify | End-to-end ratio |
| --- | ---: | ---: | ---: |
| 80 / cyclic | 4.584 + 0.325 s | 2.188 + 0.310 s | 1.97× |
| 129 / cyclic | 6.672 + 0.330 s | 2.896 + 0.323 s | 2.18× |
| 192 / cyclic | 11.444 + 0.341 s | 4.735 + 0.342 s | 2.32× |
| 80 / leading-term watchlist | 3.706 + 0.350 s | 2.274 + 0.391 s | 1.52× |

CSV files `wu019_proofs*.csv` record actual proof hashes, bytes, timings
and counters; do not merge checker time into solver-only benchmark claims.

## Falsification: genuinely wide random interactions

`dense_planted` and `sparse_planted` use **all n independent variables**
with 3n binary clauses and a known planted solution. The dense variant
chooses each parity support at random; the sparse variant uses four
variables per parity support. There are no unary relations hiding a
small-dimensional core.

At widths 80, 129 and 192, **all twelve baseline/wide trials timed out**
(2–3-second per-process limits). No solved-runtime or soundness comparison
can be inferred from these censored runs. Experimental diagnostic snapshots
showed approximate skipped/eligible fractions:

| Width | Dense random | Sparse random |
| ---: | ---: | ---: |
| 80 | 78.8% | 5.7% |
| 129 | 78.6% | 6.1% |
| 192 | 79.0% | 0.8% |

These are *within-run activity observations*, not normalized throughput,
speedup, solution results or proof results. In particular, selecting only
the first four **coordinate** duals performs poorly on sparse formulas:
most watched equations have zero projected signature. This is a concrete
negative result and a target for WU-020, not a reason to claim success on
the random families.

## The default-compaction control: separate attribution

With original Xorcle compaction **enabled**, the same embedded formulas
finished in the following paired timings. The wide version inherits both
the WU-018 one-word gate and the WU-019 multiword extension, so the observed
speedup versus untouched Xorcle **cannot be attributed solely to WU-019**.

| Width | Family | Baseline | WU-018+019 | Ratio | Multiword eligible / all eligible |
| ---: | --- | ---: | ---: | ---: | ---: |
| 80 | embedded unplanted | 1.386 s | 0.967 s | 1.43× | 132 / 5,517,299 |
| 129 | embedded unplanted | 1.491 s | 0.888 s | 1.68× | 132 / 5,316,775 |
| 192 | embedded unplanted | 1.408 s | 0.818 s | 1.72× | 132 / 5,437,652 |
| 80 | embedded planted | 0.216 s | 0.133 s | 1.62× | 132 / 743,512 |
| 129 | embedded planted | 0.064 s | 0.057 s | 1.12× | 132 / 208,827 |
| 192 | embedded planted | 0.679 s | 0.427 s | 1.59× | 132 / 2,618,901 |

Compaction eliminates most high-dimensional representation cost on this
family. Consequently, future multiword results must hold active width
constant or use inputs that naturally remain wide, and compare explicitly
against **WU-018-only** to isolate the incremental WU-019 contribution.

## Reproduction and next unknown

With a pinned native Xorcle baseline and patch-built experimental binary
available, generate the 12 holdouts with the Rust generator and run:

```bash
cargo run --release --manifest-path rust/witnora-ve/Cargo.toml \
  --bin wu019_generate_wide_xnf -- /tmp/wu019-holdout 910019

python3 -m unittest -v scripts.test_wu019_benchmark_wide

python3 -m scripts.wu019_benchmark_wide \
  --instances /tmp/wu019-holdout \
  --baseline /path/to/untouched/xorcle \
  --wide /path/to/patch-built/xorcle \
  --results /tmp/wu019-results.csv --timeout 15 \
  --family embedded_unplanted,embedded_planted

python3 -m scripts.wu019_check_native_proofs \
  --instances /tmp/wu019-holdout \
  --baseline /path/to/untouched/xorcle \
  --wide /path/to/patch-built/xorcle \
  --checker /path/to/untouched/tools/check_lrup_parity.py \
  --scratch /tmp/wu019-proofs --results /tmp/wu019-proofs.csv \
  --width 80 --timeout 35
```

**Next falsifiable frontier question (WU-020):** Can a small collection of
*non-coordinate*, trail-annihilating random or adaptively selected duals
retain the exact gate certificate while covering sparse wide watched
equations, **including the costs of generating and evaluating those duals**?
Compare coordinate-only, randomized four-dual, and the untouched baseline;
measure complete solve time and independent proof checks. If the extra
mask cost overwhelms saved row reductions, record a negative result.
