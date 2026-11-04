# R-098: Rust bounded recoloring comparison

`color_bounded_recolor_native` ports the bounded, incomplete backtracking recolor
search. It retains the Python vertex ordering, color ordering, changed-vertex
budget, visit count, and budget-exhaustion report. Python remains the default;
`bounded_recolor(..., backend="rust")` opts in.

The seeded multistart DSATUR heuristic and experiment sampling remain Python.
The deterministic native result must exactly match the Python reference on
the focused differential CI matrix before any milestone is certified.

No failed budgeted search is a proof of non-colorability, and neither novelty
nor formal verification is claimed.
