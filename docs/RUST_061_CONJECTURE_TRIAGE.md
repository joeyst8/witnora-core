# R-061 — Conjecture identity normalization (partial native port, pending CI)

The fixed syntactic rewrite functions `normalize_expression`, `identity_key`,
and `known_identity_keys` now have opt-in Rust equivalents. Their purpose is
conservative duplicate/known-catalog classification, not a proof oracle.
Python's full empirical graph search, adversarial challenge, and Lean review
queue remain the unchanged defaults.

Differential controls enumerate every expression in the current grammar,
800 seeded equality pairs, complete known-catalog equality, and malformed
function controls. The Rust crate also has direct positive and negative tests.
Native PyO3 CI has not yet passed this port; do not count the entire
`conjecture_triage.py` module as migrated or verified.

No graph theorem, general SAT performance bound, or novelty result follows
from this syntactic port.
