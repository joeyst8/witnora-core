# R-107: native symbolic GF(2) ANF polynomial algebra

Four Boolean-quotient polynomial operations now have opt-in Rust paths:
XOR, multiplication with idempotent monomials (`x*x = x`), Shannon
substitution, and canonical equation-set normalization. Each output remains
the same immutable Python frozenset structure as before.

The focused CI compares 270 seeded polynomial pairs, both substitution
branches, and duplicate/zero equation handling. The bounded symbolic
Shannon counting recursion, CNF source normalization, and downstream
formal-proof boundary remain Python and are **not** certified by R-107.
