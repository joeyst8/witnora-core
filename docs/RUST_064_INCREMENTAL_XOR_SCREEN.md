# R-064 — Necessary exact-XOR pattern prefilter (partial native, pending CI)

The cheap screen `possible_two_xor_patterns` now has an opt-in Rust equivalent.
It counts distinct clause supports with arity 2..6 and exactly `2^(arity-1)`
clauses, rejecting repeated variables within a clause. It returns true when
at least two supports pass this **necessary**, not sufficient, pattern count.
It does not infer an actual XOR equation or certify satisfiability.

The native differential gate compares 800 deterministic random canonical
source-CNF inputs, including independently generated complete XOR gadget
controls, against the untouched Python default. Full cut selection and
incremental SAT solving remain in Python. Native CI is pending; this is a
partial module migration and contributes no new verified full-file count.
