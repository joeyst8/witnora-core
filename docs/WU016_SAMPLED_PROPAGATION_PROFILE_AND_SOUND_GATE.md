# WU-016 — sampled native-XNF propagation costs and an independently falsified shortcut

**Status:** 24 paired baseline/instrumented solver observations, 10 Python
regression tests passed; **no optimized solver or new SAT theorem**.

## Purpose and source identity

WU-015 showed that swapping Xorcle's GF(2) row representation to sparse
cost more CPU on our independent dense random XNF even at equal conflict
and propagation-attempt counts. WU-016 asks which *existing routine* takes
time and whether a cheap algebraic predicate can safely prove that a
clause cannot propagate.

Baseline is the unmodified Xorcle from Beame and Sun, *Extending CDCL to
Disjunctions of Parity Equations*, SAT 2026,
<https://doi.org/10.4230/LIPIcs.SAT.2026.5>, source commit
`af93ea646a4237958e9925bc684dcd545e68de30`. The original compiled
binary and source tree were **not modified** by these measurements.

Two *separately linked* measurement-only versions of `src/core/solver.cpp`
were created: a timer-only version, and a timer-plus-observational-gate
version. All releases use the same pinned core object library except the
instrumented `solver.cpp.o`. The tracked patch
`research_patches/wu016_sampled_profile_and_gate.patch` applies to the
pinned upstream source and reproduces the final measurement-only version.
It does **not** skip clauses, change branching decisions or alter proofs.

## Measurement protocol

- Profiled `selector_->next_with_hint()` and
  `propagator_.unit_propagate_one_clause` at **1-in-256** calls,
  and successful-propagation post-processing and conflict analysis
  at **1-in-32** calls, using `steady_clock` bracketing.
- Emitted cumulative machine-readable stderr snapshots every million
  attempted propagations, and a final record for completed runs.
  Snapshots survive deadline kills; final counters cannot be inferred
  from a timed-out run.
- Paired unmodified binary against each instrumented binary on eight
  fresh WU-015 n21/22 cases (3.5s each, SAT/UNSAT completed) and four
  WU-014 n28 cases (2s each; all censored). Rotated run order, serial
  executions. For all eight completed easy pairs, the instrumented and
  baseline **conflicts, attempted propagations, successful propagations,
  watch updates and decisions matched exactly**. Every SAT model was
  re-evaluated on the original XNF. UNSAT statuses in this profile are
  not independently proof-checked; WU-015 separately certified one of
  the same new-seed instances.
- Sample timing brackets add overhead, are not randomized and do not
  account for all work. The numbers below are **not** exact CPU fractions;
  multiplying samples by call counts can overstate total wall time.

## Observed profile (timer-only version)

| Metric | 8 easy completed inputs | 4 hard censored inputs |
| --- | ---: | ---: |
| Mean attempts at final/last snapshot | 3,041,781 | 8,000,000 |
| Attempted / successful propagations, pooled | **195.9** | **325.9** |
| Mean sampled clause-selection cost | 41.3 ns | 40.6 ns |
| Mean sampled clause-propagator cost | 161.6 ns | 229.0 ns |
| Mean sampled successful post-processing cost | 154.3 ns | 218.8 ns |
| Mean sampled conflict-analysis cost | 10,933 ns | 15,724 ns |

The last hard-case snapshots, rather than unobserved termination totals,
include roughly **32 million clause-propagation attempts** across the four
timed-out runs. This supports prioritizing native propagation CPU profiling
over blindly changing the equation representation. It does **not** show that
all non-propagating checks are unnecessary: a sound solver must establish
whether watched equations can newly become unit under a changing trail.

## Candidate 1 — raw nonpivot projection: **unsound; rejected**

Initial conjecture: take watched equations' raw coefficients on columns
that are not pivots of the trail's row-echelon matrix. If the two projected
vectors are nonzero and different, infer linear independence modulo the
trail span and skip propagation. **This inference is FALSE.**

Concrete counterexample over GF(2), with three columns:

- Trail span `U = span(011)` (bit 0 is the pivot column).
- Watch `a = 011` is itself in `U`; watch `b = 100` is not.
- Restricting to nonpivot columns (bits 1 and 2) gives `010` and `100`:
  nonzero, distinct projections, **yet a reduces to zero modulo U**.

Reason: a row-echelon *pivot row can still contain nonpivot bits*.
Projection onto raw nonpivot coordinates therefore does **not** annihilate
the trail span. This shortcut would be unsound if enabled. We caught the
counterexample before modifying any solve path, and added the regression
test `test_raw_nonpivot_projection_is_unsound`.

## Candidate 2 — distinct free leading columns: sound, low yield

Corrected conservative predicate for a clause with two watched rows:

1. Obtain their *actual leading set-bit columns* `p(a)` and `p(b)`.
2. Return true only if both exist, are **different**, and **neither** is
   a pivot column of the current trail's echelon span.
3. Restrict observations to calls without a trigger hint. No skip was
   performed in WU-016; the unmodified propagator still ran and its
   result was compared to the predicate.

**Proof of soundness:** every nonzero vector in an echelon span has a
leading column equal to one of that span's pivots. Thus neither `a` nor
`b` is in the span. Since their leading columns are different, the
leading column of `a+b` is the smaller of the two and is likewise a
nonpivot. So `a+b` is not in the span. Their cosets in the quotient
are nonzero and distinct, hence linearly independent over GF(2), and
neither watched equation can produce a unit consequence. This is a
basic GF(2) fact, **not a novel mathematical theorem**.

Observational results from the independent second instrumented build:

| Corpus | Eligible sampled calls | Predicate true | Fraction | True-gate samples with propagator nonnull |
| --- | ---: | ---: | ---: | ---: |
| Fresh n21/22, 8 completed | 95,049 | 1,042 | **1.10%** | 0 |
| Hard n28, 4 censored | 125,000 | 217 | **0.17%** | 0 |

These are **sampled** hit rates and checks; zero contradictory observations
does not replace the proof above. Crucially, even a free prefilter could
skip at most its triggered share of attempts in this sample. The extra
leading-bit/pivot lookups have a cost too, and clause-cost heterogeneity
prevents translating a 0.17% attempt share directly into a wall-time bound.
We therefore **reject implementation as a performance improvement** on
the available evidence and record it only as a sound negative-control
candidate.

## What is genuinely unknown; next gate

Can Witnora produce **incrementally maintained, sound certificates of
watch-pair independence** that eliminate a much larger share of native
XNF checks *without* reintroducing work through cache invalidation,
backtracking, proof generation or verification? Published watchlists
already handle some related bookkeeping, so any new mechanism must
beat both the untouched cyclic and leading-term-watchlist options.

For WU-017, first measure the **potential upper-bound coverage** from
more expressive sound quotient signatures on *recorded trails*, and
include update/backtracking cost. Implement a proof-compatible skip
only if independent held-out instances show a meaningful achievable
coverage advantage and the predicted net runtime survives a direct
baseline comparison. Include independent UNSAT certification and total
proof-checking wall time. Reject hypotheses with near-zero coverage.

No results here imply P=NP, polynomial arbitrary SAT, general XNF solver
superiority, or a new proof-complexity result.

## Reproduce source-level instrumentation

With the pinned upstream Xorcle tree present, use the included patch on
an **independent source copy**, not on the original pinned baseline:

```sh
patch -p1 < research_patches/wu016_sampled_profile_and_gate.patch
```

Recompile only its `src/core/solver.cpp` with upstream release flags
`-O3 -DNDEBUG -std=c++23` and upstream include paths, replace that object
in a **copied** `libxorcle_core.a`, and relink against the original
`src/cli/main.cpp.o`. Do not relink it into the pristine source binary.

Use `scripts/wu016_profile_xorcle.py` with `--instances`, `--baseline`,
`--profiled`, `--max-cases`, `--timeout`, and `--results`. The complete
per-case timer-only and gate-observation CSV records are preserved under
`research_data/wu016/`. Run the isolated mathematical regression tests
with `python3 -m unittest -v scripts/test_wu016_linear_gate.py`.
