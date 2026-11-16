# HV-007 — Prior-art elimination and certifying hardware-verification frontier gate

**Date:** 2026-11-10. **Status:** Literature audit plus a deterministic post-hoc analysis of archived HV-006 timings. **Result: no original Witnora algorithm, theorem, hardware-verification breakthrough, or validated speedup.**

## Question

Does the DSP output-partition overhead observation from HV-006 justify a novel *constraint-interaction* or *output-partition selection* method for certified chip-equivalence checking? If not, where is a scientifically plausible, chip-relevant frontier?

## Exact prior data and calculation

HV-006 source: `research/results/hv006_partition_overhead_screen.json`, precommitted ten-design development cohort `docs/HV006_PREDECLARED_DEVELOPMENT_COHORT.md`, pinned source and ABC commits identified there. All figures below use archived `elapsed_wall_seconds`, not new solver runs.

| Quantity | HV-007 deterministic replay |
| --- | ---: |
| All-partitioned summed screening time | 28.67 s |
| Per-case hindsight-oracle minimum of two modes | 24.79 s |
| Hindsight saved from always-partitioned | 3.88 s (13.53%) |
| Of that saving, attributable to DSP | 3.87 s (99.74%) |
| Remaining saving across nine cases | 0.01 s |
| Partitioned equivalent within 14 s guard | 10 / 10 |
| Unpartitioned equivalent within 14 s guard | 9 / 10 (VGA censored) |

**Caution:** A per-instance oracle uses outcome knowledge unavailable before solving and is not an implementable algorithm. These unisolated single-run timings (except the separate four-per-mode DSP follow-up) are not a statistical comparison. The unpartitioned VGA case timed out at the external guard; the oracle uses its partitioned success, but the censored unpartitioned time must not be treated as a measured completion time. The 0.01 s residual is smaller than plausible scheduling noise. The 13.53% is a post-hoc arithmetic upper bound on gains from choosing only between the *two recorded* modes on *this ten-case cohort*, ignoring choice-feature, training, proof and overhead costs; it is not a universal theoretical upper bound.

The DSP mode regression remains credible **as an observed local behavior**: replicated partitioned median 12.815 s vs unpartitioned median 9.21 s (ratio 1.3914), each mode proved equivalent on all its runs. The sum of ABC-reported partition AND counts for DSP was 514,432 vs 83,404 original+optimized input ANDs (ratio 6.17). This is a post-hoc **workload proxy**, *not* a count of unique duplicated gates, a complexity invariant, or causal proof.

## Kill gate: what the literature already solved or explored

| Tempting 'novel' claim | Closest verified primary evidence | Decision |
| --- | --- | --- |
| Discover overlapping output support and cluster outputs | Herbstritt, Kmieciak, Becker (2004), *Circuit Partitioning for SAT-based Combinational Circuit Verification — A Case Study*, explicitly defines the output-correspondence matrix `OCM[i,j] = |supp(i) ∩ supp(j)|`, discusses work reuse and WOG/BOG grouping; https://edocs.tib.eu/files/e01fn06/519562895.pdf | **Reject novelty** |
| Detect repeated SAT work between shared output cones and reuse it | Disch and Scholl (ASP-DAC 2007), *Combinational Equivalence Checking Using Incremental SAT Solving, Output Ordering, and Resets*, explicitly identifies the duplicate-work tradeoff and introduces incremental SAT, ordering and reset; https://www.cecs.uci.edu/~papers/aspdac07/pdf/p938_9C-3.pdf | **Reject novelty** |
| Optimize partition choice for runtime in principle | Mukherjee et al. (ASP-DAC 2000), *Automatic Partitioning for Efficient Combinational Verification*, DOI 10.1109/ASPDAC.2000.835072; plus 2004/2007 works above | **Reject generic novelty** |
| Certify incremental SAT / bit-level model checking | Fazekas et al. (2024), *Certifying Incremental SAT Solving*, DOI 10.29007/pdcc; Froleyks et al. (CAV 2025), *Introducing Certificates to the Hardware Model Checking Competition*, DOI 10.1007/978-3-031-98668-0_14 | **Reject generic novelty** |
| Invent liveness proof certificates | Froleyks, Yu, Bogaerts, Biere and Heljanko (CAV 2026), *Liveness Proofs for Hardware Model Checking*, DOI 10.1007/978-3-032-32537-2_1; algorithm-independent certificate format with evaluation | **Reject generic novelty** |
| Invent certified retiming + sequential-equivalence sweep | Seufert and Scholl (FMCAD 2026), *Certified Sequential Sweep Without Unrolling*, https://arxiv.org/abs/2607.27498, IC3-based certified SEC under retiming and resynthesis | **Reject generic novelty** |
| Optimize PDR for certificate size and verifier cost | Ferdowsi and Kovacs (FMCAD 2026), *Certificate-Aware Property-Directed Reachability*, https://repositum.tuwien.at/handle/20.500.12708/230511, reports checker-aware heuristic with disjoint training | **Reject generic novelty** |
| First word-level certificate checker | Froleyks and Yu (IJCAR 2026), *Hardware Model Checking Certification with Certifaiger and Cerbtora*, DOI 10.1007/978-3-032-32589-1_17; public Cerbtora checker https://github.com/Froleyks/cerbtora | **Reject novelty** |
| First Btor2 certifying verification workflow | Ádám et al. (TACAS 2024), *Btor2-Cert: A Certifying Hardware-Verification Framework Using Software Analyzers*, DOI 10.1007/978-3-031-57256-2_7, https://www.sosy-lab.org/research/btor2-cert/; bridges hardware to software witnesses with an independent validator | **Reject broad novelty** |
| First algorithm selection for word-level hardware checking | *Algorithm Selection for Word-Level Hardware Model Checking* (AAAI 2025 student abstract), https://ojs.aaai.org/index.php/AAAI/article/view/35275 | **Reject generic portfolio novelty** |

A narrower *new way to quantify interaction* is **not** logically excluded by the support-overlap papers. It merely lacks evidence today. In particular, neither our 6.17 workload proxy nor a standard output-overlap heuristic qualifies as such a new measurement.

## What still looks scientifically valuable (not yet established as novel)

Word-level, memory-rich **sequential chip safety verification with independently checked proof witnesses** is promising as an application. The July 2026 Certifaiger/Cerbtora paper reports that the new BTOR2 *witness-circuit* format had a working checker but an immature producer ecosystem, with an internal prototype k-induction certificate producer. Importantly, **Btor2-Cert existed in 2024** and generates independently validated *different-format* evidence via translation to C; therefore, blanket claims that no word-level certifying system exists are false. The actual candidate is interoperability and robust proof-inclusive scalability across *specific* publicly documented BTOR2 designs with arithmetic, state, and arrays, not invention of word-level proofs themselves.

Further relevant 2026 results constrain claims: hardware verification of security information flow has guarded-equivalence methods (https://arxiv.org/abs/2606.22063); the array-bearing word-level model-checking complexity landscape was studied in *On the Complexity of Word-Level Model Checking with Arrays* (FMCAD 2026); a new certificate tool is not interesting without improved solved-set, reliable checking, or meaningful resource reduction on *unseen* tasks.

**Research direction (candidate, not a verified open theorem):** For BTOR2 designs with nontrivial arrays/state, can a *specific, independently checkable* witness-production or structure-preserving reduction technique increase independently accepted solved instances or reduce total (solve + emit + check) cost against the 2024 Btor2-Cert, 2026 Cerbtora-compatible prototype and top open model checkers? The most important capability gap to verify first is which public baseline actually emits the same certificate format under matching semantics.

## HV-008 admission gate (proposal only; no experiment or holdout exposure yet)

1. Retrieve and pin a publicly licensed BTOR2 safety corpus (including array and nonarray tracks), benchmark ID list, all original input hashes, tool versions, machine characteristics, expected semantics, constraints/reset assumptions. Keep development, validation and final holdout disjoint. **Do not run or tune on previously frozen HV-003/HV-006 `tv80`, `spi`, `systemcaes` holdouts.**
2. Reproduce established baselines before editing algorithms: Cerbtora/Bitwuzla checker, Btor2-Cert/Btor2-Val, one strong word-level solver, one bit-blasted baseline. Record public availability, formats, and actual independent validator acceptance. The *same original task* must be checked; no silent relaxation of assumptions or array semantics.
3. Require a safe property and deliberately mutated unsafe counterpart on a development toy model, verify both witness and replayed counterexample; cross-check translated and original semantics. Report UNSAT only when accepted by an independent checker, and UNKNOWN otherwise.
4. Pre-register one technically explicit intervention and failure criterion **before** final evaluations. Suggested hypothesis: a structure-preserving reduction can reduce end-to-end checker-accepted runtime on unseen memory-rich tasks without lowering acceptance or losing semantic equivalence; this is a hypothesis, not a claimed new algorithm.
5. Compare number of independently certified instances, total wall time **including certificate emission and checking**, certificate bytes, peak RSS, incorrect/certificate-rejected results, and paired repeated runs. A checker failure is not success; unknown remains unknown.
6. Literature re-check immediately before any novelty claim. If improvement is only another implementation of an established technique, label it engineering, not frontier discovery.

## Falsification / stopping rules

- **Stop this specific output-overlap selector** unless a *pre-registered unseen cohort* demonstrates advantage after feature and proof-check costs; the HV-006 hindsight oracle's 3.88 s is too DSP-concentrated to support a general claim.
- **Stop proof-format novelty claims** if an equivalent witness protocol or checker already exists.
- **Do not claim a new theorem or complexity result** from elapsed-time charts. Any mathematical claim needs a complete theorem, assumptions, proof, and independent adversarial review.
- Keep PR in **draft**; retain all predeclared holdouts untouched until a full protocol, code, and fixed thresholds are committed.

## Provenance and interpretation

Archived ten-case raw inputs: `research/results/hv006_partition_overhead_screen.json`; derived arithmetic: `research/results/hv007_prior_art_and_oracle_gate.json`. No new SAT run, no new AIG transformation, no new external certificate, and **no scientific breakthrough** claimed for HV-007. This is an honest termination of rediscovery paths and a better-specified experimental target.
