# W-CRC-004: exact defect-bounded orbit/cardinality response

Status: mathematical and Python experiment, opt-in on draft PR #122.
This is a **known-style lifted cardinality optimization**, not a
new solution of general SAT or P vs NP.

## The structural idea

Conventional primal graph width can be huge even when every clause is
governed by a simple permutation symmetry. Define a signed rank-r
uniform CNF for r in {2,3}:

- There are n active Boolean variables.
- Every clause has width r and the chosen sign of each variable is
  consistent across all its occurrences.
- Among all C(n,r) r-subsets, at most d<=r clause supports are
  *missing*; all the others occur exactly (duplicates are normalized).

Let b be the assignment satisfying all chosen literal polarities and
let J be the set of variables whose bits are flipped relative to b.
The CNF is satisfied exactly if |J|<r, or if |J|=r and that subset
is one of the d missing clause supports. A set |J|>=r+1 contains
at least r+1 distinct r-subsets, but only d<=r are absent, so at
least one present clause is violated. This establishes both directions
of the characterization.

Thus the model count over the active variables is:

    N = SUM_(j=0)^(r-1) C(n,j) + d.

For a requested Walsh mask T, let t=|T intersect active| and
B=popcount(T & b). The unnormalized signed model count is:

    W(T) = (-1)^B * (
      SUM_(j=0)^(r-1) SUM_(a=0)^j (-1)^a C(t,a) C(n-t,j-a)
      + SUM_(H missing) (-1)^popcount(T & H)
    ).

The binomial coefficient is zero outside its normal support. The
coefficient is W(T)/2^n if there are no free boundary variables.
For free boundary bits, multiply W by 2^(#free) if T excludes them,
and use 0 if T meets the free bits, before dividing by 2^(#boundary).

## Why recognition is efficient

Normalize original signed clauses to their falsifying bit masks.
Check uniform width and fixed polarity for every active variable,
then enumerate all C(n,r) *supports*, not all 2^n Boolean assignments.
Compare support membership, collecting missing combinations; reject if
d>r. Since the source already has C(n,r)-d clauses, verification is
linear in source size plus enumerating O(n^r) possible supports.
For fixed r<=3 this is polynomial.

Each requested exact Walsh coefficient then takes
O(r^2 + d) binomial/sign operations (ignoring big-integer bit costs),
with no variable branching. The left affine spectrum is combined by
W-CRC-001's original exact contraction identity.

Implementation:
- `witnora_core/crc_orbit_oracle.py`: exact recognizer and
  arbitrary requested Fourier masks, including free boundary vars.
- `count_asymmetric_boundary(..., enable_orbit_oracle=True)`
  and source adapter opt in to the new backend. The old IE/Shannon
  path and its budgets remain the default.
- `tests/test_crc_orbit_oracle.py`: all-mode exhaustive Walsh
  controls on random polarities/missing-clause sets, parity
  composition, free-variable modes, negative controls.
- `scripts/benchmark_crc_orbit.py`: dense 3-CNF at
  12/20/28/36 vars with 0/2/3 omissions, plus canonical XOR
  gadgets forcing odd parity, against independent Ganak and
  budgeted Shannon recursion.

## Structural scope, novelty and adverse cases

This is a very narrow family: it needs a nearly complete uniform
clause hypergraph and globally compatible signs. Arbitrary random
3-CNF, conflicting literal polarities, or d>r defects fail closed
to the existing exact fallback or INCOMPLETE_BUDGET. This must never
be read as compressing *all* dense constraints.

The identities are elementary cardinality/character-sum formulas;
their use in Witnora's source-CNF-to-selected-Fourier pipeline is
engineering, not an established novel complexity theorem. Density
alone is not difficulty. Recognition cost is charged to total
source-to-count time.

Potential future hypothesis: can a bounded number of *local
symmetry defects* be retained symbolically without requiring the
full C(n,r) input pattern? If yes, characterize the defect parameter
and prove a fixed-parameter time bound. Otherwise reject the idea.

## Lean proof obligations (not yet completed)

1. Soundness of normalized-clause sign and support checks.
2. All r-subset coverage and the bound d<=r imply the exact
   flip-set characterization.
3. Exact signed Walsh/Krawtchouk binomial identity.
4. Free-variable and normalization factors.
5. Composition with source XOR extraction and affine projection.
6. Checked source evidence for accepted results, plus separate
   Python-to-Lean refinement if making execution-level claims.

Finite Python and Ganak tests do not substitute for these universal
kernel-checked statements.


## First measured results — 2026-11-03

GitHub Actions: https://github.com/joeyst8/witnora-core/actions/runs/41703441943
All **36 Python unittest methods passed**. Every one of the 8
dense-nonlinear benchmark cases was exact and independently matched
Ganak's integer count; the opt-in backend was explicitly reported as
`orbit_cardinality`. The ordinary 3,000-state Shannon backend
also completed all eight cases.

| Boundary k | Right nonlinear clauses (defects) | Orbit source-to-count | Shannon source-to-count | Ganak count, including CNF load |
| --- | ---: | ---: | ---: | ---: |
| 12 | 220 (0) | 3.8825 ms | 8.3319 ms | 28.6442 ms |
| 20 | 1,138 (2) | 21.4526 ms | 77.0867 ms | 183.7662 ms |
| 28 | 3,274 (2) | 52.9791 ms | 323.4890 ms | 849.9806 ms |
| 36 | 7,137 (3) | 124.1389 ms | 1,010.6001 ms | 2,990.0322 ms |

An additional 4 source-CNF instances contained a canonical XOR
chain enforcing odd global boundary parity. Those instances had
262, 1,212, 3,380, and 7,275 total clauses, and 22, 38, 54, and
70 source variables. All four matched Ganak; orbit runtimes were
3.9563, 18.3714, 56.9256 and 130.7492 ms respectively,
while the Shannon fallback took 9.0856, 80.9879, 319.1857
and 1,004.4497 ms.

These are very small samples, **not calibrated microbenchmarks**:
two orbit timings per case, one Shannon and one Ganak engine
timing, all on one CI runner. Ganak's default cache has a documented
low collision-error probability, so this integer comparison is
independent evidence, not formal verification. The source-to-count
timings include parsing/extracting canonical XORs where applicable
and recognizing the dense orbit pattern. There is no claim that
all densely overlapping formulas admit a compact signature.

**Hostile audit:** This result exploits a complete/near-complete
signed uniform hypergraph. Its satisfying assignments can be
characterized by the number of flipped literals. That is familiar
lifted cardinality reasoning, not a new source of polynomial-time
general SAT algorithms. For example, see the AAAI 2022 paper on
closed-form lifted counting with cardinality constraints:
https://ojs.aaai.org/index.php/AAAI/article/view/20525 .
The Walsh signed-sum expressions are related to established
Krawtchouk/Hamming-weight identities.

**Next falsification:** perturb the symmetry in *more* than r
places and vary signs across overlapping clauses. The exact
recognizer must reject these, leaving a complete fallback. Measure
whether an extension based on a small set of perturbed variables
improves runtime, with an explicit exponential parameter bound in
the perturbation set. If it merely renames known lifted inference,
report that connection explicitly.
