# W027 full preregistered solver comparison — measured results

**Status:** Completed, CI green. [GitHub Actions run 42143620646](https://github.com/joeyst8/witnora-core/actions/runs/42143620646), job 127649681791. All conclusions below refer only to the frozen W027 study.

## Frozen protocol and provenance

- 204 distinct CNFs: 192 matched W026 synthetic XOR (96 SAT, 96 UNSAT), 8 official external VLSAT2 cases, 4 deterministic planted-SAT near-XOR negative controls.
- 3 arms per CNF: Kissat 4.0.4 (`8af8e56f174b778aef3aa45af9f739b2a5f492c2`), source-certified Rust Witnora XOR precheck followed by unchanged-CNF Kissat where no certificate, and CryptoMiniSat 5.17 (`03954f7f7815ea3984774c95a66e7c224cd25952`).
- 3 repeats per arm, interleaved order: 1,836 timed invocations. 30-second end-to-end timeout and 2GiB per invocation. CI completed successfully on AMD EPYC 7763 runner, Rust 1.99.1.
- Raw unmodified per-invocation JSON: [`research/results/w027_full_solver_measurements.json`](../research/results/w027_full_solver_measurements.json), SHA-256 `405492f47924e23feae041752a5ff6a14d1c2e62e6b4419d6fcf07155968a544`; source run artifact `w027-full-solver-measurements` retained 90 days.
- Machine-produced preregistered paired bootstrap calculation: [`research/results/w027_full_break_even.json`](../research/results/w027_full_break_even.json), code [`scripts/analyze_w027_break_even.py`](../scripts/analyze_w027_break_even.py), preregistered before full run completed.

## Primary outcomes

| Stratum | CNFs | Kissat solved / attempted | Witnora+Kissat solved / attempted | CryptoMiniSat solved / attempted | Paired comparisons |
| --- | ---: | ---: | ---: | ---: | --- |
| Synthetic XOR (96 SAT, 96 UNSAT) | 192 | 576/576 | 576/576 | 576/576 | Witnora wins all 96 UNSAT and loses all 96 SAT cases |
| Official external VLSAT2 | 8 | 9/24 | 9/24 | 0/24 | 3 jointly solved, Witnora wins 1 and loses 2; 5 joint timeouts |
| Adversarial near-XOR SAT controls | 4 | 12/12 | 12/12 | 12/12 | Witnora loses 4/4 |

All 1,836 rows are present. There are 1,782 solved invocations and 54 timeout invocations (all on external instances), with no reported errors or incorrect SAT/UNSAT answers. All 288 Witnora UNSAT short circuits on synthetic CNFs had independently checked XOR certificates. Solved SAT witness models were checked against original CNFs.

Among the 192 synthetic case medians (three repeats/case), mean full-pipeline wall time was **10.513 ms Kissat**, **13.052 ms Witnora+Kissat**, **20.479 ms CryptoMiniSat**. Witnora was thus **24.14% slower than Kissat** on this artificially balanced 50% SAT / 50% UNSAT family despite its 96 UNSAT wins. Median *paired* Kissat/Witnora ratio was about **1.261 on UNSAT** (Witnora wins) versus **0.574 on SAT** (Witnora loses).

For the three external CNFs jointly solved by Kissat and Witnora+Kissat, paired Kissat/Witnora ratios were approximately 1.0003, 0.9947, and 0.9915; median 0.9947. The other five external CNFs timed out for both arms. The Rust precheck produced no XOR certificate on any external trial. CryptoMiniSat timed out on all eight external CNFs under this 30-second cap.

Every planted-SAT near-XOR adversarial control returned SAT and no XOR certificate. Witnora was slower in all four (median Kissat/Witnora ratio approximately 0.554), which is the expected negative-control outcome when checking is pure overhead.

## Predeclared cost-aware break-even analysis

The synthetic matched-pair model defines mean SAT penalty `s = time(Witnora+Kissat) − time(Kissat)` and mean UNSAT saving `g = time(Kissat) − time(Witnora+Kissat)`; for positive s,g the mixed-workload average favors Witnora only when UNSAT fraction `p > s/(s+g)`. This is **not** an estimate of UNSAT prevalence in any real workload.

| Synthetic noise clauses | Mean SAT penalty (ms) | Mean UNSAT saving (ms) | Required UNSAT fraction | Paired-bootstrap conditional 95% interval |
| ---: | ---: | ---: | ---: | ---: |
| 0 | 6.522 | 2.124 | 75.4% | 72.1%–78.9% |
| 32 | 6.571 | 2.058 | 76.1% | 74.0%–78.4% |
| 256 | 5.763 | 2.160 | 72.7% | 68.8%–76.6% |
| 1024 | 6.872 | 2.084 | 76.7% | 73.5%–79.7% |
| 4096 | 8.207 | 2.546 | 76.3% | 73.9%–78.8% |
| 8192 | 10.048 | 2.553 | 79.7% | 77.8%–81.9% |

Every noise stratum included 16 matched SAT/UNSAT seed pairs and 5,000 paired bootstrap draws. The intervals are **conditional** on draws satisfying `p > threshold` and are not a population-level uncertainty statement about future SAT instances. The break-even threshold spans **72.7%–79.7%** here.

## Interpretation and next gate

**Supported:** Source-level independent XOR certificates are sound on the frozen synthetic family and reduce end-to-end latency on these UNSAT constructions. The performance benefit does not generalize to a balanced mixture or the official external suite under this setup. An unconditional precheck pays a measurable latency tax on SAT and misleading near-XOR controls.

**Not supported:** A general solver improvement, a state-of-the-art victory, a polynomial-time SAT algorithm, or any conclusion about P versus NP. The synthetic family has a planted structure and is not representative of arbitrary NP-complete instances.

**Next experiment:** Precommit a **selective gate** that cheaply decides whether to invoke the Rust XOR precheck based on independent structural information; compare gate+precheck+Kissat against baseline Kissat and the full-precheck arm under a held-out source/domain split. Account for *all* gating costs, constrain false positives, audit correctness, and maintain the same 30-second end-to-end cap. The W028 information-barrier theorem rules out perfect class separation based solely on the low-order moments that are identical for paired inputs.
