# R-095: concrete Lean coloring certificate source in Rust

Rust now provides the exact Fin-valued paint declaration, lexicographic
clique witness selection, and full concrete coloring certificate Lean source
emission. Source graph generation and Python `_validate` remain unchanged;
all input cases are validated before native emission. The default backend
remains Python, and the new Rust implementation is an explicit opt-in.

Compiled differential CI compares complete source text for every default
prefix and cyclic case ordering, 180 randomized finite-value declarations,
150 clique searches, and malformed color/identifier rejection. Lean kernel
verification remains separate from the exporter and is not replaced.

Status: awaiting compiled native Rust CI.
