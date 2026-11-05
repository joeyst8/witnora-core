# R-109: native residual ANF variable-hypergraph components

The Rust `anf_residual_component_sizes_native` computes connected-component
sizes in the variable-scope hypergraph after deleting a specified variable
mask. Arbitrary-width scope integers are passed as decimal strings; no
fixed-word graph-size truncation occurs.

The deterministic Python separator-candidate search can opt in through
`backend="rust"`, retaining all candidate-budget rules and tie breaks.
Focused CI compares 340 seeded scopes and 85 bounded separator searches.

The structured counting and separator-conditioned summation algorithms
remain Python. A failed bounded search does not show that no separator exists.
