# TC-063 exhaustive small separator attack (v59)

Draft PR #60. CI: https://github.com/joeyst8/witnora-core/actions/runs/41253352811

## Independent finite result

The harness exhaustively enumerates a controlled family consisting of:

- One separator variable `x1`.
- Either one or two independent residual components, each using a two-variable XOR system.
- For each component and separator branch, one of four parity-equation sets: none, parity 0, parity 1, or both.
- Zero, one, or both separator-only unit clauses.

There are 64 + 1024 = 1,088 parameter combinations. After removing absent-separator and repeated canonical formulas, **1,023 distinct formulas** were tested: 63 with one residual component and 960 with two.

For every formula, a separate Boolean truth-table evaluator computed the SAT/UNSAT truth value without consulting G14, G5 or its certificate. The harness then required *both* the native G14 verdict and native certificate verifier to agree.

| Independent oracle class | Count |
|---|---:|
| SAT | 494 |
| UNSAT | 529 |
| Total | 1,023 |
| Wrong or unverified result | **0** |

The test is deterministic and retains the first failing formula's exact integer clauses, source hash, branch parity parameters, expected verdict, produced verdict and native checker errors if a regression occurs.

## Meaning and limits

This is empirical validation of a finite, specially constructed family, **not** a proof of `UnsatCoverComplete c (Family c r)` or of asymptotic complexity. The oracle grows exponentially and is used only as an independent small-instance reference. These results do not generalize to arbitrary formulas, arbitrary affine component widths, or unrestricted separators.

The next hard mathematical step is to prove a *semantic UNSAT cover existence lemma* for the independent `SemanticSAF.Family`: every UNSAT source and every separator branch must contain at least one UNSAT residual component. Its proof requires assembling component witnesses under variable disjointness. Then prove a **complete G5 contradiction-certificate constructor** from every inconsistent accepted affine row system. Only those two existence results, together with the actual producer/refinement and cost obligations, can close the TC-063 family theorem.

Avoid merely increasing the size ladder as a substitute for these universal proofs.
