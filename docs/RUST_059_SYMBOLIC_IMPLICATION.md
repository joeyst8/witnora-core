# R-059 — Fixed-rule symbolic implication triage (pending CI)

Native Rust reproduces the finite directed axiom graph search and syntactic
normalization of `witnora_core/symbolic_implication.py`. Python remains the
default. Opt-in `bound_path_rust` and `normalize_rust` use PyO3 entry points.

The differential test checks every expression in the current expression
grammar and every ordered pair of recognized graph symbols plus unrecognized
control symbols. Rust unit tests also check representative positive and
negative cases. GitHub Actions Rust CI is required before this entry can be
recorded as a verified parallel port.

This triage system deliberately derives only consequences **relative to its
listed, unformalized rules**. It does not turn conjectures into Lean theorems,
assert mathematical novelty, or promote an unresolved candidate to proof.

**Status at authoring:** Python reference tests pass locally (3/3). Rust
differential tests are locally skipped because the native extension/toolchain
is unavailable. Counts remain 44 verified parallel counterparts, 516 Python
files not yet verified, zero Python files retired. R-059 is pending.
