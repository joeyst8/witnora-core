# Witnora W032–W035: source-verified experiment index

**Branch:** `research/w-crc-001-asymmetric-v1` in `joeyst8/witnora-core`.

These four experiments refine the central Witnora research goal: identify how interacting constraints predict or certify SAT/UNSAT, **without conflating proof strength, predictive information and computational advantage**. None constitutes a general SAT breakthrough or a resolution of P versus NP.

| Experiment | Primary question | Exact observed result | Verified artifacts |
| --- | --- | --- | --- |
| **W032** | Does the streaming Rust XOR detector generalize from synthetic to external published SAT? | External VLSAT2: **0/8 source UNSAT certificates**, all 8 fully scanned; same 3/8 solved by all three arms within 6 seconds; W030 marginally slower on solved cases. | `docs/W_CROSSDOMAIN_032_EXTERNAL_DOMAIN_RESULTS.md`, `research/results/w032_external_raw.json.gz`, CI `42160627842` **passed**. |
| **W033** | Can a Walsh–Fourier energy lower bound certify UNSAT beyond complete XOR cubes? | Exact proof on small non-XOR examples, independently brute-force checked; **0/8 external VLSAT2 certificates** and strongly negative global bound. | `docs/W_CROSSDOMAIN_033_SPECTRAL_EXTERNAL_RESULTS.md`, `research/results/w033_walsh_external_raw.json.gz`, CI `42161046353` **passed**. |
| **W034** | Can nonnegative weights isolate useful interacting constraints and rescue the global bound? | **74/77 UNSAT** certified on 200 tiny `n=5` synthetic source formulas, **0 false positives on 123 SAT**, 3 explicit incompleteness misses; every proof exact-integer audited. | `docs/W_CROSSDOMAIN_034_WEIGHTED_SPECTRAL_RESULTS.md`, `research/results/w034_weighted_small_raw.json.gz`, CI `42161941290` **passed**. |
| **W035** | Does W034's certificate strength beat ordinary full SAT search cost on these same formulas? | **No**: reference Python DPLL faster on **200/200**; median *paired per-case* W034/DPLL ratio **53.52×**; 1,200 cost comparisons. | `docs/W_CROSSDOMAIN_035_DPLL_COST_RESULTS.md`, `research/results/w035_cost_raw.json.gz`, CI `42162412066` **passed**. |

## Interpretation

- **Proof soundness:** the XOR and spectral certificates are source-derived and independently audited. SAT negative controls do not receive UNSAT certificates.
- **Expressivity:** weighting greatly extends the simple global spectral bound on a small artificial distribution.
- **Cost:** the extra LP power is not cheap; W035 shows a wide cost disadvantage on all small examples.
- **External relevance:** W032 and W033 failed to produce external proof coverage. W034 LP was *not* run on those large CNFs; claim no external W034 benefit.
- **Scientific novelty:** XOR extraction, Fourier analysis, LP, SAT algorithm selection, and statistical-physics-inspired message passing have substantial prior art. Avoid presenting recombinations as original theorem-level advances absent a formal literature and proof review.

## Next executable milestone

**W036: budgeted, source-verified local-constraint selection.** Exact proposed protocol: `docs/W_CROSSDOMAIN_036_LOCAL_CERTIFICATE_PROTOCOL.md`. Test whether cheap graph/hypergraph neighborhoods can isolate small subformulas worth checking before running the full SAT solver. Independently compare against **unit propagation and DPLL on the identical selected subformulas**, as well as unmodified Kissat on the full original CNF. Capture all feature, extraction, proof and subprocess costs, and include negative SAT controls.

Stop/redirect criteria: if there is no external proof coverage or if end-to-end overhead dominates savings, report the negative result and move to a *predictive* program (held-out runtime/complexity features), rather than assuming a mathematical shortcut exists.
