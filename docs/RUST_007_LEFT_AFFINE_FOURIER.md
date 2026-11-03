# R-007: Exact GF(2) projection and left Fourier expansion in Rust

Status: **verified opt-in native port** on research branch
`research/w-crc-001-asymmetric-v1`, draft PR #122.
No merge to main and no edits to formal TC-063/Lean PR #121.

[Verified R-007 Rust/PyO3 CI](https://github.com/joeyst8/witnora-core/actions/runs/41741754634)

## What was ported

`rust/witnora-ve/src/left_affine.rs` replaces two related
Python operations **when explicitly enabled**:

1. `_project_affine`: deterministic GF(2) Gaussian
   elimination of internal pivots followed by boundary
   pivots. For each boundary assignment, the surviving
   projected equations determine feasibility; all feasible
   assignments have exactly `2^free_internal` internal
   completions. Inconsistent systems produce an empty
   spectrum, not a guessed model count.
2. `_sparse_fourier`: the exact Walsh expansion of the
   resulting boundary compatibility/completion function.
   Each new equation `mask·x = rhs mod 2` multiplies
   by `(1 + (-1)^rhs χ_mask(x))/2`.
   The resulting coefficients are dyadic; Rust stores
   arbitrary-precision signed integer numerators with
   a **common power-of-two denominator**.

The native PyO3 `affine_spectrum_native` binding returns
projected rows, the free-variable count, and the complete
bounded sparse spectrum. A strict Python bridge
`witnora_core/crc_rust_affine.py` converts integer ratios to
exact `fractions.Fraction` values and checks masks, variable
universes, and resource invariants.

`count_asymmetric_boundary` and `count_signed_cnf_crc`
accept the explicit opt-in `left_backend="rust"`.
The original Python code remains the **default and the
independent differential reference**.

## Safety and exactness conditions

- Only declared internal and boundary variable IDs 1..256
  can appear in a row; overlaps, duplicates, invalid parity
  bits and undeclared support bits raise errors.
- The original `max_spectrum_terms` cap remains in effect.
  Excessive Fourier support returns **incomplete**; it is
  never misreported as UNSAT.
- Zero coefficient cancellation, contradictory and dependent
  rows, unconstrained variables, arbitrary-bit-width masks,
  and free internal variables are handled exactly.
- The Rust compiler initially caught an intermediate ownership
  move during pivot insertion; the research branch was
  corrected and then all native/combined CI gates passed.
- This is conventional exact linear algebra plus Fourier
  identities. It is **not a novel complexity theorem** and
  is not yet a Lean-refined kernel.

## Differential and independent verification

The dedicated [R-007 workflow](https://github.com/joeyst8/witnora-core/actions/runs/41741754634)
passed:

- **20 Rust tests**, including hundreds of small random complete
  truth-table checks for the number of compatible internal
  assignments at every boundary assignment.
- **Four new Python integration tests:** **280** seeded random
  exact projected-row and complete Fourier-dictionary
  comparisons against Python; **160** randomized full left
  affine + right CNF count comparisons against Python and
  exhaustive model counts; malformed/budget/256-bit controls;
  and a **12-case combined native source pipeline** exercising
  R-003/004 preprocessor, R-005 XOR extraction, R-007
  left Fourier and R-006 right coefficients together against
  the unchanged all-Python path and analytic model counts.
- **15/15** independent Ganak counts and closed-form
  mathematical counts across n=12,24,48,60.

The original 105-test Python source regression suite remains
separate from the new native extension tests.

## Timed left-stage comparison

Each controlled instance has `groups` disjoint 3-variable
positive OR clauses, and q local even XOR equations.
For each XOR block, an additional explicit internal variable
is constrained by **two** affine rows; eliminating it yields
the 3-variable parity equation and leaves no free internal
completions. The exact model count is
`3^q * 7^(groups-q)`.

The **right coefficient backend was native Rust in both arms**.
Both timed measurements include left affine projection, sparse
Fourier, right CNF normalization, native inclusion-exclusion,
and model assembly. They deliberately exclude preprocessing
and source XOR extraction to isolate R-007. Three timed
repetitions per arm on one hosted runner; median milliseconds:

| n | q projected XOR blocks | Python left (ms) | Rust left (ms) | Rust/Python |
|---:|---:|---:|---:|---:|
| 12 | 0 | 0.0806 | 0.0733 | 0.909 |
| 12 | 1 | 0.1697 | 0.1071 | 0.631 |
| 12 | 3 | 0.2449 | 0.1458 | 0.595 |
| 24 | 0 | 0.1327 | 0.1491 | 1.124 |
| 24 | 1 | 0.1760 | 0.1443 | 0.820 |
| 24 | 3 | 0.3349 | 0.2614 | 0.781 |
| 24 | 6 | 0.8836 | 0.5139 | 0.582 |
| 48 | 0 | 0.1038 | 0.1081 | 1.041 |
| 48 | 1 | 0.1229 | 0.1167 | 0.950 |
| 48 | 3 | 0.2651 | 0.1963 | 0.740 |
| 48 | 6 | 0.9605 | 0.6094 | 0.634 |
| 60 | 0 | 0.1731 | 0.1190 | 0.687 |
| 60 | 1 | 0.1427 | 0.1467 | 1.028 |
| 60 | 3 | 0.2759 | 0.1881 | 0.682 |
| 60 | 6 | 1.0272 | 0.6572 | 0.640 |

With n=60, q=6, both methods and Ganak counted exactly
**494,424,620,106,921 models**. That instance improved ~1.56×
using Rust for the left projection/spectrum. The n=24
q=0 and n=60 q=1 cases exhibited slight Rust slowdowns:
PyO3 conversion and startup work can exceed the saved
arithmetic on trivial spectra. This is an important negative
control, not an anomaly to hide.

These numbers are short (sub-ms) hosted-runner timings with
only three repeats. They are **not stable population-level
speed estimates** and show no general SAT/#SAT advantage.

## Migration checkpoint and next target

Native Rust now covers the principal bounded computational
primitives in the W-CRC branch:

- Exact source normalization and adaptive selection (R-003/004)
- Complete small-XOR source extraction (R-005)
- Exact affine projection and left sparse Fourier (R-007)
- Exact right CNF Walsh inclusion-exclusion (R-006)
- Indexed variable elimination for independent small-width
  components (R-001/002)

Python still orchestrates the stages, transports masks across
several PyO3 calls, and owns important alternative coefficient
backends, source separator discovery, experiment orchestration
and differential references. **R-008 should measure a fused
native source-to-count entry point** and compare memory and
full preparation time, avoiding repeated Python↔Rust data
serialization. Neither the finite read-only queue nor this
native port can independently invent or certify a new theorem.
