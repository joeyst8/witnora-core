# R-130: full native source-CNF XOR pattern discovery

An additional opt-in mode, `detect_cnf_xor_patterns(..., backend="rust_full")`,
performs support grouping, complete parity-gadget matching, additional
clause overlap and exact skip/rejection diagnostics entirely in Rust.
Python constructs the original `XorEquation` and `XorSystem` objects with
unchanged safety flags (`IMPLIED_CONSTRAINT_ONLY` and original source
clauses retained). The earlier `backend="rust"` composed algebra path
remains independently available.

The Rust matcher fails closed on parity support above 16 variables,
consistent with the native R-127 enumeration budget. Differential CI
compares complete/incomplete 2–6-variable gadgets in both detection modes,
180 seeded mixed formulas, and the disabled-pattern diagnostic.
Nothing here makes inferred XOR patterns independently trusted proofs.
