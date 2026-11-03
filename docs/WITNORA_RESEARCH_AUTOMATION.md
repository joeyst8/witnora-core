# Witnora: completion-driven research automation (research branch)

Status: opt-in research infrastructure on draft PR #122, not a production
solver, not an autonomous mathematical-discovery agent.

## What now runs automatically

A push touching research queue / CRC files on branch
`research/w-crc-001-asymmetric-v1` starts the dedicated GitHub Actions
workflow `.github/workflows/witnora-research-queue.yml`.

A single bounded job runs three approved experiments in this order:

1. W-CRC-012 exact source cutset model-counting unit controls.
2. W-CRC-013 signed-block analytic count and chain/ring rejection tests.
3. W-CRC-013 heterogeneous, random and adversarial model-count benchmark,
   including Glucose3 witness-search timing and independent Ganak checks.

These are the **current** three approved queue tasks. Earlier W-CRC-005
through W-CRC-011 configurations described chronologically below are
historical.

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
