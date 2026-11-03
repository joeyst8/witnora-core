# Scope-aware elimination on Witnora's auxiliary parity bridge

**2026-11-03 — ongoing controlled research, draft PR #121**

This experiment follows the [auxiliary clause-violation tensor bridge](AUXILIARY_VIOLATION_TENSOR_BRIDGE.md),
where a mathematically exact factor representation created far worse
*greedy min-degree* graph fill than the original CNF:

    (n,m)       original CNF   flat parity   auxiliary bridge
    (32,224)          26            30              94
    (96,576)          73            90             310
    (256,1536)       191           241             921

The numbers are elimination widths under a specific order, *not*
true optimal treewidth, SAT runtimes, or proven complexity lower bounds.

## Hypothesis

A generic min-degree ordering may choose auxiliary violation variables
too early. Those variables connect source clauses through parity rows;
eliminating them can introduce many new fill edges and dense global
coupling. We therefore test the following complete orders on the
**same** frozen planted random 3-CNFs and the **same** auxiliary factors:

1. **min_degree** — unrestricted smallest active graph degree, with
   numeric variable-ID tie breaks; reproduces the previous baseline.
2. **source_first** — eliminate every original source variable before
   any clause-violation auxiliary variable; min-degree within a block.
3. **aux_first** — opposite phase ordering.
4. **beam_fill** — among the eight lowest-degree candidates, prefer the
   one whose elimination creates the fewest new neighbor-neighbor edges.

The research implementation is
`witnora_core/factor_elimination_orders.py`;
`scripts/benchmark_factor_elimination_orders.py` measures
(n,m) = (32,224), (96,576), (256,1536)).
`tests/test_factor_elimination_orders.py` checks each order is a
permutation and independently replays its induced width, including
the frozen n=32 auxiliary graph.

## Metrics and limits

Measured fields: graph vertex and factor counts; induced width,
new fill edges, and wall-clock **ordering computation time**.
A width for a constructed elimination order is an upper bound on the
graph's optimal treewidth, and a potentially costly upper bound on
generic table-based contraction space. It does not establish a
lower bound on what a different algorithm could do.

The graph-based min-fill preference does not exploit XOR algebra or
variable assignment semantics. A decrease in these width diagnostics
would motivate implementing an actual exact tensor/counting engine,
not prove such an engine will beat the source-CNF solver.

Even when phase ordering helps, all these factorizations contain
the original source clause interactions. Mere auxiliary splitting
cannot evade worst-case SAT complexity. We need independent counting
timings, full overhead, memory profiles, and adversarial controls.

## Next decision gate

- If some order reduces width *substantially*, implement exact
  variable-elimination counting on bounded-width cases and compare
  against direct source-CNF contraction.
- If orders remain much worse than the original, stop optimizing this
  purely generic factor graph and experiment with **algebra-aware
  parity elimination** (GF(2) normalization, local variable
  conditioning, shared-row summaries) prior to tensor contraction.
- In either case, preserve TC-063 as a separate formal verification
  obligation; these experiments do not complete TC-063 or P vs NP.

Benchmark numbers and the CI run will be appended only after they
are observed and verified.


## Verified experimental outcomes

The **full** n=32, 96 and 256 run completed successfully with the
[new order-search CI gate](https://github.com/joeyst8/witnora-core/actions/runs/41652408617).
Independent replay tests verified every reported order's width on
the frozen small graph; the full 256 benchmark printed all measurements.

| n / clauses | Original CNF | Flat parity | Auxiliary min-degree | Auxiliary source-first | Auxiliary aux-first | Auxiliary beam-fill |
|---|---:|---:|---:|---:|---:|---:|
| 32 / 224 | 26 | 30 | 94 | 226 | 94 | **89** |
| 96 / 576 | 73 | 90 | 310 | 590 | 311 | **291** |
| 256 / 1536 | 191 | 241 | 921 | 1575 | 831 | **774** |

All widths are heuristic induced widths, not optimal treewidth or
tensor/SAT performance. The limited min-fill choice reduces the
largest auxiliary *observed* width from 921 to 774 (~16%), still
far worse than the original source's 191.

| Auxiliary n/clauses | Min-degree ordering ms | Source-first ms | Aux-first ms | Beam-fill ms |
|---|---:|---:|---:|---:|
| 32 / 224 | 58 | 126 | 61 | 105 |
| 96 / 576 | 1,367 | 2,856 | 1,344 | 2,344 |
| 256 / 1536 | 34,594 | 96,721 | 29,753 | 61,585 |

This table measures the cost of calculating graph orders alone,
not coefficient extraction. Source-first produced a much wider graph
than the unconstrained baseline, while aux-first and beam-fill
helped somewhat at 256. At 32 and 96, aux-first was comparable to
min-degree; beam-fill consistently reduced width modestly.

The implementation also logged fill-edge counts (256 case):
min-degree 613,422; source-first 1,433,487;
aux-first 597,706; beam-fill 577,081.

A subsequent usability update made n=256 full-order search
**opt-in** with `python -m scripts.benchmark_factor_elimination_orders --large`;
default CI runs 32/96. The recorded full 256 result above was
produced by the preceding successful full-size workflow.

### Decision

This test confirms that elimination strategy affects induced width,
but **no evidence of efficient general exact counting emerged**.
The correct next milestone is an algebra-aware parity contraction
or bounded-width exact factor-count pilot with total runtime and
memory comparison. Iterating on graph ordering alone is unlikely
to overturn the large gap to the source CNF.
