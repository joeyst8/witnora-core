# W-CRC-016: Held-out graph-family admission and exact-count benchmark

Status: **95 green Python test methods**, a completed independent
23-case Ganak pilot, and verified bounded research-queue execution.

Full green W-CRC CI:
https://github.com/joeyst8/witnora-core/actions/runs/41723375350

Dedicated sequential W-CRC-016 queue:
https://github.com/joeyst8/witnora-core/actions/runs/41723396262

## Question

Can the W-CRC-015 indexed, source-witness-checked cutset model counter
extend beyond path/ring examples and repeated fixed signed blocks?
What is its *observed admission rate* and what fails?

This benchmark uses newly seeded **signed random trees**, signed
ladder graphs, planted random signed 3-CNF, and a large-clique
separator control. No source model counts are guessed when the exact
backend returns incomplete. All admitted integers are compared
against an independently executed Ganak counter; its default cache
has a small probabilistic guarantee and does not constitute a formal
proof oracle.

## Case design

- **8 random recursive signed trees**, n=32/64/128/256 × seeds
  16016,16017. One literal in each clause is always positive,
  ensuring all-ones satisfies the formula. Endpoints are chosen
  far apart by independent graph BFS. Each tree's source primal
  graph has a small separator and low induced width.
- **8 signed two-rail ladders**, n=32/64/128/256 × the same
  seeds. Along-rail/rung clauses are mixed polarity but the
  second literal stays positive. Endpoint groups are the two
  leftmost/rightmost rungs. Minimum vertex separator has size 2.
- **6 planted signed random 3-CNFs**, n=16/24/32 × the same
  two fresh seeds, at 3n clauses. Source primal graphs do not
  admit the requested endpoints with a size<=2 vertex cut.
- **1 bridged two-clique case**, n=21, two 10-variable cliques
  linked through a single source hub. The separator exists, but
  surviving clique components require intermediate factors wider
  than the intentionally fixed 4-variable cap.

A separate Glucose3 solver finds and times a satisfying source
assignment for **every** case; it is not assumed for free.
W-CRC-015 then verifies it and runs cut discovery, all branches
and local bounded factor variable elimination.

Hard caps: max separator size 2, max primal graph edges 10000,
max VE factor scope 4 variables, 200000 counted factor operations,
and per-method time budgets. Resource failure returns
`INCOMPLETE_BUDGET`, not a false SAT/UNSAT/model count.

## Exact admissions and failures

| Family | Cases | W-CRC exact | Ganak exact | Outcome |
|---|---:|---:|---:|---|
| signed random trees | 8 | 8 | 8 | full integer agreement |
| signed 2-rail ladders | 8 | 8 | 8 | full integer agreement |
| planted dense random 3-CNF | 6 | 0 | 6 | no admitted cut |
| bridged K10 cliques | 1 | 0 | 1 | cut found, factor width rejected |
| **Total** | **23** | **16** | **23** | **16 exact matches, 7 safe refusals** |

Three W-CRC-016 unit tests additionally checked 10-variable
random trees and signed ladders against a separate exhaustive
full-assignment model counter, plus a small bridged-clique
positive-cap/negative-cap comparison. Entire full CI: **95
Python tests passed**.

## Full-CI measured held-out timings

All times in milliseconds. W-CRC timings include the separately timed
external Glucose3 source witness plus median of two complete indexed
W-CRC invocations. Ganak uses its independently reported **engine
time**, excluding child-process startup.

| Family | n | Seed | W-CRC + witness | Ganak engine | W-CRC/Ganak |
|---|---:|---:|---:|---:|---:|
| tree | 32 | 16016 | 0.9370 | 17.1870 | 0.055 |
| tree | 32 | 16017 | 0.9642 | 16.5168 | 0.058 |
| tree | 64 | 16016 | 1.9188 | 21.0565 | 0.091 |
| tree | 64 | 16017 | 1.8189 | 21.2897 | 0.085 |
| tree | 128 | 16016 | 3.8464 | 30.7519 | 0.125 |
| tree | 128 | 16017 | 3.9001 | 30.9210 | 0.126 |
| tree | 256 | 16016 | 8.8297 | 50.6966 | 0.174 |
| tree | 256 | 16017 | 9.4128 | 54.2920 | 0.173 |
| ladder | 32 | 16016 | 1.9008 | 24.5474 | 0.077 |
| ladder | 32 | 16017 | 1.8548 | 29.1372 | 0.064 |
| ladder | 64 | 16016 | 4.2963 | 32.4422 | 0.132 |
| ladder | 64 | 16017 | 3.2578 | 33.2775 | 0.098 |
| ladder | 128 | 16016 | 10.5872 | 56.5225 | 0.187 |
| ladder | 128 | 16017 | 10.3214 | 47.6243 | 0.217 |
| ladder | 256 | 16016 | 28.6203 | 81.8859 | 0.350 |
| ladder | 256 | 16017 | 21.4656 | 88.7414 | 0.242 |

On these particular narrow-graph sources, W-CRC+Glucose3 witness
search was approximately **2.9–18× faster** than Ganak's counting
engine alone across 16 cases. These are pilot wall times with only
two W-CRC repeats, one external run, and significant possible
GitHub-hosted runner contention; a standalone matched benchmark
is required before broad performance comparisons.

All 7 adversarial controls produced `INCOMPLETE_BUDGET`; Ganak
returned exact counts. The 21-variable K10-bridge example is an
especially important *positive separator but negative width*
control: the discovery certificate alone cannot justify an
unbounded runtime claim.

## Scientific interpretation and limits

This is a **successful restricted-family performance and exactness
experiment**, not a discovery of a new complexity theorem. Tree
and ladder primal graphs have bounded width, a familiar reason
variable elimination runs efficiently. Source SAT witnesses and
group choices are supplied through separate classical routines.
The method remains exponential in cut size and intermediate factor
width, with no general SAT/#SAT guarantee.

Further research must avoid only refining planted, easily recognized
low-width examples. Useful directions include a completely held-out
external suite, high-width but algebraically special constraint
families, and a distinct, source-checkable interaction measure
whose predictive power survives controls matched for clause/edge
count and ordinary treewidth.
