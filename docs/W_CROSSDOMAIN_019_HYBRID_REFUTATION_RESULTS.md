# W-CROSSDOMAIN-019: hybrid covariance and GF(2) refutation

Frozen protocol: `docs/W_CROSSDOMAIN_019_HYBRID_REFUTATION_PROTOCOL.md`.

## Motivation and exact proof boundary

W-018 proved 32/32 embedded complete eight-pattern contradictions with an
integer vector in the kernel of the signed clause-violation covariance.
It could not detect the 32 separate four-XOR parity-cycle contradictions.

W-019 combines two **sound, incomplete** UNSAT proof procedures:

1. An integer vector `w` with `K*w=0` and `sum(w)!=0` proves that the
   weighted violated-clause sum is a fixed nonzero constant on every
   Boolean assignment. This rules out a satisfying assignment.
2. A recovered XOR equation on variables `(a,b,c)` requires all four
   CNF clauses that forbid the opposite parity, and carries their exact
   source clause indices. XORing a selected subset of these equations
   to `0=1` proves inconsistency. The Rust verifier replays every
   claimed equation against the original CNF and the final GF(2) sum.

If both checks fail, the outcome is `no_certificate`, **not SAT**.
Neither mechanism is new by itself; the value of this pilot is exact
source-backed routing, independent verification, and a controlled
comparison between complementary proof families.

## Prospective cohorts and independent preflight

The W-019 generator uses new fixed seeds, 32 cases per family, plus
deterministic permutations of all variable names, per-variable sign
flips, and shuffled clause order. These preserve truth but prevent
hardcoding clause positions or sign patterns.

| Frozen family | SAT cases | UNSAT cases | Independent standalone XOR contradiction screen |
| --- | ---: | ---: | ---: |
| Fresh planted 48 | 32 | 0 | 0 |
| Fresh uniform 48 | 26 | 6 | 0 |
| Hidden eight-pattern core 56 | 0 | 32 | 32 |
| Hidden four-equation XOR cycle 64 | 0 | 32 | 32 |

The SAT/UNSAT counts above are from exhaustive independent Python truth
tables, not an inference from the certificate algorithm. The parity
column is from a separate independent GF(2) screen and must be
confirmed by source-backed Rust proof witnesses before use as evidence.

## Rust result and verification status

| Family | Verified covariance proofs | Verified XOR proofs | No certificate |
| --- | ---: | ---: | ---: |
| Fresh planted 48 | 0 | 0 | 32 |
| Fresh uniform 48 | 0 | 0 | 32 |
| Hidden eight-pattern core 56 | 32 | 0 | 0 |
| Hidden four-equation XOR cycle 64 | 0 | 32 | 0 |

- [x] Rust library tests, source replay and full 128-case release audit pass.
- [x] Independent Python controls (`0`, `1`, `31`) compare generators,
  truth status and replay every emitted witness.
- [x] No false UNSAT certificates on any SAT case.
- [x] Focused and full-native GitHub CI both pass.

Source commit: `32f9bc32409c436d4d4dbd5e4759c582afe93253`.
Focused GitHub Actions run `42102801072`; full-native run `42102800804`.
Both completed **successfully** on 2026-11-05. The focused job built the
release executable, passed two independent Python tests, and audited all
128 cases. The native Rust regression workflow also passed.

**Crucial limitation of this benchmark:** an independent XOR-only screen
also detects the 32 embedded eight-pattern contradictions, in addition
to the 32 parity-cycle contradictions. Thus the covariance route has
**zero incremental UNSAT coverage versus this XOR-only baseline** on
these particular families. The router selects covariance first for the
eight-pattern cases; that does not establish a unique benefit. Six
naturally UNSAT random-boundary cases remain without a certificate.

## Post-result research lead, not part of the frozen benchmark

Consider these eight 3-clauses:

`(1,2,3), (1,2,-3), (1,-2,4), (1,-2,-4),
(-1,2,5), (-1,2,-5), (-1,-2,6), (-1,-2,-6)`.

For every assignment, **exactly one** of these clauses is violated.
Therefore the all-ones weight vector has `K*w=0` and sum 8, proving
UNSAT. The four clause-triple groups each contain only two sign patterns;
the W019 four-pattern XOR extractor sees **zero equations**. This
8-clause example was checked exhaustively over all 4096 assignments,
but has not yet been submitted as a prospective Rust benchmark.

It is mathematically just a disguised contradictory **2-CNF** (each
pair eliminates its padding variable by ordinary resolution), so it
does *not* demonstrate superiority over standard SAT preprocessing.
It does establish a useful separation between W019's two restricted
certificate formats. W020 should prospectively test this separation,
compare against ordinary resolution/2-SAT, and seek harder cases where
one mathematical representation provides an independent advantage.

## Interpretation

This pilot should demonstrate *complementarity*, not a claim of general
SAT-solving completeness. Any remaining random UNSAT cases demand
stronger proofs, potentially involving higher-degree polynomial
multipliers or interaction between extracted XOR constraints and
ordinary CNF propagation. Performance and solver competitiveness
remain separate, falsifiable future research questions.
