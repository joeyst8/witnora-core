# W-CRC-011: Bounded automatic minimum separator discovery

Status: **verified graph min-cut + source-bound conditional certificate,
not a general SAT solution**.

Full green W-CRC workflow, **72 Python tests** and 8 scaling cases:
https://github.com/joeyst8/witnora-core/actions/runs/41716921282

Completed sequential research queue, **all three tasks passed**:
https://github.com/joeyst8/witnora-core/actions/runs/41717147917

## Hypothesis and method

W-CRC-010 requires a supplied separator S. W-CRC-011 finds the
minimum-cardinality **primal-graph vertex separator** between disjoint
nonempty source groups A and B while forbidding removal of any
group-member vertex.

Each original variable v is split into directed v_in and v_out
nodes. Their link has capacity 1, except group endpoints have capacity
greater than n. An original undirected primal edge produces two
high-capacity directed arcs. A super-source connects to A and B connects
to a super-sink. Exact augmenting-path max flow determines the
minimum separator cardinality (standard vertex-cut reduction).
After extracting the residual min cut, independent BFS verifies the
actual original graph has no A-to-B path once that separator is deleted.

A candidate is accepted only within explicit max-separator-size and
primal-edge budgets, and only if an offered source-model witness
passes W-CRC-010's signed-source conditional graph certificate. An
UNSAT source, invalid witness, direct A-to-B edge, large cut or budget
exhaustion returns `None`; no unsupported instance is called UNSAT.
This is established graph theory (Menger / max-flow-min-cut), not a
new algorithmic breakthrough. The minimum is among vertex separators
in the *original primal graph*. Conditioning clauses can make smaller
semantic separators possible; W-CRC-011 does not find them.

Implementation:
- `witnora_core/crc_separator_discovery.py`
- `tests/test_crc_separator_discovery.py`
- `scripts/benchmark_crc_separator_discovery.py`

## Exact correctness tests

The six new test methods include:
- a 16-variable star, whose unique minimum cut is its hub;
- two vertex-disjoint paths requiring a 2-vertex cut;
- a direct edge between endpoint groups (no admissible cut);
- disconnected sources with cut size 0;
- forged witness, UNSAT source, and explicit budget rejection;
- **100 random 6-variable positive CNFs** cross-checked against
  exhaustive minimum-separator enumeration. Every admitted separator
  was also checked against an independently enumerated conditional
  model probability table.

Entire CI suite: **72 Python tests passed**.

## Practical cost: discovery versus known cut

All eight star-source benchmarks found exactly the 1-variable hub.
All reported times are GitHub Actions milliseconds, median of two
repeats. 'Known' supplies the separator to W-CRC-010, while
'Discovered' includes the minimum-cut search and W-CRC-010 proof.

| n | hub assignment | Known-separator audit | Discovered + audit | overhead |
|---:|---:|---:|---:|---:|
| 16 | 0 | 0.0669 | 0.1368 | 2.045× |
| 16 | 1 | 0.0370 | 0.0940 | 2.541× |
| 64 | 0 | 0.1572 | 0.4046 | 2.574× |
| 64 | 1 | 0.0899 | 0.3011 | 3.349× |
| 128 | 0 | 0.3047 | 0.7408 | 2.431× |
| 128 | 1 | 0.1745 | 0.5508 | 3.156× |
| 256 | 0 | 0.6061 | 1.5255 | 2.517× |
| 256 | 1 | 0.3393 | 1.3266 | 3.910× |

There is no evidence yet that separator discovery outperforms solving
the original instance end-to-end. The benchmark only compares
certificate construction costs, not full #SAT algorithms.

## Verified automation

The three reviewed research-queue tasks:
1. `wcrc010_conditional_unit`;
2. `wcrc011_separator_unit`;
3. `wcrc011_separator_benchmark`

all ran in order and **passed** in the dedicated event-driven queue run
#41717147917, finishing in approximately 0.089s, 0.093s, and 0.110s
of subprocess time respectively. The queue remains bounded/read-only,
requires a new eligible research commit to trigger, and does not
generate new tasks or post messages to ChatGPT autonomously.

## Next falsifiable experiment (W-CRC-012)

Implement exact component-product #SAT counting after enumerating all
assignments to the found small separator; compare the **full time,
including cut discovery**, with independent Ganak #SAT and an analytic
model-count control on small-separator families. Detect and record
cases in which cutset conditioning is *slower* or fails the component
enumeration resource budget. Standard cutset conditioning, not a
general new complexity theorem.
