# Witnora: completion-driven research automation (research branch)

Status: opt-in research infrastructure on draft PR #122, not a production
solver, not an autonomous mathematical-discovery agent.

## What now runs automatically

A push touching research queue / CRC files on branch
`research/w-crc-001-asymmetric-v1` starts the dedicated GitHub Actions
workflow `.github/workflows/witnora-research-queue.yml`.

A single bounded job runs three approved experiments in this order:

1. W-CRC-018 matched graph/clause/model-count semantic unit controls.
2. W-CRC-019 exact source-equivalence regression tests.
3. W-CRC-019 28-case encoding-sensitivity pilot versus Ganak.

These are the **current** three approved queue tasks. Earlier task
configurations described chronologically below are historical.

As soon as one subprocess **successfully completes**, the runner launches
the next. If a subprocess fails or times out, it stops; it never labels a
timeout UNSAT. This is **completion-driven, not hourly**.

The task manifest is `research/witnora_research_queue.json`. The runner
is `scripts/run_witnora_research_queue.py`. Each task ID maps to a fixed
reviewed Python module; the manifest cannot inject shell commands.

## Resource and write limits

- At most **3 tasks** per workflow invocation (runner hard maximum 5).
- A task is interrupted after **180 seconds**; the total task budget is
  **480 seconds**, with a hard GitHub job timeout of **15 minutes**.
- At most one queue run concurrently per branch.
- No retries, no periodic scheduling, no self-triggering dispatch loop.
- GitHub token has `contents: read` only. No auto-commit, merge, issue
  creation, destructive shell command, or external secret use.
- CI prints truncated experiment logs and uploads a JSON report as
  `witnora-research-queue-report`, retained for 14 days.
- Each additional eligible research-branch push triggers a fresh, bounded
  queue run. The queue does not repeatedly rerun itself.

The prior hour-based ChatGPT reminder is disabled. This GitHub Actions
workflow does not depend on it. The queue is finite and is refreshed
only by reviewed commits to the research branch, never by its own
automatic writes.

## Scientific test: why four missing triples matter

For the all-positive rank-3 complete CNF on n variables with missing
triple-support family M, let J be the set of variables assigned false.

The formula is satisfied exactly if **every triple contained in J is
missing from the formula**, i.e. `C(J,3) subseteq M`. Therefore the
number of models depends on how missing supports overlap, not merely on
`|M|`.

With four missing triples:

- When the missing supports do not form all four faces of a tetrahedron,
  there are `1+n+C(n,2)+4` models.
- When the missing supports are all four faces of one 4-set, there are
  `1+n+C(n,2)+4+1` models, owing to one additional 4-variable false set.

For n=8 these predicted counts are 41 and 42; for n=11 they are
71 and 72. The benchmark also introduces conflicting literal polarity.
The current W-CRC-004 orbit recognizer **must reject** all these cases
since they exceed its stated omission bound or violate sign coherence.
An independent brute-force evaluator and Ganak cross-check the outputs.
A budgeted exact CRC fallback is allowed to report incomplete.

This is a useful falsification of a too-simple orbit extension; it does
not prove a new complexity bound. The general problem of counting
high-order compatible sets may itself become intractable.

## Editing or extending the queue

Add a reviewed bounded task to `ALLOWED_TASKS` in the runner, then name
that ID in the JSON manifest. Add corresponding tests and select a
resource budget. Each push causes the workflow to run once on this
branch. The runner refuses duplicate and unknown task names.

To dry-run in a Python 3.11 checkout:

```sh
python -m scripts.run_witnora_research_queue --dry-run
python -m unittest tests.test_research_queue -v
```

The `workflow_dispatch` manual Run button for a new workflow is not
generally available until that workflow file exists on the repository's
default branch. This experimental workflow is instead activated by
research-branch pushes without merging anything to main.

## What this does NOT automate

There is no presently configured LLM research API key or paid inference
budget. This runner **cannot invent its own next hypotheses, edit Lean
proofs, or push its own improvements**. It exhausts its finite reviewed
queue and stops. Making that a genuinely autonomous research agent would
require user-controlled model credentials/budget, a protected change
review process, provenance and reproducibility checks, and a separate
research-task generator. That expansion is intentionally not enabled.

TC-063/#121 and the Lean formalization remain separate. Python tests,
Ganak comparisons, and this GitHub workflow are not kernel proofs.

Useful GitHub paths:

- [Draft PR #122](https://github.com/joeyst8/witnora-core/pull/122)
- [Research workflow](https://github.com/joeyst8/witnora-core/actions/workflows/witnora-research-queue.yml)

## Verification checkpoint — 2026-11-03

The existing W-CRC GitHub Actions suite passed on research commit
`3d3ed744a572d5c0f99db292789d3eb70516f7fd`:
https://github.com/joeyst8/witnora-core/actions/runs/41706281993

- **42 Python unittest methods passed**, including queue ordering,
  whitelist rejection, failure stop, timeout stop and task caps.
- **6/6 W-CRC-005 negative-control instances** matched independent Ganak
  and an exhaustive evaluator.
- For n=8, dispersed versus tetrahedral deletions yielded **41/42**
  models; for n=11, **71/72**. Every case was rejected by the
  out-of-scope orbit recognizer and counted by the exact fallback.

This CI result validates the queue **unit tests and benchmark**, not an
independently inspected end-to-end run/artifact of the new dedicated
queue workflow. That operational check is still pending.


## Verified revised queue — 2026-11-03

The research-branch manifest was advanced to the three W-CRC-005
experiments above. Its whitelist and ordering tests passed. The
dedicated workflow then completed successfully with sequential,
bounded execution and JSON artifact upload:
https://github.com/joeyst8/witnora-core/actions/runs/41711345293 .

The new coefficient source-to-count method also passed the full
independent W-CRC/Ganak suite:
https://github.com/joeyst8/witnora-core/actions/runs/41710683455 .
See docs/W_CRC_005_DEFECT_HYPERGRAPH.md for exact results.
This is vetted task automation, not a self-generating agent.


## Verified W-CRC-006 queue — 2026-11-03

The manifest now contains the exact three W-CRC-005/006 tasks listed
above. The whitelist and sequencing tests passed, and dedicated
completion-driven workflow run
https://github.com/joeyst8/witnora-core/actions/runs/41712614609
successfully executed all three in order:

- wcrc005_defect_unit PASS (0.852s)
- wcrc006_conflict_unit PASS (0.944s)
- wcrc006_conflict_ganak PASS (3.388s)

The JSON artifact was uploaded successfully. These observed times
come from this GitHub Actions run and exclude runner setup.
Mock failure/timeout events visible in the preceding safety tests
are intentional tests of fail-stop behavior, not experimental failures.

The independent full W-CRC CI gate also passed 50 tests and all
16/16 mixed-polarity Ganak comparisons:
https://github.com/joeyst8/witnora-core/actions/runs/41711999357 .
The exact mathematics and limits are recorded in
docs/W_CRC_006_MIXED_POLARITY.md .

This remains a **finite, read-only, non-self-modifying queue**.
Its success does not automatically invent the next theorem or create
a new research task. A new reviewed task requires a further draft
commit; no automatic merge into TC-063/main occurs.


## W-CRC-007 adversarial regression carried by the queue

The W-CRC-006 unit task also runs the new W-CRC-007 negative
independence case. Its two disjoint exceptional clause scopes are
not independent under the complete source 3-CNF, so a naive
multiplicative count is rejected. Full updated W-CRC gate:
https://github.com/joeyst8/witnora-core/actions/runs/41712957364
(51 tests passed). The updated queue workflow's file triggers now
also include W-CRC-005/006 unit and benchmark files, and the
dedicated queue succeeded again at
https://github.com/joeyst8/witnora-core/actions/runs/41713038135 .
See docs/W_CRC_007_CLUSTER_FALSIFICATION.md for the exact witness.


## Verified W-CRC-010/011 queue and W-CRC-012 investigation

The reviewed finite queue was advanced to three exact signed-source
separation tasks. Dedicated [queue run #41717147917](https://github.com/joeyst8/witnora-core/actions/runs/41717147917)
completed in sequence with all three subprocesses passing:

- `wcrc010_conditional_unit`: PASS, 0.089s.
- `wcrc011_separator_unit`: PASS, 0.093s.
- `wcrc011_separator_benchmark`: PASS, 0.110s.

The complete W-CRC gate for W-CRC-011 passed **72 Python tests** and
eight mincut timing controls:
https://github.com/joeyst8/witnora-core/actions/runs/41716921282 .

A later W-CRC-012 full-counting test exposed a genuine oversight in
the W-CRC-011 minimum-cut implementation: terminal-arc 'infinite'
capacity was only n+1, which is insufficient when an explicit
max-separator budget is larger than n. The fix binds infinity above
**both n and the configured cut budget**, and a regression test now
requires a clean inconclusive return for a direct group edge even with
a vastly oversized requested budget. This is an example of an
adversarial negative control improving the checker.

The queue remains finite, event-triggered by reviewed branch pushes,
with a read-only token. It does not autonomously create research tasks
or send a ChatGPT notification when a GitHub Action completes.
The W-CRC-012 model-count benchmark is subject to its own separate
full CI gate; its result is not implied by the queue's success.


## W-CRC-012/013 exact source-counting queue — 2026-11-03

A finite reviewed task plan now runs three bounded tasks in order:
`wcrc012_cutset_unit`, `wcrc013_adversarial_unit`,
`wcrc013_adversarial_ganak`. After all inputs are checked, the
event-driven GitHub Actions workflow launches the next only after the
previous succeeds. Its token is read-only and it never auto-merges.

Separately from the queue, the full W-CRC independent gate passed 79
tests and **8/8** W-CRC-012 exact counts against Ganak and analytic
formulas (roughly 11–32× faster in the *special hub family*):
https://github.com/joeyst8/witnora-core/actions/runs/41718161372 .

W-CRC-013 broadened to 12 cases with explicit source-witness-search
timing: 5/5 modular signed-block cases admitted and matched Ganak
(roughly 7.6–14.8× faster with one SAT witness solve included), while
7/7 chain/ring/random controls returned *incomplete* without
incorrect counts. The independent Ganak counter solved 12/12.
Full W-CRC CI passed **81 tests**:
https://github.com/joeyst8/witnora-core/actions/runs/41719072620 .

These are pilot family-level timings and established cutset
conditioning, not a broad #SAT victory or an autonomous theorem
discovery. A passing queue run validates that the three *reviewed*
commands executed sequentially; it does not autonomously create the
next experiment or send a chat message.


### Verified W-CRC-012/013 completion-driven execution

[GitHub Actions research queue #41719605405](https://github.com/joeyst8/witnora-core/actions/runs/41719605405)
completed the new approved manifest in order, without any
fixed-interval polling:

1. `wcrc012_cutset_unit`: **PASS**, 0.107 seconds.
2. `wcrc013_adversarial_unit`: **PASS**, 0.155 seconds.
3. `wcrc013_adversarial_ganak`: **PASS**, 0.809 seconds.

The queue printed `QUEUE_COMPLETE` and uploaded its JSON report.
This demonstrates bounded, event-triggered experiment sequencing;
it is **not** a self-generating research agent and cannot post new
updates to a closed ChatGPT turn on its own.


## Verified W-CRC-014/015 completion-driven work — 2026-11-03

The W-CRC-014 VE prototype rescues 10/10 long chain/ring model counts
that the previous component enumeration rejected, but rescanning all
remaining factors at each elimination step caused large-n timing loss.
W-CRC-015 adds a versioned heap and variable-to-factor incidence index
while preserving exactly the old factor algebra and operation budgets.

The entire independent W-CRC gate passed **92 Python test methods**
and 15/15 Ganak controls at:
https://github.com/joeyst8/witnora-core/actions/runs/41722453364 .

The dedicated finite research queue also completed successfully at:
https://github.com/joeyst8/witnora-core/actions/runs/41722441602 .

Actual subprocess task ordering and results:

1. `wcrc014_ve_unit`: PASS (0.356 seconds).
2. `wcrc015_indexed_unit`: PASS (0.263 seconds).
3. `wcrc015_indexed_ganak`: PASS (5.055 seconds).

The queue wrote a JSON report and uploaded its artifact. It **still
does not invent new hypotheses, edit source automatically, merge into
TC-063/main, or post to ChatGPT when the turn is closed**.


## Verified W-CRC-016 held-out completion-driven queue

[Dedicated W-CRC-016 queue #41723396262](https://github.com/joeyst8/witnora-core/actions/runs/41723396262)
finished all reviewed experiments successfully; its subprocess sequence
was `wcrc015_indexed_unit`, `wcrc016_heldout_unit`, then
`wcrc016_heldout_ganak`. The queue uploaded its JSON result artifact
and remained bounded and read-only.

Full W-CRC [CI #41723375350](https://github.com/joeyst8/witnora-core/actions/runs/41723375350)
passed **95 Python test methods** and an independently counted
23-case held-out study. Witnora completed 16/16 random-tree and
signed-ladder cases and correctly returned incomplete on all 7
high-width/no-cut controls. Ganak completed every case. These
results do **not** establish general SAT performance superiority.

The distinction between *automatically executing a fixed reviewed
queue* and *autonomously inventing the next research hypothesis*
remains critical: only the former is configured, and the queue
does not send messages into a closed ChatGPT thread.


## Verified W-CRC-017 dense-semantic queue and full gate — 2026-11-03

The manifest now selects `wcrc016_heldout_unit`,
`wcrc017_dense_unit`, and `wcrc017_dense_ganak` in precisely that
order. The [dedicated queue run #41724585736](https://github.com/joeyst8/witnora-core/actions/runs/41724585736)
confirmed all three finished successfully: 0.170s, 0.096s, and
2.077s respectively. A JSON results artifact was uploaded.

The independent [full W-CRC gate #41724594677](https://github.com/joeyst8/witnora-core/actions/runs/41724594677)
completed with **97 Python tests passing** and 16/16 exactly matched
Witnora/Ganak dense 2-CNF counts on graph-equivalent parity,
inconsistent parity, positive OR, and signed OR examples (n=8,16,32,64).
12/12 analytic model counts were verified. All cases had the complete
variable primal graph, but different source semantics. The n=64
signed-OR case was roughly **18.5x slower** than Ganak's reported
engine time; the positive-OR case was ~36.7x faster. These are
limited single-runner pilot timings and show no general #SAT edge.

See `docs/W_CRC_017_DENSE_SEMANTICS.md` for the complete design,
integer counts, timing and limitations. Neither a new interaction
metric nor new polynomial-time theorem has been established.
The queue is still finite/read-only; it will not invent W-CRC-018
or notify ChatGPT when no conversation is active.


## Verified W-CRC-018 matched-semantic queue and full gate — 2026-11-03

The new reviewed queue tasks are `wcrc017_dense_unit`,
`wcrc018_matched_unit`, and `wcrc018_matched_ganak`. The
[dedicated queue run #41725603426](https://github.com/joeyst8/witnora-core/actions/runs/41725603426)
passed all three subprocesses in sequence (0.275s, 0.109s,
1.100s), with the JSON artifact saved. The independent
[full CI #41725616948](https://github.com/joeyst8/witnora-core/actions/runs/41725616948)
passed **101 Python tests** and **10/10 Ganak source-count matches**.

Both matched 2-CNF families had exactly K_n, n(n-1) source clauses
and two models at n=8/12/16/32/64. Exhaustive small-n model
profiles distinguished all-live globally coupled parity from
(n-1)-backbone/one-free-variable forcing, despite the same
size and model count. A three-way XOR formula gave an exact
counterexample to relying on pairwise dependence alone.
At n=64 the Witnora generic backend was ~44.6x slower than
Ganak on the forcing family, an important negative control.
See `docs/W_CRC_018_MATCHED_SEMANTICS.md` for mathematics and
limits. This does not establish a novel invariant or a general
#SAT solver advantage.

The queue remains finite, source-triggered by new reviewed
commits, and read-only. It cannot create W-CRC-019 on its own,
auto-merge a proof, or send closed-chat notifications.


## Verified W-CRC-019 exact same-solution encoding pilot — 2026-11-03

The current finite, reviewed tasks are `wcrc018_matched_unit`,
`wcrc019_encoding_unit`, `wcrc019_encoding_ganak`. Dedicated
[queue run #41727817224](https://github.com/joeyst8/witnora-core/actions/runs/41727817224)
succeeded with all three task processes and uploaded JSON results.
Independent [full W-CRC gate #41727822505](https://github.com/joeyst8/witnora-core/actions/runs/41727822505)
passed **105 Python tests**, including full truth-table checks that
all alternative CNF encodings of each n-variable family have precisely
its original set of satisfying assignments at n=6/8/10.

Across 28 cases n=8/16/32/64, Ganak returned 28/28 exact 2-model
counts; Witnora returned 25 exact 2-model counts and 3 honest
`INCOMPLETE_BUDGET` statuses on the logically implied-unit variants.
The cause was identified: n-1 independent explicit affine unit rows
expand into 2^(n-1) Fourier modes while the sparse spectrum is capped
at 4,096. At n=64, an equivalent 63-unit encoding counted in 0.5453
ms versus 336.0094 ms for the original 4,032-clause encoding,
**without counting the cost of deriving that simpler encoding**.
This is encoding sensitivity, not a new intrinsic complexity theorem
or an end-to-end solver speedup. Full evidence and limitations:
`docs/W_CRC_019_EQUIVALENT_ENCODINGS.md`.

The bounded read-only queue still cannot invent its own next
experiment or notify a closed ChatGPT chat. A future approved
W-CRC-020 could test source-level consensus normalization with its
preprocessing time included, maintaining independent Ganak crosschecks.


## Native Rust migration workflow — 2026-11-03

The separate opt-in `.github/workflows/rust-ve.yml` builds and
tests a standalone Rust exact VE component kernel plus its in-process
PyO3 extension. The [verified Rust run #41730735431](https://github.com/joeyst8/witnora-core/actions/runs/41730735431)
passed native tests, source-level Python differential controls, and
eight independent analytic/Ganak cases (up to 256 variables).
The legacy [105-test W-CRC gate #41730735450](https://github.com/joeyst8/witnora-core/actions/runs/41730735450)
also passed. Rust is an opt-in backend; neither the existing Python
default nor Lean TC-063 formal proof files were changed.

The Rust in-process binding improved this restricted component-counting
pilot by ~1.1–4.5x over the Python indexed engine, with no general
SAT/#SAT speedup or formal count-certificate claim. See
`docs/RUST_001_NATIVE_VE_MIGRATION.md` for the complete benchmark.

**This Rust workflow is not a self-generating AI research loop**. Like
the original queue, it responds to vetted research-branch pushes.


## Verified R-003 source preprocessor — 2026-11-03

The native Rust migration now has a second exact operation:
assignment-set-preserving source simplification (unit closure and bounded
consensus). It is explicitly selected by
`source_preprocessor="rust_consensus"`; Python remains the default.

The [R-003 Rust workflow](https://github.com/joeyst8/witnora-core/actions/runs/41736318985)
passed **9 Rust tests**, **4 additional Python integration tests** and
**12/12 exact Ganak counts**. Randomized controls compared full
satisfying-assignment sets, not just cardinalities. Three previously
resource-refused equivalent-unit encodings n=16/32/64 now count exactly.
For the n=64 pairwise-forcing case, full source-to-count latency was
185.03 ms without preprocessing and 3.40 ms including Rust
preprocessing. For the parity negative control it regressed from
18.32 ms to 23.27 ms. These are family-specific two-repeat timings,
not a blanket speedup claim. Details:
`docs/RUST_003_SOURCE_PREPROCESS.md`.

The dedicated Rust tests run on research-branch pushes. They **do not**
add steps to the finite autonomous research queue, infer a mathematical
theorem, post to a closed ChatGPT conversation, merge into main or
modify TC-063 Lean proofs. The remaining Rust migration requires
adversarial gating, expanded held-out controls and independent formal
checking if transformation certificates become part of the trust base.


## Verified R-004 adaptive native admission — 2026-11-03

Native Rust now exposes an opt-in `rust_adaptive` source-preprocessing
mode using an inexpensive polarity-pattern screen on 2-CNF clause
supports. If that screen rejects, the original clauses pass through
unchanged; if admitted, the already verified R-003 exact simplifier
runs. The screen is a **performance heuristic**, not a novel
complexity measure or proof of irreducibility.

[Dedicated R-004 workflow #41737533969](https://github.com/joeyst8/witnora-core/actions/runs/41737533969)
passed **10 native Rust tests**, **5 Python native integration
tests** (including 120 new randomized full-assignment-set
checks) and **12/12 independent Ganak matches**. It bypassed all
four parity negative controls while admitting all eight forcing
cases. In the n=64 forcing sample it cut source-to-count time
257.01 to 3.82 ms including admission and preprocessing; on
n=64 parity 27.27 ms raw versus 28.15 ms adaptive, still a
small overhead. Full analysis:
`docs/RUST_004_ADAPTIVE_SOURCE_ADMISSION.md`.

This feature is built and tested automatically on vetted commits
but it **does not** start a self-modifying research loop, post to
the user's closed chat, modify Lean TC-063 or merge draft PR #122.


## Verified R-005 exact native XOR extraction — 2026-11-03

A third opt-in computation moved from Python to Rust: recognition
and removal of **complete** width-1..3 source-CNF XOR blocks,
with all nonmatching clauses retained. The source counter selects
it via `source_extractor="rust"`; `"python"` remains the default.
No unverified partial-parity assumptions are introduced, and
native equation masks use 256-bit-capable arbitrary-precision
integers.

[Dedicated R-005 workflow #41738553647](https://github.com/joeyst8/witnora-core/actions/runs/41738553647)
passed **13 Rust tests**, **4 new Python source-extractor tests**
including **280 exact-output plus full-model-set comparisons**,
and **12/12 independent Ganak count matches**. On the n=64
pairwise-parity negative control, *whole adaptive-preprocessing
and source counting* latency was 38.08 ms with Python extraction
and 21.06 ms with Rust extraction (~1.8x, two repeats). On
n=64 forcing it was 5.43 versus 4.59 ms (~1.18x). These
are controlled comparisons, not a general #SAT superiority claim.
Complete evidence: `docs/RUST_005_EXACT_XOR_EXTRACTION.md`.

The existing reviewed read-only research queue is not self-writing
and cannot notify the user in a closed ChatGPT chat. No Lean TC-063
proof files or production default choices were changed.


## Verified R-006 exact native coefficient engine — 2026-11-03

The fourth opt-in Rust computation is exact batched right-CNF
Walsh coefficients, using component-wise inclusion-exclusion
and arbitrary-precision rational dyadics. `coefficient_backend=
"rust_inclusion_exclusion"` can be selected in both the direct
boundary and source count adapter; `"python"` remains default.
The new explicit mode×subset operation budget fails closed
without silent Python Shannon/orbit fallback.

[Dedicated R-006 CI #41740113548](https://github.com/joeyst8/witnora-core/actions/runs/41740113548)
passed **17 native Rust tests**, **4 new Python tests** with
randomized entire Walsh spectra and full affine model-count
differentials, and **16/16 independent Ganak matches**
against analytic formulas. n=60 with 20 independent OR
components and three XOR blocks produced exactly
6,281,023,877,654,589 models in all three validators.
In that controlled coefficient-engine benchmark, Python took
0.7021 ms and Rust 0.2218 ms, including projection/spectrum
and coefficient assembly but excluding raw source parsing.
Full details: `docs/RUST_006_RIGHT_WALSH_COEFFICIENTS.md`.

This verified source-triggered CI is **not** autonomous theorem
discovery. The separate finite read-only research queue still
cannot generate its own next experimental task or send a
notification to a closed ChatGPT thread. Lean TC-063 and main
remain untouched.
