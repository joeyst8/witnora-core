# W-CRC-010: Verified conditional independence after source conditioning

Status: **sound restricted certificate; 66 green Python tests; 8 positive
star-family benchmark cases; not a general #SAT speedup**.

GitHub Actions:
https://github.com/joeyst8/witnora-core/actions/runs/41716282998

## The question

Can a small set of variables S explain the interaction between A and B,
even when the original source primal graph is connected?

**Yes, conditionally.** Fix a concrete value S=s that is witnessed by
a satisfying *full source assignment*. Simplify every **signed** source
clause under S=s. A satisfied clause disappears; each surviving clause
loses its S literals. Build the residual primal graph. If its connected
components touching A do not touch B, the conditional source model set
factors and the uniform model distribution obeys

P(A=a,B=b | S=s) = P(A=a | S=s) P(B=b | S=s)

for all assignments a,b, provided P(S=s)>0. The independently checked
source satisfying witness ensures the conditioning event is supported.

This follows standard factorization-implies-conditional-independence
results for undirected graphical models, not a new general mathematical
theorem. See David Sontag's MIT lecture 4:
https://people.csail.mit.edu/dsontag/courses/pgm12/slides/lecture4.pdf

It does **not** imply unconditional A ⟂ B. For example, the 3-variable
equivalence chain X1=X2=X3 has correlated endpoints, yet conditioned
on X2=1 both endpoints are fixed and independent. When the residual
graph remains connected, the implementation returns *inconclusive*,
never a claim of conditional dependence.

## Implementation

- `witnora_core/crc_conditional_independence.py`
- `tests/test_crc_conditional_independence.py`
- `scripts/benchmark_crc_conditional_independence.py`

Input includes actual source clauses, group sets A/B, a candidate
separator S, and an offered full satisfying bit mask. The checker
validates the full mask's range, the source-relative residual signed
clauses, and every resulting witness condition. It refuses empty
remaining clauses / any false witness by returning `None`.
Invalid group, separator or mask declarations raise `ValueError`.
The current implementation does **not** discover S automatically and
does **not** find a SAT witness.

## Correctness and benchmark

The full W-CRC workflow passed **66 Python tests**. Five new W-CRC-010
methods include a connected XOR-like equality chain, both truth
assignments for signed separators, a source clause disappearing when
conditioned, invalid/UNSAT controls, and 140 random planted-satisfiable
small formulas. On every emitted positive certificate in the seeded
random tests, an exhaustive independent rank-one conditional model
table agreed.

The benchmark uses n-1 clauses `(x_i OR h)`, one shared hub h,
and left/right groups of non-hub variables. All full source graphs
are connected. Fixing hub h=1 deletes every clause. Fixing h=0
reduces them to separate positive units. Both cases have a verified
source-model witness, both certify conditional independence, and
neither certifies unconditional independence.

| n | Clauses | h | Original graph audit ms | Conditional audit ms | Residual clauses |
|---:|---:|---:|---:|---:|---:|
| 16 | 15 | 0 | 0.0521 | 0.0408 | 15 |
| 16 | 15 | 1 | 0.0320 | 0.0235 | 0 |
| 64 | 63 | 0 | 0.1264 | 0.1187 | 63 |
| 64 | 63 | 1 | 0.1064 | 0.0639 | 0 |
| 128 | 127 | 0 | 0.1916 | 0.2470 | 127 |
| 128 | 127 | 1 | 0.1843 | 0.1281 | 0 |
| 256 | 255 | 0 | 0.3922 | 0.5205 | 255 |
| 256 | 255 | 1 | 0.3870 | 0.2541 | 0 |

Times: median of 2 runs under the same GitHub Actions environment,
not a statistically meaningful comparison. The 'original graph'
audit and conditional audit establish different statements; their
times are shown only as cost context, *not* as solver speedups.
No independent Ganak benchmark was needed for the graph certificate
claim; the 140 random small-case conditional tables were exhaustively
enumerated as an independent semantic control.

## Key limitation and successor

Finding a candidate small S is an **additional computational problem**.
W-CRC-011 will attempt a bounded minimum vertex separator of the
normalized source primal graph, validate it by an independent reachability
check, and pass it to W-CRC-010. A vertex separator is only a sufficient
candidate: conditioning can remove clauses and create even smaller
semantic separators. The result remains source-bound and witness-bound,
not a general SAT algorithm or a resolution of P versus NP.
