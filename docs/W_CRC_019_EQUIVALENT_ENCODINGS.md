# W-CRC-019: Identical satisfying sets, different CNF encodings

Status: **105 green Python regression tests**, **28/28 independently
checked Ganak exact counts of two models**; **25/28 Witnora source
counts exact**, **3/28 safely incomplete**; small-case full
truth-table equivalence for each source variant. Both the full
W-CRC CI and dedicated sequential research queue passed.

Full green W-CRC CI:
https://github.com/joeyst8/witnora-core/actions/runs/41727822505

Dedicated queue and raw logs:
https://github.com/joeyst8/witnora-core/actions/runs/41727817224

## Critical objection from external alien-math audit

A statistic of the *solution set* S cannot, by itself, determine the
wall-clock runtime of a specified SAT/#SAT implementation over arbitrary
CNF representations. The same satisfying assignments can be
represented by syntactically very different formulas. Runtime depends
on the **pair (encoding, algorithm)**, plus implementation and
hardware. A semantic measure can still be useful if an algorithm
class, representation model and predictive task are specified.

We do **not** assert the unproven universal negative hypothesis that
no scalar semantic invariant could ever predict performance.
Instead, challenge the prototype with explicit equivalent encodings.

## Families and exact-preserving variants

Two n-variable families from W-CRC-018 are tested independently.
Each family always has **exactly two satisfying assignments**.
Different variants within one family have exactly the **same set S**
in {0,1}^n, with no auxiliary variables.

1. **Pairwise forcing** baseline: for all u<v, clauses
   `(u OR v)` and `(u OR NOT v)` imply u. There are
   n(n-1) clauses and a complete K_n primal graph.
   - `shuffled`: same clause multiset, randomized order.
   - `entailed_units`: add all n-1 positive units already implied
     by the baseline; S is unchanged and the graph stays K_n.
   - `consensus_reduced`: retain only the n-1 units, a logically
     equivalent CNF with an edgeless primal graph. This is a
     **precomputed equivalent representation**: its cost of
     derivation is NOT charged to the measured solver time.
2. **Pairwise parity** baseline: for all u<v, exact two-clause XOR
   equivalence with a fixed seeded bit pattern, giving a pair of
   complementary global solutions. K_n and n(n-1) source clauses.
   - `shuffled`: same source clauses in randomized order.
   - `entailed_wide`: append up to 12 three-literal clauses,
     each obtained by adding a literal to a baseline two-clause.
     Every new clause is implied by the original source; S is
     exactly unchanged and the primal graph remains K_n.

Tests exhaustively compare the **entire source model set** for
every variant at n=6/8/10, and compare semantic profiles at n=8.
Larger cases use the elementary Boolean equivalence identities
to establish source-set invariance, plus independent Ganak counts.

## 28 source-to-count and independent engine controls

Sizes n=8,16,32,64, seven variants per size = **28 cases**.
Every one of 28 Ganak 2.8.0 experiments returned exactly 2 models.
Witnora returned exact 2 on 25 cases, including all baselines;
the other three returned `INCOMPLETE_BUDGET` **without inventing
a model count or UNSAT conclusion**.

| n | Forcing base Witnora ms | Same S: consensus-reduced ms | Same graph, extra implied units | Ganak baseline engine ms |
|---:|---:|---:|---|---:|
| 8 | 1.1052 | 0.0773 | exact, 2.7333 ms | 4.8341 |
| 16 | 6.0944 | 0.1288 | incomplete | 5.3545 |
| 32 | 43.7934 | 0.2411 | incomplete | 6.2034 |
| 64 | 336.0094 | 0.5453 | incomplete | 8.8153 |

At n=64, the compressed CNF is roughly **616x faster** for the
existing Witnora source count (336.0094 / 0.5453 ms) but is
**not the same input size**: 4,032 source clauses versus 63
units. This is a deliberately stark example of representation
sensitivity, **not an end-to-end preprocessing speedup**.

The `shuffled` forcing n=64 case remained exact at 340.6403 ms;
the `entailed_units` forcing case had 4,095 clauses and failed
closed. Ganak completed all variants, with three engine timings
per case. Forcing n=64 baseline had Ganak median 8.8153 ms;
unit-augmented 9.8518 ms; reduced 5.0776 ms. Differences
near measurement noise should not be overinterpreted.

For the parity family at n=64:
- baseline Witnora 33.7591 ms, Ganak engine 21.5332 ms;
- shuffled 34.5071 ms, Ganak engine 24.6181 ms;
- 12 extra entailed wide clauses 32.3094 ms, Ganak 21.8884 ms.

All three were exact with the same two assignments. No
consistent speed change should be inferred merely from adding
redundancy to this parity family.

## Exact reason for the important three budget refusals

The source adapter converts each explicit unit in the
`entailed_units` encoding to an affine equation. The
`_sparse_fourier` expansion in
`witnora_core/crc_boundary.py` doubles the number of active
Fourier modes for each independent unit constraint, up to
2^(n-1) modes for the n-1 units.

The prototype's default limit is **4,096 Fourier terms**.
For n=16, 2^15 = 32,768 exceeds this limit, so the
routine correctly returns `None`, propagated as
`INCOMPLETE_BUDGET`. The same mechanism applies to n=32/64.

This is a **representation-induced algorithmic pathology**:
adding logically implied, seemingly useful unit clauses makes
the exact asymmetric Fourier backend refuse an otherwise
easy family. It is not a proof of intrinsic semantic hardness.
An ordinary source-level Boolean unit/consensus simplifier
could eliminate this representation before Fourier expansion,
but its correctness, full cost, and effect on other families
must be experimentally checked.

## Scope and implications

This pilot falsifies any unqualified claim that Witnora's
current implementation time is determined only by source
model-set semantics. It says nothing universal about every
solver, representation, or intrinsic problem complexity.

The broad negative assertion that *no* efficient semantic
invariant can predict time across all encodings is not proved.
"Predict" and the algorithm/encoding distributions must be
defined before a statistical hypothesis can be falsified.

The external audit's suggestion to match variable-clause
incidence while freely adding redundant clauses is internally
inconsistent without an explicit compensating construction:
the added clauses generally modify the incidence representation.

Next reviewed investigation: implement a **source-checkable
consensus simplifier** which recognizes
`(A OR b) AND (A OR NOT b) == A` before asymmetrically
projecting the formula; evaluate total preprocessing plus
exact-count wall time, prove small source-model equivalence
with exhaustive checks, add adversarial controls, and
compare with unchanged independent Ganak. This uses
**standard Boolean resolution**, not alien mathematics.

Research branch `research/w-crc-001-asymmetric-v1`,
draft PR #122; TC-063 draft #121 is unchanged. There is
no new theorem or P-versus-NP claim.
