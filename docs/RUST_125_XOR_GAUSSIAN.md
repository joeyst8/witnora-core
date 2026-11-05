# R-125: native XOR Gaussian elimination and complete trace

`solve_xor_system_gaussian(system, backend="rust")` executes deterministic
GF(2) row elimination, contradiction detection, back elimination,
assignment reconstruction and forced-value extraction inside Rust.
It emits the same ordered trace events as the Python reference; Python
formats them into the established result schema.

Focused CI compares the complete result dictionaries (including traces,
rank, pivot ordering, free variables, forced assignments and RREF rows)
for 350 seeded systems and explicit satisfiable/inconsistent cases.
`XorSystem` continues to preserve detected-CNF versus sidecar trust flags;
no unsound promotion of a detected relation is authorized. The Rust native
wheel and differential comparisons must pass before this path is verified.
