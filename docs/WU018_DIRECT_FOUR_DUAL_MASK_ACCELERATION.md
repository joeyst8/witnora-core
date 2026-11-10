# WU-018 — direct dual-mask tests accelerate Xorcle on a held-out native 2-XNF family

**Status:** real 64-bit experimental Xorcle fast path compiled and benchmarked;
64 paired complete no-proof runs checked; 16 independent LRUP(⊕) proof checks
accepted; fresh held-out replication passed. **Distribution-specific engineering
result, not a general-purpose SAT result or a new complexity theorem.**

## Motivation and the crucial difference from WU-017

WU-017 measured the *possibility* of certifying 78–80% of eligible watches
with four canonical quotient bits, but calculated each sampled quotient
by **fully reducing** a copied watched equation. That oracle could not make
the solver faster. It also suggested that refreshing cached signatures in
every clause after each trail change would be costly.

The alternative tested here is a small **current-trail dual basis**, not a
per-clause signature cache. It computes four dual masks once at the first
no-hint clause inspection after the trail changes; then each new watched
equation is checked by packed parity dot products, with no GF(2) row
reduction or per-clause cached state.

This is elementary dual linear algebra applied to the published Xorcle
propagation path. **No mathematical novelty is asserted.** Relevant prior
work: Laitinen, Junttila, Niemelä (2012), *Extending Clause Learning SAT
Solvers with Complete Parity Reasoning*, using incremental Gauss–Jordan
elimination (<https://arxiv.org/abs/1207.0988>); Beame–Sun, *Extending CDCL
to Disjunctions of Parity Equations*, SAT 2026, introducing Xorcle and
LRUP(⊕) (<https://doi.org/10.4230/LIPIcs.SAT.2026.5>).

## Exact mathematical certificate

Let `U` be the current trail span in GF(2) over all coefficient columns
**including the affine constant bit**. For the first four nonpivot columns
`j`, construct dual vectors `d_j` such that:

1. `u·d_j=0` for **every** `u` in `U`;
2. on free/nonpivot columns, `d_j` is the coordinate vector `e_j`.

For an echelon basis, construct each `d_j` by putting `1` at free column
`j`, then visiting echelon rows from largest pivot to smallest. When a row
has odd dot product with the current mask, toggle its pivot bit. This is
back substitution on the dual nullspace: the resulting vector annihilates
each trail row.

For any equation `a`, its canonical quotient remainder `r(a)` differs
from `a` by an element of `U`, and has all pivot coordinates zero. Thus
`a·d_j = r(a)·d_j = r(a)[j]` exactly. Four dot products recover exactly
WU-017's canonical 4-bit signature **without reducing `a`**.

Given two watched equations `a` and `b`, if both four-bit signatures are
nonzero and distinct, then their quotient images are independent over
GF(2); the original watch inspection with no trigger hint can produce no
propagation or watch replacement. Only then is the entire original
`unit_propagate_one_clause()` call safely skipped. All other cases fall
through to the unchanged published propagator.

The experiment applies this gate only with `dense` representation and
`active_num_vars_ < 64`, i.e. at most 64 columns including the constant.
All other variable counts and sparse representations use the original
propagator, unchanged. The four masks are **invalidated immediately after
each successful propagation**. Decisions, backjumps, restarts and
compaction each end/restart the `propagate_until_conflict()` invocation,
so they receive a new local gate. Mutating a clause watch does not stale
the mask: the mask depends only on the trail, and the current watched
rows are read on every query. No persisting cache crosses variable
renumbering, levels or proofs.

## Source and execution controls

- Pinned untouched Xorcle reference source at
  `af93ea646a4237958e9925bc684dcd545e68de30`.
- Build the C++ experiment from a **separate copy** of this source, using
  `research_patches/wu018_four_dual_masks_propagator.patch`. This changes
  `src/core/solver.cpp` and the dense GF(2) vector's one-word accessor.
  Its baseline binary and objects are never modified. The patch passes
  a dry-run against the original source.
- Compile optimised C++23 with the same `-O3 -DNDEBUG` baseline flags.
  Relink the experimental `solver.cpp.o` with the unchanged published
  objects and original `main.cpp.o`. Solver counters and SAT results
  are checked by `scripts/wu018_benchmark_dual.py`.
- Calibration: eight preexisting, independent WU-014 easy controls,
  n=21/22. **True algorithm holdout**: freshly generated eight n=21/22
  cases from the Rust generator with base seed **910018**, created after
  selecting the four-dual algorithm. Two repetitions with reversed
  baseline/experimental order, both the original cyclic selector and
  published leading-term-watchlist selector. Each easy invocation has
  a 3.5-second deadline and **all completed**.
- Additional fresh hard holdout: four n=28/29 cases from the same new
  seed base. 2.5-second budget, both selectors, paired unmodified and
  experimental runs. All were **right-censored**; their results cannot
  be interpreted as solved cases or measured whole-run speedups.
- Easy held-out manifest SHA256
  `f23b8f870db9b9957f81881aea4cc158dff23417c299813f6901e8a0b1f05749`;
  hard manifest SHA256
  `25fe3698c4a1081b50a9b115928954d54599ca2a4ca9876ccb0fb210c5d964ed`.

## Completed paired wall-clock measurements

Geometric mean speedup is `baseline wall_seconds / experimental
wall_seconds`, paired by exact formula, selector and repetition. The
reported ratios include runtime cost of constructing and invalidating
dual masks; they exclude separate proof generation/checking below. These
are short, serial, single-machine observations without randomized-run
confidence intervals or independent hardware replication.

| Corpus | Selector | Completed pairs | Geometric mean speedup | Skipped / eligible |
| --- | --- | ---: | ---: | ---: |
| Initial 8 n21/22 | cyclic | 16 | **1.507×** | 78.39% |
| Initial 8 n21/22 | leading-term watchlist | 16 | **1.385×** | 77.72% |
| New 8 n21/22 | cyclic | 16 | **1.544×** | 78.59% |
| New 8 n21/22 | leading-term watchlist | 16 | **1.384×** | 77.57% |

In **all 64 completed pairs**, SAT/UNSAT statuses and *every compared
official search counter* matched exactly: conflicts, successful and
attempted propagations, watch replacements, learned clauses and
decisions. Returned SAT models passed independent evaluation on the
original XNF. The 64-bit C++ gate is deterministic; complete-run
equivalence on this sample is not itself a general proof of soundness,
which rests on the algebraic argument above.

Average mask rebuild frequency was about `0.0058–0.0067` per attempted
propagation, or **one rebuild per ~150–173 attempted calls**. The gate
does not require an all-clause refresh. No per-clause signature cache is
maintained, so this avoids the WU-017 eager-refresh cost trap.

### Hard holdout is only a censored progress check

All four fresh n28/29 inputs timed out in both solver versions for both
selectors at 2.5 seconds. The experimental version's last complete
million-attempt snapshots show 80.94% eligible skip coverage under
cyclic, 80.01% under watchlist. The untouched baseline emitted no
matching progress snapshots. **These data do not establish a hard-case
runtime advantage or solver completion advantage.**

## Independent LRUP(⊕) end-to-end correctness and cost

Reran the **four fresh unplanted UNSAT n21/22 cases** with
`--compact=false --proof=<file>`, separately for each solver and each
of the two selectors. This is eight baseline-versus-dual *proof pairs*,
16 proof files in all. The separately supplied, unmodified Xorcle
`tools/check_lrup_parity.py` checker accepted **every** proof. Crucially,
for each pair the entire proof file was **byte-for-byte identical**
(SHA256 matched), as did all official search counters.

Including both solver proof generation time and independent checker
time, the four-pair geometric mean end-to-end gains were:

| Selector | Verified UNSAT proof pairs | Geometric mean speedup including checker |
| --- | ---: | ---: |
| cyclic | 4 | **1.515×** |
| leading-term watchlist | 4 | **1.359×** |

Proof checker costs were roughly unchanged because the emitted proofs
were identical. These proof-generation runs use `--compact=false`, so
their timing figures **must not be combined** with the default-compaction
timing table. The test covers four small UNSAT formulas only.

## Verification status and guardrails

- Python source/data parser and earlier math regressions: **17/17**
  tests passed locally.
- The C++ experimental source compiled and linked successfully; its
  source patch dry-run against untouched upstream passed.
- The Rust `wu018_dual_certificate` regression independently compares
  packed dual evaluation against fully reduced quotient coordinates
  through **12,800 randomized trail states**, including trail extension
  and truncation, and checks its linear-independence implication.
  This file is committed for GitHub CI; local execution was unavailable
  because this scratch executor has no `cargo`/`rustc` binary.
- Python CI and separate Rust CI were added to the existing read-only
  frontier workflow. Their final remote outcome is recorded separately.
- The current implementation is a portable mathematical shortcut only
  in the 64-bit dense scope; expanding to 65+ columns, sparse formulas,
  real industrial workloads, other heuristics, and a wider performance
  range is **future work**. No claim of unique algorithmic novelty,
  worst-case complexity improvement, or progress on P versus NP follows.
- Precise peak-RSS profiling and machine-independent variance estimates
  are not included. As implemented, the cache itself is just four 64-bit
  masks plus constant-sized counters/flags; downstream implementation
  effects were not separately measured.

## Reproduction

1. Produce two source trees at pinned Xorcle revision. Keep one untouched.
   In the second run
   `patch -p1 < research_patches/wu018_four_dual_masks_propagator.patch`
   from the upstream source root, build with `-O3 -DNDEBUG -std=c++23`.
2. Generate heldouts with the compiled Witnora Rust binary:
   `wu014_generate_xnf OUT_EASY 21 22 2 910018` and
   `wu014_generate_xnf OUT_HARD 28 29 1 910018`. Compare manifests to
   the saved SHA256 checksums.
3. Run `scripts/wu018_benchmark_dual.py` twice (selector `cyclic` and
   `leading_term_watchlist`) with `--baseline`, `--dual`, `--instances`,
   `--repetitions 2`, `--timeout 3.5`. Preserve CSV; repeat on hard
   with `--repetitions 1 --timeout 2.5`.
4. For independent native proof checking, run
   `scripts/wu018_check_native_proofs.py` with the unmodified Xorcle
   LRUP(⊕) checker, separate proof output directory and results file.
   Proof files are large temporary artifacts and are **not** committed;
   SHA256, sizes, times and checked results are in the committed CSV.
5. Test math with
   `cargo test --release --manifest-path rust/witnora-ve/Cargo.toml
   --bin wu018_dual_certificate` and Python parsers with
   `python3 -m unittest -v scripts.test_wu018_benchmark_dual`.

## Next falsifiable gate, WU-019

1. Generalise the on-demand dual construction to **arbitrary width**
   with checked packed words, compare against immutable original Xorcle
   and Xorcle's published watchlist on truly separate XNF distributions.
2. Replace eager rebuild/back substitution with *incrementally updated
   duals* only if benchmark counters show a clear further saving.
3. Add repeatable confidence intervals, memory accounting, source-level
   independent differential verification, and proof+checker measurements
   on substantially harder instances where both variants finish.
4. Reject or scope down the technique if wide instances, mixed parity
   density, or proof overhead erase the small-instance improvement.

The current result is **an experimentally demonstrated and proof-checked
small-instance XNF solver engineering acceleration**. Generality and
novelty remain open.
