# W-CRC-015: Incremental indexed variable elimination

Status: **verified restricted-family implementation speedup**;
the dedicated completion-driven research queue passed all approved
W-CRC-014/015 tasks. Full green CI gate is recorded separately.

Sequential W-CRC-015 research queue:
https://github.com/joeyst8/witnora-core/actions/runs/41722441602

## Problem exposed by W-CRC-014

W-CRC-014's bounded exact factor variable elimination rescued large
low-width source components, but at n=128/256 it became slower than
the independent Ganak engine. The underlying factor arithmetic was
small (at most 3 variables per intermediate table), so repeated
global rescoring of *all* elimination candidates was a plausible
Python implementation bottleneck.

## W-CRC-015 change

- `witnora_core/crc_variable_elimination_indexed.py`
- New **opt-in** `component_backend="variable_elimination_indexed"`
  in `witnora_core/crc_cutset_count.py`.
- Existing `"enumeration"` default and the frozen
  `"variable_elimination"` reference remain available and unchanged.

The new backend maintains an incidence index mapping each variable to
its current factor IDs. Each variable's union-scope score resides
in a versioned min-priority heap. On eliminating a variable, only
other variables whose factors were removed or added get new scores.
An outdated heap score is never accepted; its version fails.
Exact factor multiplication, Boolean summation, source-mask
validation, max-table-width cap, and counted operation cap remain
unchanged.

This is ordinary indexed variable elimination. It improves
implementation complexity but does *not* prove any new algorithmic
worst-case bound for general #SAT. Width/treewidth still controls
the exponential factor growth (see Larrosa/Dechter prior art):
https://ics.uci.edu/~dechter/publications/r89a.html

## Trust controls

- Five new unit test methods, including **200 seeded random signed CNF
  cases** checked against both the frozen W-CRC-014 output and an
  independent exhaustive all-assignment evaluator.
- Operation counts were checked against the reference exactly, not
  merely model totals; both choose the same min-scope ordering.
- 16/32/64/128-variable chain/ring analytic Fibonacci/Lucas controls,
  source-level cutset integration, signed 3-variable modular blocks,
  no-clause/free-variable and invalid-mask/budget controls.
- The new dedicated read-only three-task queue was verified end-to-end:
  `wcrc014_ve_unit` PASS (0.356s),
  `wcrc015_indexed_unit` PASS (0.263s),
  `wcrc015_indexed_ganak` PASS (5.055s), with `QUEUE_COMPLETE`.
- The benchmark's **12/12 admitted counts** matched frozen reference,
  independently derived analytic formulas and Ganak integers.
  Three planted dense random 3-CNFs still fail closed. All **15/15**
  independent Ganak runs completed exactly.

## Paired runtime results

All times are milliseconds, one GitHub-hosted Actions environment.
Both W-CRC modes time two complete source-to-count invocations with
identical input, full externally supplied Glucose3 witness, cut
discovery, same width and work caps. The independent Glucose3
witness search time is then **added** to the indexed method for
Ganak comparison. Ganak's engine time excludes child process
startup. Ratios are exploratory two-repeat pilot results.

| n | Source | Frozen VE ms | Indexed VE ms | Indexed + witness ms | Ganak engine ms |
|---:|---|---:|---:|---:|---:|
| 16 | chain | 1.1761 | 0.7030 | 0.8192 | 9.0427 |
| 16 | ring | 1.8112 | 1.1169 | 1.3718 | 9.1242 |
| 32 | chain | 3.6225 | 1.3965 | 1.6661 | 28.7319 |
| 32 | ring | 6.3865 | 2.4586 | 2.7254 | 34.0302 |
| 64 | chain | 15.0807 | 3.2185 | 3.5623 | 41.8984 |
| 64 | ring | 29.0734 | 5.9483 | 6.2543 | 47.8520 |
| 128 | chain | 84.5080 | 8.3178 | 8.6841 | 57.3135 |
| 128 | ring | 166.0162 | 15.1468 | 15.4975 | 74.6738 |
| 256 | chain | 511.7769 | 22.6467 | 23.0714 | 101.7220 |
| 256 | ring | 971.9901 | 43.5203 | 43.9610 | 136.1539 |

For n=256 this is about **22.6× lower W-CRC internal time**
on a chain and **22.3×** lower on a ring versus the same frozen
reference. Including separately timed SAT witness search, the indexed
prototype was **4.4×** faster than Ganak engine on the n=256 chain,
**3.1×** faster on the n=256 ring, and faster in all 10 tested
chain/ring cases. Every integer count agreed with both an external
counter and a Fibonacci/Lucas closed form.

Two nonuniform signed three-variable block benchmarks also matched
the W-CRC-014 reference, Ganak and analytic model totals. Indexed
implementation cost was only modestly better (0.921×/0.941× of old
time); low-width disconnected *small* components were already cheap.
The three seeded dense random controls (n=16/24/32) continued to
return `INCOMPLETE_BUDGET` for both implementations, while Ganak
returned exact counts.

## Scientific limits and next falsification

- Source witness acquisition is external and includes a separate,
  one-shot Glucose3 time; method still requires declared endpoint
  groups and a small primal separator.
- This is favorable width-2 source structure, not representative
  arbitrary CNF. No Lean proof of this Python implementation exists.
- Ganak's default counter cache has a small probabilistic guarantee;
  analytic exact counts independently support the reported cases.
- Timings have two W-CRC repeats, one external run, one hosted runner;
  not an industrial benchmark or stable solver ranking.
- No P≠NP, #P separation or general polynomial SAT claim follows.

The next meaningful study is a **held-out graph-family admission and
width-stress benchmark**, reporting unsuccessful candidates,
actual intermediate widths, witness/preprocessing cost and memory.
A theoretically fresh Witnora idea would require more than choosing
existing separator/VE representations efficiently.
