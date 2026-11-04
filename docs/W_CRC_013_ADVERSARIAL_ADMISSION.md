# W-CRC-013: Heterogeneous #SAT and adversarial admission study

Status: **81 green tests, 5/12 W-CRC admissions, 12/12 independent
Ganak completions, explicit witness-search cost**.

GitHub Actions independent CI:
https://github.com/joeyst8/witnora-core/actions/runs/41719072620

## Question

Were W-CRC-012's 11–32× wins artifacts of the trivial all-positive
one/two-hub formulas and a pre-supplied SAT witness?

**Partly.** A more heterogeneous repeated signed 3-variable block
family still admits exact cutset counting and has a smaller but
substantial measured advantage even after independent SAT witness
search. But all seven unsymmetric connected/random controls are
**incomplete by the intended budgets**, while Ganak counts them.

## Explicit source witness time

Every case uses PySAT/Glucose3 to **find** an actual satisfying source
assignment and times that solver invocation. W-CRC then verifies the
source witness, discovers the minimum cut, and counts exactly under
the same fixed resource limits. The reported combined time is
one observed Glucose3 source-SAT runtime **plus** the median of two
complete Python W-CRC counts. That is more realistic than W-CRC-012,
but it is not a rigorously matched repeated end-to-end competition;
the witness component is one sample and may be reuse-specific.

For positive admissions, Ganak's engine timing is separately
reported and excludes process startup. Ganak also uses a
probabilistic-cache default; the positive family is independently
checked against an analytic exact formula.

## Structured but heterogeneous family

For each three-variable block (a,b,c) and one shared hub h, use
signed clauses:

- (a OR b)
- (NOT a OR c)
- (b OR NOT c)
- (h OR a)
- (h OR b)

These clauses are not a uniform all-positive orbit; each local block
has an actual signed constraint pattern. The full primal graph
connects all blocks via h. Given h=1, each block has **3** models.
Given h=0, each block has exactly **1** model. The full k-block
formula therefore has exactly **3^k + 1** models, independent of
the implementation. An all-ones source witness exists, but this
benchmark actually asks Glucose3 to find one.

| Blocks | Variables | W-CRC cutset ms | Witness SAT ms | Combined ms | Ganak engine ms | Combined / Ganak |
|---:|---:|---:|---:|---:|---:|---:|
| 4 | 13 | 0.2965 | 0.0986 | 0.3951 | 5.8461 | 0.068 |
| 8 | 25 | 0.4945 | 0.2029 | 0.6974 | 6.4199 | 0.109 |
| 16 | 49 | 0.9895 | 0.2165 | 1.2060 | 17.1749 | 0.070 |
| 32 | 97 | 1.9701 | 0.3092 | 2.2793 | 22.3330 | 0.102 |
| 64 | 193 | 4.0992 | 0.3548 | 4.4540 | 33.9082 | 0.131 |

The five exact model counts `3^k+1` matched both W-CRC and Ganak.
The measured ratio is approximately 7.6–14.8× lower combined time
for W-CRC in this restricted family. This is a pilot, not a
general external solver ranking.

## Seven adversarial/negative controls

| Case | Variables | W-CRC admission | Ganak engine ms | Ganak models |
|---|---:|---|---:|---:|
| positive 2-CNF chain | 16 | component > budget | 6.3496 | 2584 |
| positive 2-CNF ring | 16 | no admissible group separator | 6.1620 | 2207 |
| positive 2-CNF chain | 32 | component > budget | 25.0381 | 5702887 |
| positive 2-CNF ring | 32 | no admissible group separator | 30.1823 | 4870847 |
| planted random signed 3-CNF | 16 | no admitted cut | 9.5255 | 838 |
| planted random signed 3-CNF | 24 | no admitted cut | 73.1435 | 6242 |
| planted random signed 3-CNF | 32 | no admitted cut | 341.4995 | 192643 |

All seven W-CRC calls returned the explicit `INCOMPLETE_BUDGET`
status and never claimed SAT/UNSAT or a model count.
Every independent Ganak call produced an exact integer; no timeout.
The ring tests have a direct endpoint clause, so no vertex
separator excluding endpoint variables can remove that edge.
In chain tests a cut exists but the remaining component is much
larger than the 8-variable exhaustive local-count cap.

## Correctness and reproducibility

Implementation: `scripts/benchmark_crc_adversarial.py`,
`tests/test_crc_adversarial_benchmark.py`. Two new unit tests
verify signed-block closed-form counts against independent brute
full-source enumeration and deliberately reject large chain/ring
residuals. The whole workflow passed **81 Python test methods**.
All 12 independent Ganak runs completed; all 5 W-CRC admitted
cases agreed with Ganak and the analytic integer counts.

GitHub run:
https://github.com/joeyst8/witnora-core/actions/runs/41719072620

## Scientific interpretation and prior art

Cutset conditioning and component factorization are established
graphical-model inference strategies (for example, Mateescu and
Dechter, *AND/OR Cutset Conditioning*):
https://ics.uci.edu/~dechter/publications/r121.pdf

This work does not solve an unrestricted SAT/#SAT instance efficiently
in the worst case and does not imply P≠NP. It establishes that a
small-separator, small-residual-component method is **both useful
and limited** in reproducible source-level conditions. The research
challenge remains to construct a sound and less conservative
structural measure that predicts successful decomposition beyond
the already known primal graph-cut criterion, or to prove something
genuinely new about constraint interactions.

## Next research candidates

- Replace brute-force residual component counting with a bounded
  exact dynamic-programming/variable-elimination backend; a
  *path or ring* with large component size but low treewidth would
  then become tractable without claiming a new complexity theorem.
- Benchmark real/random 3-CNF with a separate SAT witness cost and
  realistic admission rates.
- Compare against additional independent counters, more seeds,
  and stronger baseline preprocessing.
