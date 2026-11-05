# R-128–R-129: native clause overlap and source-XOR validation path

R-128 moves the exact witness-excluding clause-overlap computation to
Rust: `_extra_touching_clauses(..., backend="rust")` returns all nonwitness
clauses touching at least one detected XOR variable.

R-129 routes `detect_cnf_xor_patterns(..., backend="rust")` through both
native full-gadget CNF parity enumeration (R-127) and native extra-clause
overlap (R-128). Group formation, safety metadata and diagnostics still
use the Python reference implementation. Crucially, a recognized pattern
remains marked `IMPLIED_CONSTRAINT_ONLY` and its source clauses are not
removed.

Differential CI compares 350 seeded overlap cases, all complete and
incomplete 2–6-variable parity gadgets and 120 mixed seeded CNFs.
No detected constraint is promoted to an independent source proof.
