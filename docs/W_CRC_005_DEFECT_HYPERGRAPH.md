# W-CRC-005: exact bounded defect-hypergraph coefficient response

**Status:** experimental, opt-in, draft PR #122. CI green on
[run 41710683455](https://github.com/joeyst8/witnora-core/actions/runs/41710683455).
The result is lifted hypergraph counting with a bounded defect parameter,
not a new general-purpose #SAT algorithm or a P-versus-NP result.

## The exact high-order identity

Consider an r-uniform CNF, with r in {2,3}, containing all r-subset
clauses on n active variables except a missing-support family M of size
d. Each variable has one globally coherent literal polarity. Let b be
the assignment satisfying all these polarities and J the set of bits
flipped relative to b.

An assignment satisfies the source precisely when:

    (|J| < r)  OR  (every r-subset of J is in M).

For |J|>=r, every vertex in J belongs to at least one r-subset
contained in J, so every variable in J occurs in some missing support.
Thus J lies in U=union(M) with |U|<=r*d. Define

    H(M) = {J subseteq U: |J|>=r and C(J,r) subseteq M}.

This includes nontrivial high-order cases: four missing triangle
supports can form all faces of a tetrahedron, admitting its
four-variable flip set. Four dispersed missing triples need not.

For Walsh mask T on the active source variables, t=|T| and coherent
reference assignment b, the unnormalized signed model sum is exactly

    W(T)=(-1)^popcount(T & b) * [
         SUM_{j=0}^{r-1} SUM_{a=0}^{j}
              (-1)^a C(t,a)C(n-t,j-a)
         + SUM_{J in H(M)} (-1)^popcount(T & J)
    ].

The code includes the correct free-boundary Fourier-zero rule and
normalizes by 2^(total boundary variables). It computes only the masks
requested by the already exact affine-left Fourier spectrum.

## Algorithm and declared cost

1. Read actual normalized signed clauses and require uniform r in
   {2,3} and globally coherent polarity. Reject conflicts.
2. Check all C(n,r) source supports, reconstruct missing M, and reject
   d>6 by default.
3. Enumerate subsets of U only. Enforce default caps |U|<=18 and
   2^|U|<=262144, returning None on excess.
4. Test each candidate high-flip support against the missing
   hypergraph, then answer requested exact Walsh masks by the formula.
5. A separate opt-in source-CNF adapter combines these coefficients
   with existing exact affine extraction. Unrecognized or overbudget
   instances retain the previous bounded fallback; they are not
   pronounced satisfiable or unsatisfiable.

With r fixed, the support scan costs O(C(n,r)); the defect enumeration
is at most 2^(r*d) candidate subsets with further polynomial subset
tests, plus requested-mode evaluation and arbitrary-precision integer
arithmetic. This is fixed-parameter in d, on a family whose input
already contains nearly all rank-r clauses. It does not offer a cheap
certificate for arbitrary sparse or conflicting-polarity CNF.

Implementation:
- witnora_core/crc_defect_oracle.py
- opt-in enable_defect_oracle flag in crc_boundary.py and crc_source.py
- tests/test_crc_defect_oracle.py
- scripts/benchmark_crc_defect.py

The old W-CRC-004 d<=r orbit recognizer and all production defaults
are unchanged. When both optional backends are enabled, the older
lower-defect cardinality response has priority.

## Independent verification and falsification

The updated W-CRC GitHub workflow passed **47 Python unittest
methods** and the full existing Ganak comparison suite:
https://github.com/joeyst8/witnora-core/actions/runs/41710683455 .

New tests independently enumerate all 2^n assignments for every
requested Walsh mask in 27 randomly generated small coherent
rank-three instances with four, five or six missing supports, random
global polarities, and free-variable effects. Further cases cover
the exact tetrahedron/dispersed discrepancy, a rank-two missing
triangle with a valid three-bit flip, parity-left composition,
rejected contradictory signs, invalid masks and hard budget caps.

The source-to-count pilot freezes eight dense 3-CNF cases with four
missing supports and different overlap geometry. Every result matched
the elementary exact count and independent Ganak's integer answer.
The original d<=3 oracle rejected every case as out of scope.

| n | Clauses | Missing pattern | Exact #models | New CRC median (ms) | Ganak engine (ms) |
| ---: | ---: | --- | ---: | ---: | ---: |
| 8 | 52 | dispersed | 41 | 0.8984 | 10.6920 |
| 8 | 52 | tetrahedral | 42 | 1.0411 | 10.9539 |
| 12 | 216 | dispersed | 83 | 3.3016 | 26.6121 |
| 12 | 216 | tetrahedral | 84 | 3.2607 | 26.3563 |
| 20 | 1136 | dispersed | 215 | 16.1362 | 186.4132 |
| 20 | 1136 | tetrahedral | 216 | 16.2408 | 190.6863 |
| 28 | 3272 | dispersed | 411 | 46.6891 | 841.5800 |
| 28 | 3272 | tetrahedral | 412 | 49.5975 | 848.7609 |

The observed Ganak-engine / new-CRC ratios range about 8.1x to
18.0x **only on these synthetic lifted-cardinality cases**. CRC
times include source extraction and recognition; Ganak engine timings
include its source loading; each CRC median has two timing repeats,
and Ganak one, on one CI runner. Ganak's default cache is a
probabilistic exact-counting baseline, not a machine-checked proof.
These are not industrial or calibrated general-purpose comparisons.

## Trust boundary and next falsification

- This is a mathematical paper argument plus Python differential tests,
  **not** a Lean kernel proof of the defect-hypergraph identity.
- Python extraction, normalized signs, defect enumeration and Walsh
  arithmetic have no universal Python-to-Lean refinement proof.
- The exponential parameter d matters: increasing the number of
  defects toward n^r can destroy the advantage. Any budget exhaustion
  must return an incomplete result, not infer UNSAT.
- Mixed inconsistent literal signs remain unsupported by this exact
  recognizer.

**Next W-CRC-006 hypothesis:** allow a bounded set of s
conflicting-polarity clauses. Remove their coherent reference
supports into the defect set; let A be the at most r*s variables
touched by the exceptions. Use the exactly computed base Walsh
coefficients on all T subseteq A and an inverse Walsh transform to
obtain exact counts conditioned on every assignment to A. Retain only
assignments satisfying the exceptional clauses, and sum. Its naive
parameter cost is exponential in d and |A|, with an explicit cap.
This should be tested against adversarial interacting sign defects
and Ganak before claiming any improvement.

The mathematical ingredients (hypergraph cliques, Krawtchouk
sums, Walsh transforms and lifted model counting) are established
ideas. The experiment is a precise integration and restricted-family
engineering result, not an established novel complexity theorem.
