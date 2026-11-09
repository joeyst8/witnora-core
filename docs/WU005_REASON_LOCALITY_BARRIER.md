# WU-005 — Reason-locality barrier and global unit-XOR baseline

Status: **bounded computational result plus an elementary algebraic family argument**.
Do not interpret as a new complexity lower bound or as a solver performance result.

## Established starting point and unknown

Paul Beame and Glenn Sun, *Extending CDCL to Disjunctions of Parity
Equations*, SAT 2026, DOI [10.4230/LIPIcs.SAT.2026.5](https://doi.org/10.4230/LIPIcs.SAT.2026.5)
define affine resolution / CDCL(⊕) and a checkable parity proof framework.
Their discussions of parity learning and minimization motivate exploring
certified rank-one strengthening of the learned clause. WU-001–004
established our basic bounded affine/RUP(⊕) testbed; this milestone tests
**our own** proposed reason-guided selection, not a published algorithm's
completeness.

## Question

For a sound clause with falsity subspace `F` of rank `d`, can intrinsic
intersections with source reason spaces nominate useful rank-`d−1`
subspaces without trying every one of the `2^d−1` hyperplanes?

Hypothesis H5: for each original reason falsity space `G`, form
`K = F ∩ G` using Gaussian elimination. If `codim_F K=1`, nominate `K`.
If `codim_F K=2`, nominate the three containing hyperplanes; otherwise
skip. Deduplicate *subspaces*, not generating row lists. Independently
RUP(⊕)-check every candidate. All of this is coordinate/gauge invariant.

## Protocol, work metric and observed results

Implemented in Rust, `rust/witnora-ve/src/bin/wu005_guided_hyperplanes.rs`.
The diagnostic exact oracle enumerates **hyperplanes in rank at most 10**;
it does not enumerate Boolean assignments. A separate RUP(⊕) fixed-point
replay verifies candidate entailment. `scans` counts replay clause visits,
including failed certificates: it is **not wall time** or a production
solver performance measure.

| Target and input | Exact hyperplanes | RUP certified | H5 proposed | H5 certified | H5 missed | Replay scans exact/H5 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| WU-004 four-clause CNF calibration | 7 | 4 | 5 | 4 | 0 | 39 / 31 |
| Two-edge native unit-XOR chain | 7 | 3 | 0 | 0 | 3 | 22 / 0 |

The first line is a small *favorable calibration*, not a speedup claim;
the second is a *counterexample to completeness*. Zero scans on H5's
second line merely means it did not try to prove anything.

### Explicit family of counterexamples

For any integer `m≥2`, use variables `x,y,a,z1,...,z(m−1)` and a target
clause whose falsifying assignments satisfy `x=1, y=1, a=1`. Its falsity
subspace is `F=span(x=1,y=1,a=1)`, rank three. The input consists of the
`m` **unit parity constraints** along the path

`x -- z1 -- z2 -- ... -- z(m−1) -- y`.

Every edge demands equal endpoint values (`u⊕v=0`) except the last,
which demands unequal values (`u⊕v=1`). Their joint consequence is
`x⊕y=1`. Consequently, the target clause is valid, and there are three
rank-two hyperplanes of `F` containing the equation `x⊕y=0`; all three
pass the independent RUP(⊕) replay.

**Why every proper reason subset fails the intersection test.**
Express any linear combination of the path-edge equations with GF(2)
coefficients `c1,...,cm`. To remove all internal auxiliary variables,
the coefficient of each internal vertex must vanish, so
`c1=c2=...=cm`. The only nonzero choice uses **all m edges**. For a
proper subset there is no nonzero combination free of auxiliary
variables. Adding the RHS constant equation `1` cannot cancel any
auxiliary variable; and `1` itself is not in consistent `F`. Thus

`F ∩ span(reason falsity rows in S, 1) = {0}` for every proper `S`.

The full set instead has a nonzero intersection, equal to
`span(x⊕y=0)` after the constant RHS row is accounted for.
Therefore any proposal rule that **only** takes anchors from
intersections with at most a fixed `k` source reasons, and declines
anchors of codimension more than two, is incomplete for the family
when `m>k`. This is a limitation of that specified proposer class,
**not** a lower bound against unrestricted SAT algorithms, CDCL(⊕),
or global linear algebra.

### Rust bounded tests

For every `m=2,...,6`, the exact oracle finds three certified rank-two
subspaces. A `k`-local proposer using *all reason subsets of size at
most k* finds **zero** for every `k<m`, and all three for `k=m`.
Pairwise composition succeeds when `m=2` but fails when `m=3`.
The tests also independently verify the intersection argument for every
reason subset (up to `m=6`), verify the three proposed clauses with
RUP(⊕), and test H5 gauge invariance over all 168 bases of the rank-three
target on the two base fixtures. **No Boolean assignments are enumerated.**

## Constructive escape from the locality barrier

In the **unit-XOR fragment only**, collect every asserted parity
equation (equivalently, the falsity rows and RHS `1`), eliminate them
*globally* over GF(2), then intersect their span with `F` **once**.
On all five tested paths, this single global Gaussian calculation
nominates the same three certified hyperplanes, without enumerating
reason subsets. The algebraic operation is polynomial in matrix size,
although RUP checking and actual SAT behavior still have separate costs.

This global rule **must not** be applied verbatim to general disjunctive
XNF clauses: a clause of multiple parity equations does not assert each
equation individually. Any extension must preserve the disjunctive
semantics and provide independently checkable proof steps.

## Decision and next experiment

**Reject H5 as a complete method.** Retain it as an inexpensive,
potentially useful heuristic only if independent, nontrivial benchmarks
justify its cost. For WU-006, compare sound *propagation-conditional*
global affine closure for XNF with its RUP certificate cost on carefully
separated unit-XOR, disjunctive-XNF, and CNF instances. First derive or
find the semantic rule in existing literature; then test it against an
exact bounded oracle, adversarial cases, and production baseline metrics.
Do not transfer the unit-XOR closure rule to arbitrary disjunctive XNF.

## Reproduce

From `rust/witnora-ve` with Rust/Cargo available:

```sh
cargo test --bin wu005_guided_hyperplanes
cargo run --quiet --bin wu005_guided_hyperplanes
cargo test --release --all-targets --quiet
```
