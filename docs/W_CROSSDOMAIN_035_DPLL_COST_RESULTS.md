# W035 — Same-host cost comparison: weighted spectral LP versus explicit DPLL

## Provenance and design

- Frozen protocol: `docs/W_CROSSDOMAIN_035_DPLL_COST_PROTOCOL.md`.
- Successful GitHub Actions evidence run: [42162185377](https://github.com/joeyst8/witnora-core/actions/runs/42162185377).
- Source code commit: `41a2b93e5f4d4a6ee2d8fddf5387555e25841018`.
- Source formulas and exact truth table classifications: original W034 200-case collection; decompressed W034 SHA256 `261ca8144fc27799c6790012157c42986be37d0c0378f0dbdac7a98d8681a8c7`.
- Complete 1,200 original same-machine algorithm-only timings, scan counts and results: `research/results/w035_cost_raw.json.gz` (compressed SHA256 `d074e115f6c8f5860226b583ad21a5c0c5c02549de0078708a6e395c554d577b`, decompressed SHA256 `4451e2c8621c85aeca47e1e330cb29023acfe0920b3ed1a249a67d808c280e1a`).
- Two Python arms: explicit reference DPLL with unit propagation versus SciPy HiGHS weighted Fourier LP plus exact integer source-certificate verification. Three repeats, rotating arm order. Same-host matched per-case comparisons. **This is not a benchmark against production Kissat.**

## Complete measured result

| Matched metric | Reference Python DPLL | W034 weighted spectral LP |
| --- | ---: | ---: |
| Source cases | 200 | 200 |
| Timed invocations | 600 | 600 |
| Median of per-case median algorithm wall times | **0.0567 ms** | **3.1964 ms** |
| Cases arm was faster than other | **200 / 200** | **0 / 200** |
| Median source-clause scans per invocation | **165.5** | N/A (spectral terms/LP rows instead) |

The **median paired per-case LP/DPLL cost ratio was 53.52×**. The ratio of the two aggregate median times is not the statistic reported above; paired ratios are used to avoid mismatched case weights.

| Clauses per 5-variable formula | Median paired LP/DPLL time ratio |
| ---: | ---: |
| 12 | 92.2× |
| 16 | 62.9× |
| 20 | 57.3× |
| 24 | 44.9× |
| 32 | 41.0× |

DPLL returned the exhaustively verified SAT/UNSAT truth on every case; W034 returned its expected exact certificate/no-certificate status on every invocation. All comparisons include the weighted LP's exact integer audit and DPLL's explicit source-clause scans. These tiny timing measurements remain sensitive to runtime noise, but the observed margin was large and the direction unanimous.

## What this falsifies, and what it does not

1. **W034's strong proof coverage (74/77 tiny UNSAT formulas) is not an immediate computational advantage.** Even a transparent Python DPLL reference solved all 200 cases much faster.
2. W034's output is a sound sufficient UNSAT certificate on those 74 cases, but the candidate-generation procedure is computationally expensive relative to the problems.
3. The comparison does not establish a large-instance performance relation, because `n=5` makes exhaustive reasoning cheap; the DPLL reference is not optimized Kissat, and this does not evaluate source extraction on independent industrial CNFs.
4. This suggests W036 should focus on **constant-cost gating, local proof extraction, and amortizing/or avoiding LP work**, with held-out external families. At a minimum, any proposed feature or proof search should be evaluated against end-to-end baseline cost, not predictive accuracy or certificate count alone.

W035 does not imply anything about the resolution of P versus NP.
