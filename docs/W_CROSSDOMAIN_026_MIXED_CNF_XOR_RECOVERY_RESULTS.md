# W-CROSSDOMAIN-026: exact 3-XOR recovery under controlled mixed-CNF noise

## Results

**W026 PASS** on the [preregistered protocol](W_CROSSDOMAIN_026_MIXED_CNF_XOR_RECOVERY_PROTOCOL.md), committed independently before implementation as 4b8f79c1d4842e4858f0f37fc3b7eb68af2a705c.

Rust source reconstruction and an independently implemented Python source/seed audit passed on [GitHub CI run 42134893383](https://github.com/joeyst8/witnora-core/actions/runs/42134893383), commit 869f5029c424bf7d1b24afac9fdc67baff78fffe.

This experiment checks source-level extraction accuracy and clause-visit accounting. It **does not establish a solver speedup, a new algorithm, or a result about P versus NP**.

## Experimental controls

- Each partner has five exactly encoded 3-XOR source equations (20 core clauses).
- 16 seeded distractor configurations per noise level, six levels, 96 total cases.
- Same distractors on SAT and UNSAT partner; every added distractor satisfied by a planted SAT witness.
- Each new distractor triple support is unique and excluded from the five core triples, so no distraction group contains four clauses. This restriction makes the test deliberately favorable to exact source grouping.
- Domain of 64 variables, 3 literals per clause, no units.

## Exact results by noise level

| Added ordinary clauses per partner (D) | Clauses scanned per full extraction | Indexed variable-triple supports | Registered cases | XOR blocks found on each side | Incorrect source detection |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 0 | 20 | 5 | 16 | 5 | 0 |
| 32 | 52 | 37 | 16 | 5 | 0 |
| 256 | 276 | 261 | 16 | 5 | 0 |
| 1,024 | 1,044 | 1,029 | 16 | 5 | 0 |
| 4,096 | 4,116 | 4,101 | 16 | 5 | 0 |
| 8,192 | 8,212 | 8,197 | 16 | 5 | 0 |

Every SAT partner passed its planted complete assignment. Source-recovered GF(2) elimination remained consistent on every SAT partner and produced a valid contradiction on every UNSAT partner.

Because W024's first/second-order moments are identical between the two core formulas and W026 adds the **same** clauses to each partner, those low-order statistics remain identical by additivity, even when distractors mention source variables. The indexed higher-order XOR cycle still differs.

## Cost accounting, without speedup inference

For D=8,192, a full source scan visits 8,212 clauses.

| Queries over same frozen formula | Rebuild/scan clauses each time | One cached index: initial full-scan clause visits |
| ---: | ---: | ---: |
| 1 | 8,212 | 8,212 |
| 2 | 16,424 | 8,212 |
| 8 | 65,696 | 8,212 |
| 32 | 262,784 | 8,212 |

These are **counts of full-clause visits**, not CPU timings. Building and consulting the index also costs time and memory. Reusing an index can avoid repeated full scans, but does **not** mean the resulting SAT solver is faster. In particular, a single query adds an index cost while saving no full scan.

## Reproduction

- [Rust extraction and generator](../rust/witnora-ve/src/bin/witnora_mixed_xor_recovery.rs).
- [Independent Python audit](../tests/test_mixed_xor_recovery_rust.py).
- [Original Rust raw JSON, 96 cases](../research/results/w026_mixed_xor_recovery.json).
- [GitHub Actions: green Rust and independent source reconstruction](https://github.com/joeyst8/witnora-core/actions/runs/42134893383).
- [Immutable run artifact](https://github.com/joeyst8/witnora-core/actions/runs/42134893383/artifacts/13465725193), ZIP digest SHA-256 988dfc09a83b0270f66ae9c5a83c41bcc69e845ab307a3388d3fd323e10006fd.

## Honest interpretation and W027

Our representation can recover known XOR parity when a complete clause quartet is explicitly present, even after adding 8,192 nonmatching clauses. **But synthetic single-clause-per-support distractors were designed so no false XOR grouping is possible.** There is no measured generalization to industrial formulas, dense overlaps, non-XOR noise with repeated supports, or partial/obfuscated XOR encodings.

Existing systems such as CryptoMiniSat already combine CNF and XOR reasoning. For relevance to real P versus NP research, W027 should compare Rust extraction overhead plus actual solving cost against pinned modern CDCL and CDCL/XOR solvers, using heldout source-origin benchmarks and a robust error/timeout protocol. A new representation is useful only if its additional information can be exploited at worthwhile computational cost.

Relevant prior work: [Soos et al., Tinted, Detached, and Lazy CNF-XOR Solving (CAV 2020)](https://www.cs.toronto.edu/~meel/Papers/cav20-sgm.pdf).
