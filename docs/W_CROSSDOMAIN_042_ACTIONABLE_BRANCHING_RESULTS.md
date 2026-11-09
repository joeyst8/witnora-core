# W042 — Published 50-variable branching trial: root UP lookahead is vacuous

## Trustworthy execution record

- **Protocol precommitted before outcomes:** `a7d2996019b8ad3086b8cca737fa9553cc3a972e`.
- **Source/implementation commit:** `304ef9f393683b250f6d502f928e528dd4c26b64`.
- **Infrastructure-only PR trigger correction:** `b67f3844ea4341fe0f2fb8b048a30dfb9c258321`. The selection, caps, policies and outcomes are unchanged.
- **Green original published-source GitHub Actions:** [run 42594432742](https://github.com/joeyst8/witnora-core/actions/runs/42594432742), artifact `w042-preregistered-raw` ID `13662871938`.
- Original official SATLIB `uf50-218.tar.gz` SHA256 `a40862e52dfdce78620b037254579a02dbda8182d2879433658a4c15cb00327c` and `uuf50-218.tar.gz` SHA256 `24cc9f492673e0f975fecc56b3a4d8ac21c385cc46205d83b7491a787f43e13d` verified **before** source parsing.
- Exactly the lexicographically first 32 original members of each previously unused archive, 50 variables/218 original 3-literal clauses each, original full clauses preserved in the raw record. Every original source SAT/UNSAT status matched independent PySAT Glucose3; every native SAT answer had an independently checked original-CNF satisfying assignment. Zero budget-censored cases for all four arms.
- Raw repo archive: `research/results/w042_satlib_raw.json.gz`, deterministic gzip SHA256 `b0111420b7398e7ee81e314c5d1c02c4066f59b19116944aee976353b77b2551`; decompressed JSON SHA256 `85a2e86fbbaad4f561b03eff76a6fe7889d93492644fb35f0f4b961fc0f101ee`. The GitHub artifact ZIP digest was `1d2389737a1e7c2c99f80ca346ecb76febb71cb2fbca6e6dce51dfa5f24f85f8`.
- **Independent local replay after the CI run:** compiled the Rust release binary on a different environment, reread both publisher archives, verified with a separate PySAT Glucose3 installation, and reran the same 64 original sources. Every native verdict, clause-visit, node, decision, probe-call and gate-activation count matched CI exactly. Timing was not expected to match across hosts.

## Frozen primary result: **negative**

All measurements use the same native Rust DPLL, cap **2,000,000** clause visits, and three same-process timed repeats per original source and policy. Clause visits include all scan/selection/speculative unit-propagation work. Cross-arm comparisons exclude common source JSON parsing.

| Policy | SAT / UNSAT solved | Total capped clause visits | Summed per-case median wall time | Probe activation |
| --- | --- | ---: | ---: | ---: |
| Fixed degree | 32 / 32 | 3,066,814 | 37.377 ms | 0 |
| Dynamic shortest-clause (M) | 32 / 32 | **2,001,925** | 36.074 ms | 0 |
| Root two-sided lookahead (P) | 32 / 32 | 2,225,157 | 36.781 ms | 64 |
| Gated root lookahead (G) | 32 / 32 | 2,137,957 | 35.462 ms | 39 |

- Primary `G` versus `M`: `(2,001,925 - 2,137,957) / 2,001,925 = -6.79506%` work improvement, i.e. **6.80% more clause visits** with the proposed gate. The predeclared >=10% work-saving criterion is **rejected**.
- 39 activated cases had worse visits; the other 25 tied. Total excess `136,032 = 39 * 16 * 218` source-clause visits. Exactly 16 trial propagations (both signs for eight candidates) per activated instance, with zero additional unit propagation rounds.
- On **all** 39 activated cases, G and M had exactly the same search-tree node count and decision count. The unconditional P policy similarly added precisely `223,232 = 64 * 16 * 218` clause visits. The candidate selection was informationally inactive.
- Per publisher label, M versus G visits were **754,049 versus 795,905 (SAT)** and **1,247,876 versus 1,342,052 (UNSAT)**. Gate activation was 12 SAT cases and 27 UNSAT cases.
- The sum of noisy CI median wall times was ~1.7% smaller for G than M despite larger counted work. This small timing difference is **not** evidence of an effective improvement: the primary joint criterion fails, and the exact counted extra visits expose the wasted work. No statistical timing significance or production-compiler speedup is claimed.

## Simple mathematical explanation — should have been checked first

Let every source clause contain exactly **three distinct literals**, with no
root-level assignments or shorter clauses. Assigning any one variable `x`
can satisfy a clause, shorten an unsatisfied clause to length two, or leave a
clause unchanged. It can create **neither a unit clause nor an empty clause**.
Therefore *ordinary unit propagation after a single root assumption makes zero
additional assignments and cannot produce a conflict*, for either sign of
every candidate variable. In the frozen score, all candidates tie at zero;
the MOMS secondary ordering then picks exactly the original MOMS candidate.

Thus the selected intervention is **provably vacuous** on these pure original
3-CNFs, and the measured extra work is just `2 * 8 * 218` source-clause scans
per activation. This elementary observation is *not* a mathematical novelty.
It should have been ruled out at the protocol-design stage before spending a
benchmark run. It remains valuable as an explicit negative control and an
honest guardrail for future work.

## What would be a scientifically distinct next test?

1. Condition on a state where the residual formula actually contains binary
   clauses, or test deeper coupled assumptions; do not repeat vacuous root
   single-assumption probing on pure width-3 source clauses. Observe the exact
   first unit/conflict opportunity before proposing a policy.
2. Compare any nontrivial conditional inference against strong classical
   MOMS, two-sided UP, and modern CDCL activity/learning heuristics. Credit
   the original IJCAI 1997 lookahead and SAT 2016 LRB literature, rather than
   renaming established techniques as frontier discoveries.
3. Use **different source families**, including structured industrial/crafted
   problems and independently published unsatisfiable instances. Retain
   per-instance timeouts, full overhead, certified results, and held-out
   source provenance. Stop if there is no cost-inclusive advantage.

The experiment teaches **no** new SAT complexity bound or P-versus-NP fact.
