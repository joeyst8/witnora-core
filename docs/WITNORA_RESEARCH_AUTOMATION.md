# Witnora: completion-driven research automation (research branch)

Status: opt-in research infrastructure on draft PR #122, not a production
solver, not an autonomous mathematical-discovery agent.

## What now runs automatically

A push touching research queue / CRC files on branch
`research/w-crc-001-asymmetric-v1` starts the dedicated GitHub Actions
workflow `.github/workflows/witnora-research-queue.yml`.

A single bounded job runs three approved experiments in this order:

1. W-CRC-005 symmetry-defect falsification. Test four missing triple
   supports arranged as a tetrahedron versus dispersed omissions;
   independently count every model and compare to Ganak.
2. W-CRC-004 exact Walsh/orbit unit checks.
3. W-CRC-004 orbit versus Shannon/Ganak benchmark.

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
workflow does not depend on it.

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
