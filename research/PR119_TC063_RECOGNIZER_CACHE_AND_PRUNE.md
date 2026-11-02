# TC-063 Recognizer: Graph Cache and Non-Separator Pruning

Status: tested implementation optimization. **Not a new mathematical theorem or a general SAT speedup.**

## What changed

1. Build the CNF primal graph only once per call to `recognize_separator_affine_family`.
2. Reuse the same graph for every candidate cut; do not cache it across different formulas.
3. If deleting a candidate set produces fewer than two connected components, immediately reject it. Such a candidate cannot be a valid separator, regardless of its affine residuals. Prior production code continued expensive residual certificate construction even after `ok = False`.
4. Preserve candidate enumeration order, the first accepted cut, all accepted component and certificate semantics, and the independently checked G14 result. The diagnostic reason for a non-separator is now explicitly `fewer than two components`; this intentionally changes part of the *failed candidate* trace.

## Strict regression tests

`tests/test_pr119_recognizer_graph_cache_equivalence.py` checks:

- Cached graph versus freshly reconstructed graphs: identical full recognition result, including traces, on three small affine families, archived Dubois20, a variable relabel, and a dense random 3-SAT negative control.
- Production graph construction occurs exactly once per invocation; uncached reference invokes it once per candidate (plus the unused initial graph for the patched reference).
- Historical no-pruning/no-cache recognizer: **same selected cut and candidate count** as optimized production.
- For Dubois20 and its relabel: byte-for-byte equal certificate dictionaries when the checker-builder recomputes graph components; certificate independently verified and UNSAT certified.
- Dense random negative control: no separator claimed, no false UNSAT certificate.

The complete pre-optimization trace is not identical: skipped non-separators now report a more accurate reason. This is a diagnostic-only change, not a change to accepted decisions.

## Small benchmark (local Python 3.12, x86_64)

Command: `python -B -m research.pr119_separator_selection_benchmark --trials 2 --permutations 1`

Wall-clock total includes cut selection, native G14 certificate construction, and independent verification. Medians over two measurements for positive cases and one for the negative control. The baseline `production` mode is an explicit replay of the original per-candidate graph rebuilding *and* expensive validation of non-separators. This avoids accidentally changing the historical baseline when production is optimized.

| Input | Legacy total (s) | Optimized production total (s) | Ratio | Result |
| --- | ---: | ---: | ---: | --- |
| Dubois20, 160 clauses / 60 vars | 8.518 | 0.486 | 17.5× | Same cut `[1,38]`; UNSAT certified |
| Relabeled Dubois20 (seed 11) | 4.379 | 0.321 | 13.6× | Same cut `[1,9]`; UNSAT certified |
| Dense random 3-SAT (160 clauses) | 5.968 | 0.643 | 9.3× | Both diagnostic only; no false certificate |

The original Dubois20 accepted certificate remains 7,783,801 UTF-8 JSON bytes. A *different* experimental balanced policy selects `[10,29]` and produces 3,756,935 bytes, but balancing is **not** in production yet: its total-time advantage is inconsistent across relabels and has not been validated against established SAT solvers.

## Limits and next gate

- These are short, machine-specific runs, not robust statistically significant solver benchmarks.
- The 3-SAT negative control has no special hard SAT guarantee; it tests conservative recognition, not UNSAT solving performance.
- Run independent structured non-Dubois families and compare total wall-clock and memory against current general-purpose SAT solvers with the same inputs before making an impact claim.
- The G5/G14 Lean theorems and their assumption boundaries remain separate from this Python implementation-level speedup. A fully universal Python-to-Lean refinement proof and broader TC-063 completeness claim are still open.
