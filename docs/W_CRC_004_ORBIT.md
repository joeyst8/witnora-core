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
