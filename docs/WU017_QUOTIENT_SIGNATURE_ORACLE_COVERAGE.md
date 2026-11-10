# WU-017 — short quotient signatures cover most non-propagating watches; update cost remains open

**Status:** original observational measurement complete, independent seed
holdout complete; **no algorithmic acceleration or proof-system novelty**.

## Research question

WU-016 showed that a *cheap* leading-nonpivot test could soundly certify
only about 0.17% of hard 2-XNF clause-propagation attempts. Does more
quotient-space information yield materially greater coverage, enough to
justify research into incremental maintenance?

This is distinct from claiming that the signatures are cheap to maintain.
Known incremental Gauss–Jordan reasoning in DPLL(XOR) is prior art; see
Laitinen, Junttila and Niemelä, *Extending Clause Learning SAT Solvers with
Complete Parity Reasoning* (2012),
<https://research.aalto.fi/en/publications/extending-clause-learning-sat-solvers-with-complete-parity-reason/>.
Our target is Beame–Sun's different **XNF disjunction-of-parities**
propagation regime: *Extending CDCL to Disjunctions of Parity Equations*,
SAT 2026, <https://doi.org/10.4230/LIPIcs.SAT.2026.5>.

## Sound certificate, stated precisely

Let the current trail's linear span be `U` in GF(2) on the equation
coefficient-and-constant columns. Xorcle's existing row-echelon matrix
gives each equation `a` a unique **fully reduced** representative `r(a)`
with zero bits on every pivot column. This is a canonical linear
representative of `a + U` in the quotient space.

Fix the first `k` nonpivot columns in ascending order. Let `sigma_k(a)`
be those `k` bits of `r(a)` (or all available bits if fewer than `k`).

For the two watched equations `a,b`, the predicate

`sigma_k(a) != 0 && sigma_k(b) != 0 && sigma_k(a) != sigma_k(b)`

**safely certifies** that `a` and `b` are independent modulo `U`.
Indeed `sigma_k` is linear and annihilates `U`; under any linear map,
two nonzero different GF(2) images are independent. Therefore their
preimages in the quotient are independent. With no external trigger
hint, Xorcle's watcher cannot produce a unit consequence or move a
watch on that clause. It may safely return `nullptr` *if* those exact
certificates have been maintained at the current trail state.

**Important distinction from WU-016's rejected shortcut:** raw bits at
nonpivot columns are **not** a quotient projection. Each equation must
be fully reduced first; otherwise pivot rows carrying nonpivot bits
can make the certificate unsound. WU-017 performs the full reduction
only on sampled **copies** of the watched rows, as an oracle. No
propagator call was skipped and no solver answer was changed.

## Source and experimental design

- Original published, unmodified Xorcle source commit
  `af93ea646a4237958e9925bc684dcd545e68de30` is the baseline.
- Measurement-only source patch
  `research_patches/wu017_quotient_signature_observer.patch` applies to
  a separate pinned source copy and instruments `solver.cpp`.
- Observe one in every 256 eligible clause-propagation calls; only
  dense-representation clauses with at least two watched rows and
  **no trigger hint** are counted. Fully reduce copies of the two
  watched equations against the current trail, extract exact (all-bit)
  quotient independence and 2-/4-/8-bit prefix signatures, then still
  run the original propagator and check for contradictions.
- Paired baseline/instrumented execution on 8 easy n21/22 cases at
  3.5s each, and 8 harder n28/29 cases at 2s each. Each hard run is
  right-censored: use only its last complete one-million-attempt
  snapshot. Completed easy cases matched baseline conflict,
  propagation, watch-update and decision counters **exactly** and
  all SAT models were independently evaluated on original XNF.
  UNSAT statuses from this study are not all independently certified;
  WU-014/015 separately checked selected proofs.
- Deterministic phase-shift control: rerun 8 easy n21/22 and 4 hard n28
  cases, moving the 1/256 sample trigger from residue 0 to residue 127.
  The full source change is exactly that one condition, reproduced by
  `research_patches/wu017_oracle_sample_phase127.patch`.
- **Fresh holdout:** 4 new n28/29 XNF formulas using the WU-014 Rust
  generator with base seed **910017**, one seed per n/family. The
  manifest SHA256 is
  `3665657604ca1d8b7a561d3f03c881fd7a0ae2101125275d0d44d5662a2aa167`.
  This was generated after the initial profiling design and has not
  been used to tune the observer.

## Measured coverage of certifiable no-propagation calls

Percentages below have *eligible sampled attempts* as denominator.
They are not measured solver speedups, not independent IID samples,
and not percentages of total wall time.

| Corpus | Distinct formulas | 2-bit | 4-bit | 8-bit | Exact full quotient |
| --- | ---: | ---: | ---: | ---: | ---: |
| Easy n21/22 | 8 | 35.81% | **78.59%** | 93.16% | 94.01% |
| Hard n28, initial phase | 4 | 36.45% | **79.79%** | 94.45% | 95.32% |
| Hard n29 | 4 | 36.74% | **80.16%** | 94.54% | 95.36% |
| Fresh unseen n28/29 | 4 | 36.64% | **80.17%** | 94.69% | 95.49% |
| Easy n21/22, phase 127 | 8 | 35.75% | **78.63%** | 93.21% | 94.02% |
| Hard n28, phase 127 | 4 | 36.53% | **80.01%** | 94.55% | 95.43% |

On all logged sampled trials, **zero** signature-true calls returned a
propagation from the original unmodified routine, and **zero** cases
contradicted the WU-016 leading-column implication. This empirical
check complements—but is not a substitute for—the linear algebra proof.

The data establish a promising **logical opportunity**: at least on
these independent dense-random 2-XNF families, only four canonical
quotient bits are enough to certify *about four-fifths* of watched
no-propagation calls. Eight bits come near exact checking. The
mechanism is ordinary GF(2) linear algebra; whether **incremental
maintenance cheaper than recomputation** is possible here remains
unanswered.

## Preliminary cost gate: why eager maintenance is unattractive

The instrumented observer also sums `selector_->num_clauses()` after
every successful trail propagation. This simulates how many clause
entries a **naive rebuild of all current database signatures** would
touch at each such event. It counts inactive entries and omits other
events such as decisions/backtracks, so this is *neither a lower bound
nor an exact implementation cost*.

| Corpus | Simulated all-database signature refreshes / measured propagation attempts |
| --- | ---: |
| Easy n21/22 | **6.31×** |
| Hard n28 | **5.06×** |
| Hard n29 | **5.10×** |
| Fresh unseen n28/29 | **5.05×** |

This suggests eager full-database refreshing is a poor starting point:
the number of hypothetical signature updates alone already exceeds
the original number of clause-propagator calls. Each update also has
nonzero GF(2) cost. The ratios do **not** rule out a watch-aware,
selectively updated or lazily certified method.

## Next falsifiable gate (WU-018)

**Open question:** can a small set of current-trail *dual functionals*
(elements of `U`'s annihilator) be maintained on learning and
backtracking with much less total work than the avoided reductions?
This is not an assertion of originality; incremental algebraic
reasoning is well studied. A successful XNF-specific mechanism must:

1. Maintain a sound signature for **the current trail version**, not an
   obsolete prior rank or decision level, across compaction/backtracks.
2. Invalidate or update only provably affected watched clauses; charge
   all maintenance and false misses, including memory overhead.
3. Preserve the native solver's SAT answers and independent UNSAT
   certificate checking, with the proof-generation/verification cost
   included in the total runtime budget.
4. Beat both the untouched cyclic and published leading-term-watchlist
   configurations on **new holdout seeds**. Drop the approach if the
   certificate-maintenance cost consumes the 80% theoretical coverage.

Nothing here proves a general SAT speedup, an original complexity
theorem, or P=NP. The outcome is a repeatable *coverage-and-cost gate*,
not a claimed new solver.

## Reproduction

Apply `research_patches/wu017_quotient_signature_observer.patch` to a
**copy** of the pinned upstream Xorcle tree and compile/relink its
`solver.cpp` independently exactly as done in WU-016. Run the shared
`scripts/wu016_profile_xorcle.py` harness with `--baseline`,
`--profiled`, `--instances`, `--results`, `--timeout`, `--max-cases`, and
optional `--skip-cases` for n29-only selection. For the phase-offset
control, apply the second one-line patch to a *separate* copy before
compiling. The plain baseline executable must remain unchanged.

The manifest, six per-instance CSV files and mathematical tests are
under `research_data/wu017/` and `scripts/`. Generate the fresh input
set with `wu014_generate_xnf <destination> 28 29 1 910017`. Test the
source-agnostic quotient lemmas with
`python3 -m unittest -v scripts/test_wu017_quotient_signatures.py`.
