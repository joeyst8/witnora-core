# R-067 — Seeded hidden separator CNF generator (pending CI)

The final primary function in `hidden_separator_challenge.py` now has an
opt-in native implementation. Python supplies the exact `Random(seed).sample`
MT19937 label stream, preserving the frozen random sequence; Rust constructs
both complete canonical XOR gadget families, the original two fixed clauses,
and the optional cross-noise clause, then relabels and canonicalizes the CNF.

The gate compares source-CNF SHA-256 hashes, complete canonical clause lists,
and full metadata dictionaries on 500 deterministic seeds split across both
widths and noise settings, including invalid-width controls.

R-065 and R-066 have passed native CI. If R-067 also passes, the three primary
Python functions have native equivalents and the source module may be promoted
to a verified parallel reference in the ledger. Until then, this is a pending
module. No Lean theorem, SAT hardness result, or independent randomness
equivalence is claimed.
