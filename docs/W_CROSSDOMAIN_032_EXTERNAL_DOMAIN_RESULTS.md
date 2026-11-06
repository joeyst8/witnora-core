# W032 — Source-verified external VLSAT2 SAT pilot (negative generalization result)

## Frozen protocol and provenance

- Exact pre-registered protocol: `docs/W_CROSSDOMAIN_032_EXTERNAL_DOMAIN_PROTOCOL.md`.
- Frozen 14-case manifest: `research/results/w032_case_manifest.json`.
- Benchmark implementation commit: `983110f81697f98eb89d7ceac563e72b27e24348`.
- Successful GitHub Actions evidence run: [42159600402](https://github.com/joeyst8/witnora-core/actions/runs/42159600402).
- Source verification: all eight original INRIA VLSAT2 compressed and decompressed publisher hashes match the archived W022 identity manifest; independently checked DIMACS headers, clauses and variables. No substituted source.
- Arms: unmodified pinned Kissat 4.0.4; frozen W027 XOR Rust precheck then same Kissat; frozen W030 streaming Rust XOR precheck then same Kissat.
- Three repetitions per arm per case; 126 total cost-inclusive invocations (72 on external inputs); rotating arm order; 6-second per-invocation cap, 2-GiB memory cap. This 6-second pilot is **not** directly comparable to the earlier 30-second W027 external pilot.
- Raw original JSON: `research/results/w032_external_raw.json.gz`, gzip SHA256 `aa87459c45986ac23be6e38b4f741024c67bfedf8db14061efdd00658fb2fa38`, decompressed SHA256 `67dbfa8a52099506efee01b57898448bb8b9a73ad76dec342a360b0054215fff`.
- Reproducible analysis: `research/results/w032_external_analysis.json`, computed by `scripts/analyze_w032_external.py`; source/models/certificates validated during the measured run.

## Primary external results

All 8 source-verified external cases gave identical outcomes across all three arms:

| Arm | Solved invocations / 24 | Timeouts / 24 | External W030 source proofs |
| --- | ---: | ---: | ---: |
| Kissat alone | 9 | 15 | — |
| W027 + Kissat | 9 | 15 | — |
| W030 streaming + Kissat | 9 | 15 | **0 of 8** |

**The W030 source scanner read 100.00% of the published clauses in every external instance**: 0 early terminations and 0 original-source UNSAT certificates. The three jointly solved UNSAT external cases all finished in all nine arm/repetition combinations; only their solved-case times may be compared numerically.

| Published case | Kissat median (ms) | W027 + Kissat median (ms) | W030 + Kissat median (ms) |
| --- | ---: | ---: | ---: |
| `vlsat2_684_13953` | 1,169.475 | 1,168.282 | 1,170.566 |
| `vlsat2_684_9417` | 1,024.033 | 1,029.338 | 1,027.477 |
| `vlsat2_708_10259` | 874.308 | 877.521 | 882.209 |

W030 adds approximately **1.09, 3.44 and 7.90 ms** versus plain Kissat on these three solved cases, respectively. The sample is too small for a general speedup or slowdown claim. Five external instances timed out under **all** arms; their times are right-censored, not performance comparisons or successes.

## Synthetic and adversarial controls (not generalization evidence)

- W030 correctly certified the one synthetic UNSAT control after reading **16 / 8,212 source clauses**. Its median complete cost was **3.313 ms**, against **8.790 ms** for Kissat and **6.978 ms** for W027.
- The synthetic SAT sanity control had no source certificate; W030 median **17.054 ms** versus Kissat **10.240 ms**.
- All four independent adversarial planted SAT decoys returned **NO_CERTIFICATE** as required, and W030 added overhead versus Kissat on all four. No false UNSAT certificates were observed.

## Interpretation and decisions

1. **W031's shuffled-clause synthetic gain did not transfer to this independent VLSAT2 sample.** This is a clear negative generalization result, not a solver breakthrough.
2. On these formulas the XOR pattern sought by W027/W030 was absent or undetectable using the frozen extractor, so a complete source scan purchased no shortcut.
3. Cheap source recognition, non-XOR certified structures, or substantially stronger prefix-level gating are the next meaningful directions; any predictor must beat its full pipeline cost.
4. This says nothing about P versus NP. Exact successes are confined to specific efficiently recognizable UNSAT subclasses; broader claims require substantially larger cross-family evaluations.

## Reproducibility and scope

Decompress the archived raw JSON and run `python -m scripts.analyze_w032_external RAW.json`; the results-integrity CI verifies hashes, frozen-case coverage, witness/certificate flags, and deterministic analysis equality. Do not pool SAT and UNSAT or interpret timed-out instances as solved. Report is a pilot, not a population-level performance estimate.
