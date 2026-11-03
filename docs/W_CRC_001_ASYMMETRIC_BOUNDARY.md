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

## 2026-11-03 milestone: exact source-CNF XOR-gadget recognition

The new source adapter, witnora_core/crc_source.py, accepts signed CNF
and lifts a clause set into a GF(2) affine equation **only if all**
canonical clauses encoding a k-variable XOR (k=1,2,3) are present.
For support variables (v_1,...,v_k) and rhs b, these clauses forbid
exactly the 2^(k-1) assignments of opposite parity. Their conjunction
is equivalent to the extracted affine equation for every assignment.

All unrecognized clauses remain on the right. Tautologies/duplicate
clauses are removed; invalid zero or out-of-range literals are rejected,
including those inside tautologies. Variables in residual clauses form
the boundary. All other source variables are internal and are counted
through exact affine projection and its free-variable multiplier.

Seven additional unittest methods pass, including:

- k=1,2,3 canonical XOR gadgets, both parity values;
- a deliberately incomplete gadget, correctly not extracted;
- empty-clause, duplication, tautology, malformed-input and budget controls;
- **400 independently exhaustive original-source-CNF random cases**,
  including planted canonical gadgets plus random extra clauses;
- a **118-variable source CNF** encoding global parity over 60 boundary
  variables via 59 recognized small XOR equations, plus 20 nonlinear
  three-literal OR clauses. Its exact count is (7^20 + 1)/2 with only
  two left Fourier coefficients and 20 right CNF components.

**Total in-memory Python dry run:** 16 unittest methods passed,
including 800 randomly generated formulas with independent exhaustive
count comparisons, plus 80 all-mode Fourier coefficient controls.
A dedicated GitHub Actions workflow now checks both test modules.

This remains a restricted, structurally easy source-CNF pilot.
The gadget recognition and boundary interaction are mathematically exact,
but universal CPython-to-Lean refinement, harder overlapping nonlinear
regions, measured advantage over existing Witnora counters, and general
SAT improvements remain unproved/unmeasured.

## 2026-11-03 first source-to-count benchmark (measured, not a theorem)

Reproducible runner: python -m scripts.benchmark_crc_vs_anf
CI: https://github.com/joeyst8/witnora-core/actions/runs/41694701619
(result **success**, all 16 Python tests + both benchmark families).

Both methods receive the **same original signed CNF**. W-CRC-001
includes its source gadget extraction and coefficient-query time.
The unchanged structured ANF baseline includes source violation-ANF
construction and exact structured counting. Times are median of three
single-process Python calls; no cross-run statistical interval or
separate external solver comparison has been performed.

| Boundary bits | Source vars | Clauses | Exact #models | CRC ms | ANF ms | Ratio ANF/CRC |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 6 | 10 | 20 | 25 | 0.2380 | 1.5673 | 6.585 |
| 9 | 16 | 33 | 171 | 0.3298 | 4.1040 | 12.444 |
| 12 | 22 | 46 | 1201 | 0.3946 | 9.8888 | 25.060 |
| 15 | 28 | 59 | 8403 | 0.5245 | 12.4170 | 23.674 |
| 18 | 34 | 72 | 58825 | 0.5848 | 17.8827 | 30.579 |

W-CRC-001 recovered a **two-term projected parity response** for
each deliberately factorable global XOR chain, while the right-hand
nonlinear clauses form independent size-three regions. This is a
meaningful improvement over the project's existing generic ANF
counter on **these constructed inputs**, but the structure is already
tractable by known Gaussian-elimination and decomposition techniques.
It is not evidence of novelty over parity-aware SAT/#SAT solvers.

**Adversarial controls (dense random 3-CNF):**

- 10 variables, 42 clauses, seed 20261103: CRC returned
  INCOMPLETE_BUDGET, while ANF exactly reported UNSAT (0 models)
  in 2.1317 ms (40 states).
- 12 variables, 51 clauses, seed 20261104: CRC returned
  INCOMPLETE_BUDGET, while ANF exactly returned 4 models in
  3.0371 ms (56 states).

The W-CRC-001 source adapter is deliberately **not** an arbitrary-CNF
replacement. The next hurdle is overlapping nonlinear components:
the current right-side inclusion-exclusion oracle may still require
2^m work when m clauses share variables. A truly substantive
algorithmic contribution must improve that case without moving the
exponential cost into extraction, oracle lookup or proof generation.

**Claim boundary:** no Lean correctness proof for this Python module,
no universal CPython refinement, no industrial SAT benchmark advantage,
no general runtime upper bound, and no P-vs-NP conclusion.
