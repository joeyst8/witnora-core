# R-104: native graph decomposition and finite coloring bounds

The Rust `nonedge_graph_bounds_native` evaluates four existing finite
subroutines in one call: connected-component lists, two-vertex connectivity,
Brooks componentwise upper bound, and the degeneracy upper bound. Python
helpers expose opt-in `backend="rust"` and retain their reference defaults.

The CI gate compares all four answers on 350 deterministic graphs, including
disconnected, dense, sparse, and empty families. These algorithms are known
finite graph procedures, not new theoretical results.
