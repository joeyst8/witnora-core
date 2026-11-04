# W-CRC-009: Source-graph sufficient independence certificate

Status: **exact limited structural theorem, verified; no general speedup**.
Research branch: `research/w-crc-001-asymmetric-v1`.
Independent test run: [GitHub Actions #41715482029](https://github.com/joeyst8/witnora-core/actions/runs/41715482029).

## Question

Can we avoid testing every cross-group Fourier moment when the source
clauses are obviously separated? Answer: yes for an explicit syntactic
sufficient condition, but this was **not faster** for larger dense
instances in the small fixed-group pilot.

## Exact certificate

Normalize each signed source clause, dropping duplicates and tautologies;
an empty clause is unsatisfiable. On source variables, build the primal
graph with one clique per clause scope. A witness bit mask is checked
against **every normalized signed clause**. If no connected component
meets both nonempty disjoint group sets A and B, then the source model
set factors as a Cartesian product of its primal-graph components.
For a satisfiable source with the uniform probability distribution over
its models, A and B are therefore independent. This is the familiar
factorization-implies-independence theorem of graphical models, not a
new mathematical result; see the MIT lecture notes:

https://people.csail.mit.edu/dsontag/courses/pgm12/slides/lecture4.pdf

The result `separated=False` means **inconclusive**. A connected graph
may still encode independent variables due to redundant clauses or
forced values. A rejected/invalid witness results in `None`; an
unsatisfiable source cannot be certified by this method.

Implementation:
- `witnora_core/crc_structural_independence.py`
- `tests/test_crc_structural_independence.py`
- `scripts/benchmark_crc_structural_independence.py`

The construction scans the touched variable bits of each clause and
uses union-find; it is linear up to DSU inverse-Ackermann factors in
the normalized literal count, plus hashing/sorting normalization
overhead. It is **not a SAT oracle**: a satisfying witness must already
have been supplied by another method.

## Soundness tests and independent comparison

Six new tests cover disconnected and connected positive/negative
examples, invalid/forged witness rejection, 140 randomly planted
satisfiable sources and exhaustive rank-one table checks, and malformed
inputs. The entire W-CRC workflow passed **61 Python tests**.
Eight fixed-four-group-bit cases n=8,12,20,28 returned the same
independence verdict as the exact W-CRC-008 Fourier-moment audit.

## GitHub Actions measured median times

All times are ms, two repeats per method. A positive structural result
only certifies independence; no model-counting speedup was measured.

| n | Source graph | Source clauses | Structural audit | 16-mode Fourier audit | Structural / Fourier | Result |
|---:|---|---:|---:|---:|---:|---|
| 8 | separated | 20 | 0.0739 | 0.1814 | 0.407 | independent |
| 8 | connected | 56 | 0.1266 | 0.1767 | 0.716 | inconclusive (Fourier: dependent) |
| 12 | separated | 120 | 0.2970 | 0.2978 | 0.997 | independent |
| 12 | connected | 220 | 0.4505 | 0.4160 | 1.083 | inconclusive (Fourier: dependent) |
| 20 | separated | 816 | 1.6685 | 1.3136 | 1.270 | independent |
| 20 | connected | 1140 | 2.2160 | 1.7669 | 1.254 | inconclusive (Fourier: dependent) |
| 28 | separated | 2600 | 6.7935 | 4.2022 | 1.617 | independent |
| 28 | connected | 3276 | 6.7095 | 5.2188 | 1.286 | inconclusive (Fourier: dependent) |

The Fourier baseline was an unusually favorable source-specific exact
backend querying only 16 modes, not a generic #SAT solver. Conversely,
normalization and graph construction are charged to the structural
method. Measurements are small single-environment pilot observations,
not an asymptotic comparison or statistically significant ranking.
In connected cases, the Fourier audit proves dependence, whereas the
structural audit correctly refuses to decide.

## Finding and successor

W-CRC-009 gives a sound **fast-in-principle source-bound certificate**,
but a dense-graph preprocessing cost can negate any practical
advantage over an already efficient restricted-family Fourier backend.
The real structural opportunity is a **small separator S**: groups
A and B may be connected in the original graph yet independent
*conditional on a fixed supported assignment to S*. This is proposed
for W-CRC-010, with source witness validation and exhaustive
conditional-table controls. No P≠NP or general polynomial-time SAT
claim follows from these experiments.
