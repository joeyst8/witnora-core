# Exact affine evidence for every G14 component (v52)

Draft PR #53; research continuation of `PYTHON_G14_EXACT_AFFINE_V51.md`.

## Claim tested

The previous experiment proved semantic affine equivalence only for the **selected UNSAT component** in each branch. That suffices for an UNSAT cover, but does not establish the stronger membership claim that **every residual component** is exactly affine.

This experiment calls Python's native `build_affine_residue_certificate` independently for every conditioned component returned by `_condition_by_separator`, retaining the selected G5 certificate where available. It requires each native certificate to contain `INITIAL_ROWS` and a verified native checker status.

The generator exports a list of G5 row lists corresponding position-for-position to the entire G14 component list in each separator branch. Lean checks:

1. Exactly as many row lists as residual components (avoids `zipWith` truncation).
2. `checkSemanticExactAffine 2 component rows = true` for **every** paired component/row list.
3. The earlier selected UNSAT G5 proofs, exact residual partitions, exhaustive separator branches, and source-level DIMACS UNSAT theorem.

The fixture generator additionally requires both native SAT-witness-verified and UNSAT-native-certified component statuses, so the all-component check cannot silently reduce to selected UNSAT components alone.

## Evidence

The three fixed `saf_unsat_cover_n` instances with `n = 2,3,4` each have two separator branches, yielding a total of **18 checked component-branch pairs** (4 + 6 + 8). The generated evidence and closed Lean obligations are reproducible through `.github/workflows/g14-all-affine-components.yml`.

The initial run [GitHub Actions 41245539356](https://github.com/joeyst8/witnora-core/actions/runs/41245539356) passed all three sizes, the Python fixture test, Lean module builds and no-holes guard. A later run additionally enforces explicit presence of SAT and UNSAT native statuses.

This is an **instance-level exact affine membership** result, not proof of universal Python behavior or the full TC-063 quantification.

## Next experiment

Introduce a controlled *non-affine residual* and verify the same generated gate rejects it, while clearly differentiating: (a) no native affine evidence, (b) a malformed correspondence, and (c) a source component with genuine extra constraints. Then bind each native component proof to a stable source hash and component identity, not only branch/list position.
