# W031 clause-order robustness — frozen 16-seed results

**Status:** Completed; original W031 GitHub Actions [run 42158190111](https://github.com/joeyst8/witnora-core/actions/runs/42158190111) succeeded. **All 900 cost-inclusive timed invocations passed** the frozen source labels and independent proof/model checks; no timeouts or solver errors. These findings are for a deliberately constructed 8,192-noise XOR family and four planted-SAT decoys, not arbitrary SAT problems.

## Reproducibility and original data

- Precommitted protocol: [`docs/W_CROSSDOMAIN_031_ORDER_ROBUSTNESS_PROTOCOL.md`](W_CROSSDOMAIN_031_ORDER_ROBUSTNESS_PROTOCOL.md) with 16 independent W026 noise seeds, each matched SAT/UNSAT under core-first, core-last, and label-blind full-CNF shuffle, plus four planted SAT decoys. Exactly 100 frozen original CNFs; three arms × three repeats = 900 timed pipeline invocations, 6-second end-to-end cap and 2GiB memory cap each.
- Exact pinned Kissat rel-4.0.4 commit `8af8e56f174b778aef3aa45af9f739b2a5f492c2`, unchanged source CNFs. W027 and W030 prechecks are source-audited Rust programs and never assert SAT.
- The original GitHub Actions artifact `w031-order-full-raw` is archived permanently as binary gzip [`research/results/w031_order_raw.json.gz`](../research/results/w031_order_raw.json.gz). Exact **uncompressed raw JSON** SHA-256: `0764220a14b5b309ba13e123c3a97fede1336beece4c64432850c4d722d3a85c`. Compressed `.gz` SHA-256: `b2d355d179acd96043b0678bc6a5a8ce948b3aa8d103b9af45e1c82cceea9cd9`. The archive is byte-for-byte the raw artifact (gzip -n for deterministic packaging).
- Recompute raw results using `python -m scripts.analyze_w031_order research/results/w031_order_raw.json.gz`. The frozen analyzer is [`scripts/analyze_w031_order.py`](../scripts/analyze_w031_order.py); its numerical result is [`research/results/w031_order_analysis.json`](../research/results/w031_order_analysis.json). A follow-up CI job verifies recomputation and stored source hashes.

## Main measurements

All timing statistics below are means over **16 per-seed medians of three repeats**, with SAT/UNSAT paired by noise seed. Paired 95% bootstrap intervals use **5,000 resamples of entire seed pairs**, as specified before the experiment.

| Clause order | W030 UNSAT saving vs W027 (ms) | 95% paired bootstrap CI (ms) | W030 SAT overhead vs Kissat (ms) | W030 UNSAT saving vs Kissat (ms) | Mean original clauses read before UNSAT proof |
| --- | ---: | ---: | ---: | ---: | ---: |
| corefirst | 3.511 | 3.483–3.541 | 5.771 | 5.170 | 0.19% |
| corelast | 0.450 | 0.426–0.472 | 5.738 | 2.156 | 99.95% |
| shuffled | 0.606 | 0.536–0.674 | 5.793 | 2.341 | 95.28% |

**Preregistered H1 passed:** under label-blind *shuffled* clause order, mean(W027 UNSAT runtime − W030 UNSAT runtime) is **0.606 ms**, with 95% conditional paired-bootstrap interval **0.536–0.674 ms** entirely above zero. This is positive evidence of an incremental Rust proof-engine improvement **within this 16-seed synthetic family**.

Crucial caveat: shuffle moves the source contradiction near the end. The W030 prefix engine consumed on average **95.28%** of the source clauses before a proof, from **90.14%** to **99.73%** across the 16 shuffled seeds. The speedup over W027 here mainly indicates lower implementation overhead, not broad early-termination benefit.

## Balanced mixture and hypothetical UNSAT prevalence

With a hypothetical equal mix of matched SAT and UNSAT pairs, W030's mean added wall time relative to plain Kissat remains positive in every order stratum. The break-even threshold is computed from mean SAT penalty `s`, mean UNSAT saving `g` as `p > s/(s+g)`; it is *not* an empirical estimate of real UNSAT prevalence.

| Clause order | Mean balanced extra cost vs Kissat (ms/case) | Conditional paired bootstrap 95% CI | Hypothetical UNSAT share needed for break-even |
| --- | ---: | ---: | ---: |
| corefirst | +0.300 | +0.205 to +0.395 ms | 52.7% |
| corelast | +1.791 | +1.703 to +1.884 ms | 72.7% |
| shuffled | +1.726 | +1.638 to +1.820 ms | 71.2% |

All four misleading near-XOR planted-SAT controls returned `NO_CERTIFICATE`, preserving soundness. The primary positive finding does **not** show that W030 beats the unmodified baseline Kissat on a balanced workload, nor does it establish anything about P versus NP.

## Next independent falsification

Test **external** DIMACS cases with no known planted parity structure, including official VLSAT2 (whose W027 results include 5/8 timeouts), plus differently generated parity problems where the contradiction is diffuse rather than one tiny core. Maintain end-to-end caps, original source hashes, and independent certificates. A structured-synthetic improvement is valuable solver engineering but not a cross-domain SAT breakthrough.
