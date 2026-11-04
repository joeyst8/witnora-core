# R-105: native constructive nonedge matching color upper bound

The bounded Rust `matching_color_bound_native` implements the Python
enumeration of vertex covers whose complements are independent, with
memoized maximum cardinality nonedge matching and lexicographic tie breaks.
It emits the exact cover, matched pairs, and checked proper coloring witness.

`matching_color_bound(..., backend="rust")` is opt-in. The focused CI
compares complete result dictionaries against the original Python method on
150 deterministic inputs within the declared `n <= 11` study boundary.

This is a constructive upper bound, not a new chromatic algorithm or a
formal proof of optimality.
