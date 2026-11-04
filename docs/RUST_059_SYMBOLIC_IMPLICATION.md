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

## Verification update

The R-059 native differential step passed in [Rust Actions run #41868308092](https://github.com/joeyst8/witnora-core/actions/runs/41868308092).
The native helpers are verified, but `derive_equality` and
`triage_with_implications` remain Python. This is a verified partial module.

## R-068 — Complete native classification path (pending CI)

Extends R-059 with native equality-pair normalization, deduplicated sorted
axiom references and known-axiom catalog construction. The opt-in Python
`derive_equality_rust` and `triage_with_implications_rust` adapters retain the
same finite expression grammar and pre-existing Python hypothesis search,
but invoke Rust for classification and known axioms. The new gate checks
800 seeded grammar equalities, full report equality, and malformed titles.

Once CI passes, every public symbolic-implication computation has a tested
native path and the module can be promoted from partial to parallel reference.
No syntactic derivation is upgraded to a Lean theorem or novelty claim.
