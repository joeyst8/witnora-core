# R-093: numeric Lean certificate source generation in Rust

The opt-in native exporter reproduces the Python source text for numeric edge
lists, vertex color lists, clique lists, and theorem declarations byte for
byte. Python continues to validate candidate names and proper colorings using
the existing `_validate` routine before passing cases to Rust. Lean itself,
not Rust or Python source generation, checks the emitted certificate theorem.

Differential CI covers defaults, every prefix and cyclic permutation of the
predeclared cases, and malformed names/colorings. This migration is format
parity only and makes no new formal-verification or novelty claim.

Status: awaiting compiled native CI.
