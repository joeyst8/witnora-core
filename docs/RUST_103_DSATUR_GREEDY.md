# R-103: deterministic native DSATUR greedy witness

`dsatur_greedy_coloring_native` ports the existing Python DSATUR vertex
priority, smallest-available-color rule, and proper coloring witness. The
Python `_dsatur_greedy_coloring(..., backend="rust")` interface is opt-in,
so existing experiments retain their default Python semantics.

The focused CI checks the exact coloring vector and greedy upper bound over
440 seeded graphs, including sparse, dense, complete, and empty cases.

DSATUR is a known heuristic and need not be chromatic-optimal on general
graphs. No novelty or formal verification is implied.
