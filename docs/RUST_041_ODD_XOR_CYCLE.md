# R-041: native source-bound odd XOR cycle discovery

**Verified green:** https://github.com/joeyst8/witnora-core/actions/runs/41772221307

## Migration

The previously untouched `witnora_core/cycle_discovery.py` has
an independent native Rust counterpart in
`rust/witnora-ve/src/odd_xor_cycle.rs` with opt-in
`discover_odd_xor_cycle_rust`.

The port independently extracts only **complete two-clause** CNF
encodings of exact binary XOR constraints, sorts the graph equations
and BFS neighbors like Python, and returns the first
contradictory closed parity walk with identical metadata.

## Independent tests

`tests/test_odd_xor_cycle_rust.py` compares **1,050**
seeded random CNFs and **100** planted contradictory triangles
against original Python discovery. Each reported edge is
independently checked to have its complete XOR CNF source
pattern. The closing vertex and odd parity of the walk are checked,
and a single suggestive CNF clause is not accepted as an XOR
equation. The complete Rust/Python/Ganak gate passed.

## Trust

This is **not** a mathematical proof of UNSAT by itself. Every
result remains `UNVERIFIED_STRUCTURAL_CANDIDATE` and
`NOT_LEAN_VERIFIED`. The separate source-bound Lean verification
gate is unchanged.

Migration inventory: **29** parallel-reference Python modules,
**531** not migrated, **0** originals removed.
