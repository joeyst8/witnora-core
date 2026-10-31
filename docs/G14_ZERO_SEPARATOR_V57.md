# G14 zero-separator and zero-variable UNSAT composition (v57)

Draft PR #58. Successful complete-source CI: https://github.com/joeyst8/witnora-core/actions/runs/41248119441

## Direct results

Two minimal UNSAT formulas are produced as native G14 covers with separator `[]`, exactly one separator branch `S1`, and a native G5 UNSAT component:

1. `[[1],[-1]]`: the contradictory unit-affine equations.
2. `[[]]`: the zero-variable empty clause, equivalent to `0=1`.

The original G14 component finder considered only primal-graph variable vertices, so the empty clause could not belong to any component. This branch adds a special `C0` component **only when the source already contains an empty clause**, and places empty residual clauses there. It does not silently treat an empty residual arising solely from an invalid separator assignment as a valid component when no source empty clause exists.

For both formulas, the test constructs a canonical ASCII DIMACS document, independently preserves the parser's raw clauses, integer tokens and decimal spellings, then calls the production `verify_g14_unsat_cover_with_lean` gate. It requires:

- `verified: true`
- `lean_formal_status: LEAN_END_TO_END_G14_UNSAT_VERIFIED`
- `source_document_verified: true`
- `source_normalization_verified: true`

The strong status is earned by one closed Lean theorem about the **actual source document and accepted certificate**, not a native UNSAT flag or a collection of assumed branch premises.

## Boundaries

This closes two *concrete* low-arity/zero-separator production gaps. It does **not** prove that Python finds a certificate for every member of the independently defined `Family c r`, prove universal Python-to-Lean execution refinement, or establish the fixed-`c` runtime bound.

The special `C0` treatment is deliberately narrow. Other separator-only clauses which become empty after conditioning, and arbitrary semantically affine but syntactically unrecognized formulas, remain research targets. Extending this mechanism requires an explicit audit of component completeness and native affine extraction, not a general assertion of TC-063 completeness.

## Next attack

Seek the smallest certified `Family c r` instance that still fails full G14 production. Start with separator-only clauses producing empty conditioned branches; test that a failing branch receives an explicit zero-variable contradiction component without incorrectly marking satisfied branches UNSAT. Continue randomized small XOR systems with independent Lean-checked exactness and compare native certificate availability.
