# W-CRC-001 — exact asymmetric boundary contraction (prototype)

**Date:** 2026-11-03. **Parent:** TC-063 draft PR #121,
branch `formal/g14-python-seen-enqueue-v121`.

This is a **bounded experimental #SAT counter**, not a complete CNF solver,
not a polynomial-time algorithm, and not a Lean-verified source-refinement.
The repository's independent TC-063 restricted-family logical theorem and
certificate gates are unchanged.

## Hypothesis

A formula split over boundary variables S has regions with exact response
functions g_L(s), g_R(s). The exact model count is

    #F = sum_(s in {0,1}^S) g_L(s) g_R(s)
       = 2^|S| sum_(T subset S) Fourier(g_L,T) Fourier(g_R,T).

If one side has a small support of Fourier coefficients, only those
coefficients need to be **queried** on the other side. This can avoid
constructing 2^|S| boundary assignments **when both** (a) a sparse spectrum
can be produced efficiently and (b) the required coefficient queries can
be answered efficiently. Neither property holds for arbitrary CNF.

This identity, Fourier-domain variable elimination and affine decision
representations have substantial prior art. The hypothesis is an
**adaptive, exact construction and performance hypothesis**, not a
claim to invent Fourier elimination.

## Implemented input class

`witnora_core/crc_boundary.py` handles:

- A left-hand affine system over GF(2) involving declared internal variables
  and boundary variables. Rows are (integer variable-bit-mask, rhs-in-{0,1}).
- A right-hand CNF containing only boundary literals, including negative
  literals, duplicates, tautologies and an empty contradictory clause.
- No arbitrary nonlinear left region or hidden variables in the right region.
- Positive 1-based variable IDs up to 256; larger sparse IDs must be
  densely relabeled before this **prototype** is called.

The left affine rows are eliminated over internal variables. If the rank
in internal columns is q with p declared internal variables, every
consistent boundary assignment has 2^(p-q) internal completions.
The projected independent boundary conditions have masks M_j and rhs b_j:

    g_L(s) = 2^(p-q) product_j (1 + (-1)^b_j chi_(M_j)(s)) / 2,

where `chi_M(s) = (-1)^parity(M & s)`. This product is expanded
symbolically as a sparse exact Fourier dictionary with a strict term cap.

For the right CNF, let v_C be the indicator that clause C is violated.
Then:

    g_R(s) = product_C (1-v_C(s))
           = sum_(U subset clauses) (-1)^|U| product_(C in U) v_C(s).

Every included subset U either has inconsistent literal-falsifying
assignments (contributes zero), or fixes some boundary-variable set D_U
to a unique value a_U. Its contribution to normalized Fourier mode T is:

    (-1)^|U| * [T subset D_U] * 2^(-|D_U|)
      * (-1)^parity(T & a_U).

Thus, the coefficient oracle does not enumerate boundary assignments.
It first splits right-hand clauses into disjoint variable-scope components.
Each component is expanded separately, so total coefficient work is bounded
by a sum of clause-subset costs, not necessarily the exponential in the
**total** number of clauses. This is an established component-factorization
identity, not a new SAT algorithm. A shared `max_inclusion_subsets` budget
and `max_spectrum_terms` cap fail closed with `None`, never SAT, UNSAT
or a guessed model count.

This is not a worst-case complexity improvement: the right oracle has a
hidden O(sum_i 2^(m_i)) cost for m_i clauses in each scope-connected
component (O(2^m) if all m clauses interact), and sparse expansion can
require O(2^r) terms for r independent left boundary conditions. Converting
general CNF to exact affine responses remains out of scope.

## Reproduced finite checks (read-only dry run)

- 12 boundary variables, even parity left, one wide positive OR clause
  right: 4096 possible boundary assignments, two nonzero left Fourier
  coefficients, two right inclusion-exclusion terms, **2047 models**.
- One internal shared affine variable plus one independent free internal
  variable: projected parity response and **4094 models**.
- Contradictory affine rows and an empty source clause: **zero models**.
- Duplicate literals, tautological clauses, fixed budget exhaustion,
  malformed literal/variable controls.
- **400 seeded randomized small mixed formulas** checked against an
  independently written exhaustive total-assignment oracle.
- **80 seeded CNFs**, each coefficient independently checked for all
  32 modes against explicit Walsh sums.
- A 60-variable parity constraint crossing **20 disjoint 3-literal
  nonlinear clauses**: exact answer `(7^20 + 1)/2` using only **2**
  left Fourier coefficients and **40** total clause-subset terms,
  without enumerating 2^60 assignments. This is a purposely
  factorable class, not evidence of improved general SAT complexity.
- Total: **9 Python unittest methods passed** in the dry run.

These are correctness controls, not benchmark speed claims. They also
do not provide a universal Lean theorem or certify CPython implementation.

## Next measured milestones

1. Add a source-CNF front end with *verified or differentially audited*
   affine extraction, without turning arbitrary parity sketches into
   presumed source equivalence.
2. Compare against `anf_structured_counter` and
   `anf_separator_conditioning` on identical mixed nonlinear formulas.
   Record total time, peak memory, spectrum size, coefficient-query
   work and fallback frequency. Reject regressions on nonmatching classes.
3. Add examples with real internal nonlinear clauses; do not merely
   append one OR clause to a Gaussian-eliminable problem.
4. Independently compare decision SAT against a modern parity-aware SAT
   baseline and exact #SAT against suitable model counters. Decision and
   counting results must be separately reported.
5. If worthwhile, prove in Lean: GF(2) affine projection semantics,
   exact source-literal falsity, subset inclusion-exclusion coefficient
   identity, Walsh orthogonality, and exact bounded acceptor correctness.

**Falsification criterion:** if selected Fourier queries only help
XOR-easy or clause-count-small cases and preprocessing plus queries do
not beat existing exact counters on mixed nonlinear controls, do not
promote W-CRC-001 as a breakthrough.
