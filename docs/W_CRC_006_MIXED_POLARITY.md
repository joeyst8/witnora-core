# W-CRC-006: bounded mixed-polarity Walsh correction

**Research status:** opt-in exact prototype, draft PR #122.
The full W-CRC source/coefficients/independent-Ganak workflow passed:
https://github.com/joeyst8/witnora-core/actions/runs/41711999357 .
This is an application of standard Fourier–Walsh convolution to a
restricted almost-symmetric CNF class. It is **not** a general SAT
algorithm, a new complexity-class result, or a Lean-kernel proof.

## Exact algebraic identity

Let F0 be a coherent rank-r uniform near-complete CNF, r in {2,3},
with bounded missing-support set M. Let E be a small set of signed
exceptional clauses, involving only variables A. The full Boolean
model indicator factors *exactly* as

    F(x) = 1[F0(x)] * 1[E(x_A)] = f(x) g(x_A).

Use normalized Fourier–Walsh coefficients on the full boundary B,
with character chi_T(x)=(-1)^popcount(T & x). If g is extended from
A to B, its coefficient is nonzero only on U subseteq A. Therefore

    Fourier(F,T) = SUM_{U subseteq A}
                     Fourier_A(g,U) * Fourier_B(f,T XOR U).

The small coefficients Fourier_A(g,U) are computed by evaluating
only 2^|A| assignments to exceptional variables and running an
exact integer fast Walsh–Hadamard transform. All requested base
coefficients Fourier_B(f,T XOR U) come from W-CRC-005's exact
bounded defect-hypergraph oracle. The affine-left projection and
final integer model-count composition remain unchanged.

The majority-polarity test gives a deterministic coherent reference
pattern for each active variable; if an occurrence tie prevents a
unique reference, the recognizer fails closed. A source clause
inconsistent with that reference is treated as an exception, never
silently discarded. The base subset must independently pass the
complete/uniform support/defect recognizer.

## Precise scope and costs

Default explicit resource bounds:
- At most **2** exceptional sign clauses.
- At most **6** distinct exceptional variables.
- At most **4,096** requested base Fourier modes.
- At most **6** missing supports in the coherent base, with the
  existing W-CRC-005 defect-union enumeration cap.

For fixed rank r and defect count d, the construction costs
source recognition O(C(n,r)), up to 2^(r*d) candidate high-flip
supports, an O(|A| 2^|A|) Walsh transform, and at most
O(Q 2^|A|) base-mode requests for Q modes. Integer bit costs,
source extraction, and exact fraction arithmetic remain charged.
The exponential dependence on d and |A| is explicit. Overbudget,
incoherent, nonuniform or unsupported sources return None.

Implementation:
- witnora_core/crc_conflict_oracle.py
- Opt-in enable_conflict_oracle in crc_boundary.py and crc_source.py
- tests/test_crc_conflict_oracle.py
- scripts/benchmark_crc_conflict.py

Old coherent d<=r and W-CRC-005 d<=6 options remain separately
opt-in; default source solver behavior is unchanged. Neither an
exceptional source clause nor a high-order missing support is
assumed to be affine or an UNSAT certificate.

## Independent finite verification

The CI source control gate passed **50 Python unittest methods**,
including 20 randomized all-Walsh-mode differential cases at 6/7
variables with random coherent signs, four missing triples, and
one/two exceptional sign clauses. The independent oracle enumerates
every source assignment. Separate tests cover a removed-and-replaced
reference clause, parity-left composition, free boundary variables,
more-than-two exceptions, invalid modes, and hard resource limits.

The full source-to-count benchmark used n=8/12/20/28, dispersed or
tetrahedral missing four-triple patterns, and one or two additional
opposite-sign clauses on selected source supports: **16/16** CRC
integer counts matched independent Ganak. The coherent-only
backend remained out of scope for every test. CI:
https://github.com/joeyst8/witnora-core/actions/runs/41711999357 .

| n | Exceptional clauses | Original pattern | CRC source-to-count median (ms) | Ganak engine (ms) | Models |
| ---: | ---: | --- | ---: | ---: | ---: |
| 8 | 1 | dispersed | 1.4581 | 12.4096 | 40 |
| 8 | 2 | dispersed | 2.2804 | 12.6275 | 38 |
| 8 | 1 | tetrahedron | 1.2208 | 12.6884 | 41 |
| 8 | 2 | tetrahedron | 1.2785 | 12.7044 | 40 |
| 12 | 1 | dispersed | 3.8760 | 28.4321 | 82 |
| 12 | 2 | dispersed | 4.0365 | 27.7616 | 80 |
| 12 | 1 | tetrahedron | 3.7787 | 28.5245 | 83 |
| 12 | 2 | tetrahedron | 3.8181 | 27.4244 | 82 |
| 20 | 1 | dispersed | 18.5970 | 180.0237 | 214 |
| 20 | 2 | dispersed | 18.6721 | 224.3305 | 212 |
| 20 | 1 | tetrahedron | 18.9169 | 180.7753 | 215 |
| 20 | 2 | tetrahedron | 18.6458 | 179.9638 | 214 |
| 28 | 1 | dispersed | 55.6851 | 835.5188 | 410 |
| 28 | 2 | dispersed | 53.9077 | 841.5039 | 408 |
| 28 | 1 | tetrahedron | 56.1650 | 834.9825 | 411 |
| 28 | 2 | tetrahedron | 55.2462 | 844.3768 | 410 |

Observed Ganak-engine/CRC ratios were 5.54–15.61x **on these
specially structured synthetic formulas**. CRC measurements are
two repeats and include source extraction/normalization; Ganak
engine measurements include source loading, are one run per case,
and use its probabilistic default component cache. This sample
does not establish industrial solver superiority, statistically
stable speedups, or general-case complexity advantages. Ganak is
independent corroboration of integer results, not a Lean proof.

## Existing mathematical context

- Fourier expansion and convolution of functions on the Boolean
  cube are standard; see Ryan O'Donnell, *Analysis of Boolean
  Functions*: https://arxiv.org/abs/2105.10386 .
- Lifted counting with cardinality constraints is established;
  e.g. https://ojs.aaai.org/index.php/AAAI/article/view/20525 .
- Hypergraph missing-support enumeration is classical combinatorics.
  The exact composition here is an experimental engineering use
  of those tools, not an asserted new theorem.

## Remaining trust and next falsification

1. A Lean theorem for the exact hypergraph high-flip set identity
   and the normalized Walsh product/convolution identity is open.
2. A source-signed-to-Lean refinement of the majority-polarity,
   exception selection, fast transform, and serialized answer is open.
3. The current family assumes a near-complete coherent core; sources
   with many exceptions, high missing-support density, mixed clause
   ranks or no such core can defeat the bounded recognizer.
4. The apparent gain may disappear when |A| grows, because the
   required Walsh queries increase as 2^|A|; benchmark held-out
   adversarial exception clusters, including interacting clauses
   and matched source sizes, against more independent #SAT solvers.

**Next W-CRC-007:** measure whether exception variables can be
partitioned into weakly coupled clusters and their Fourier
correction factors composed without generating all 2^|A| modes.
A counterexample should be recorded if shared coherent-base
correlations destroy the apparent independence. Compare total
runtime/memory and state-budget failures before enabling anything
by default.

No result here proves P=NP, P!=NP, generic polynomial SAT, or
universal CPython-to-Lean execution equivalence.
