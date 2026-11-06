# W027 Phase-1 exploratory smoke: measured outcome

**Status:** completed, archived. **Study:** W-CROSSDOMAIN-027 Phase 1; not the full W027 preregistered study.

- Protocol frozen before measurements: [Phase-1 protocol](../docs/W_CROSSDOMAIN_027_PHASE1_SMOKE_PROTOCOL.md).
- Run: [GitHub Actions #42136986126](https://github.com/joeyst8/witnora-core/actions/runs/42136986126), successful, UTC 2026-11-06.
- Raw machine-readable timings: [w027_solver_smoke.json](../research/results/w027_solver_smoke.json).
- Solver source revisions: Kissat `8af8e56f174b778aef3aa45af9f739b2a5f492c2` (rel-4.0.4); CryptoMiniSat `03954f7f7815ea3984774c95a66e7c224cd25952` (release/v5.17.0); Rust precheck in workflow-triggering Witnora commit `5cfb6c2ce01283046eb0cbc3a0bacda7f15f99d6`.
- 6 frozen cases × 3 arms × 3 repetitions = **54 executions**; 6-second per-arm wall cap including Witnora preprocessing; 2 GiB process-address-space cap. All arms built and ran. The tiny samples are **not** a reliable cross-machine speedup estimate.

## Per-case median end-to-end wall time

`Witnora` means source-certified Rust 3-XOR contradiction precheck, then *unchanged CNF* into Kissat if no UNSAT certificate. The ratio below is Kissat wall time / Witnora wall time, computed only for cases where both solved all three repeats.

| Frozen case | Kissat | Witnora + Kissat | CryptoMiniSat | Exploratory Kissat/Witnora ratio |
|---|---:|---:|---:|---:|
| Synthetic, 0 distractors, SAT | 4.61 ms | 8.23 ms | 6.49 ms | 0.56× |
| Synthetic, 0 distractors, UNSAT | 5.19 ms | 3.62 ms | 30.41 ms | 1.43× |
| Synthetic, 8,192 distractors, SAT | 10.96 ms | 17.75 ms | 22.32 ms | 0.62× |
| Synthetic, 8,192 distractors, UNSAT | 10.00 ms | 7.73 ms | 24.61 ms | 1.29× |
| External VLSAT2 684/9417, UNSAT | 1095.19 ms | 1098.79 ms | Timeout | 1.00× |
| External VLSAT2 1000/22250, SAT | Timeout | Timeout | Timeout | n/a |

Medians refer only to checked verdicts; **Timeout** means 3/3 censored repetitions and must never be treated as SAT/UNSAT. CMS timed out 3/3 times on the external UNSAT case, while Kissat and Witnora solved it. All three arms timed out 3/3 times on the external SAT case.

## Correctness, source evidence, and interpretation

- **0 incorrect or error verdicts.** Out of 54 invocations, **42 checked SAT/UNSAT verdicts** and **12 censored timeouts**. Independent harness checks validated returned SAT models against the original CNF clauses and reconstructed source-indexed XOR contradiction evidence.
- Witnora produced valid `UNSAT_CERTIFIED` source clauses on **6/6 synthetic UNSAT runs** (both distraction levels). It passed the **6 synthetic SAT runs** to Kissat, which returned independently checked SAT models. All 6 external Witnora runs returned `NO_CERTIFICATE`, found zero exact 3-XOR quartets, and then relied on unchanged-CNF Kissat.
- The synthetic UNSAT cases were about **1.43×** and **1.29×** quicker than Kissat in these specific medians because Rust short-circuited using XOR inconsistency, while synthetic SAT cases were slower (**0.56×** and **0.62×** the Kissat/Witnora ratio) because prechecking could not certify SAT and still incurred process launch plus scanning overhead.
- On one external VLSAT2 UNSAT instance, Rust preprocessing added ~4–5 ms to a ~1.1 s Kissat proof; the median difference was ~3.6 ms, not evidence of useful generalization.
- CryptoMiniSat ran in all six cases; its external SAT and UNSAT cases were censored as specified. Its small synthetic timings varied. Do not interpret these limited CMS comparisons as broad relative solver performance.

**Finding:** An exact source-derived XOR certificate can reduce *end-to-end computation on constructed contradictory instances*, while the same indiscriminate precheck harms SAT cases. This phenomenon is consistent with established XOR reasoning in SAT solvers. The new practical question is whether a cheap structure gate or in-process implementation can reduce preprocessing cost without losing completeness/soundness.

**What is not established:** No novel P=NP argument; no hardness-class claim; no large-scale solver performance improvement; no inference of speedup on outside-of-distribution CNF. This pilot is not the preregistered full W027 study (96 synthetic pairs, eight external VLSAT2 files, and near-XOR adversarial decoys).

## Next falsification-oriented work

1. Implement a **constant/low-cost gate** (do not launch the Rust precheck on CNFs without plausible complete XOR quartet patterns). Preserve fallback to original CNF; never treat absence of a certificate as SAT.
2. Add near-XOR decoys, including one deleted/replaced clause in an apparent quartet, to prove there are **no false UNSAT shortcuts**.
3. Run full W027 at preregistered scale with complete CPU/memory accounting, solver source pins, repeats, timeouts and holdouts; report gains and losses by stratum rather than a cherry-picked aggregate.

