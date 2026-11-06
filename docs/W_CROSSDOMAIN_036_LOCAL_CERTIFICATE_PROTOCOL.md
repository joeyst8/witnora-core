# W036 — Cheap geometric local subformula gate (proposed, not yet executed)

## Motivating measured barrier

- W031: shuffled synthetic XOR proof needs scanning ~95% of source and gains only 0.606 ms mean versus the old Rust precheck.
- W032: VLSAT2 external published CNFs yield zero W030 XOR source certificates and zero early terminations.
- W033: global exact Walsh L1 bound is negative on all eight VLSAT2 formulas.
- W034: small source-selected nonnegative weighted spectral LP certificates can be expressive but W035 shows **~53.5×** higher median paired case-level computation time than a simple Python DPLL reference on the same five-variable formulas.

## Hypothesis

Independent of clause count and graph size, small **locally interacting constraint neighborhoods** may contain enough contradictory structure to produce a compact source-derived UNSAT proof. A cheap prefix-limited local gate might identify such neighborhoods without the cost of a global source scan or full linear program.

This combines four complementary viewpoints:

1. **Geometry:** the signed variable–clause incidence hypergraph and local neighborhoods of overlapping constraints.
2. **Physics:** contradictions as energy frustration in a local landscape; exact positive lower energy is a proof, while estimated frustration is only a feature.
3. **Information theory:** source-derived concentration/cancellation of local Fourier coefficients; a cheap statistic is only useful if its predictive value exceeds its measurement cost.
4. **Computer science/statistics:** ordinary unit propagation, DPLL, XOR preprocessing, held-out validation, paired cost measurements, explicit false-certificate and timeout controls.

## Implementation plan and stage gates

**A. Frozen source and subsets.** Preserve SHA256 of all original published CNFs; include new independent families rather than only VLSAT2. Without a source-verified original corpus, do not claim generalization. Publish exact deterministic local-neighborhood construction, seed, and limits before outcome analysis.

**B. Cheap gate.** Read a fixed clause prefix (e.g. `1, 2, 5%`, each a separate preregistered budget) and construct at most three local signed-incidence neighborhoods per input. Cap selected subformula size at `16, 32, 64` clauses with no hidden scan of the remainder; record the exact number of original clauses read and all bytes/allocations. If subsets require expensive source-wide construction, charge it fully.

**C. Independent proof baseline.** On each *same selected* source subformula, try conventional unit propagation, fixed-budget DPLL and exact XOR extraction before claiming incremental value from Fourier LP. The sufficient certificate must use only original source clauses with exact independently verifiable integer weights; false SAT classification or unchecked floating proof fails the run.

**D. Full pipeline.** Cost-inclusive compare `Kissat`, `cheap gate + standard proof + Kissat`, and `cheap gate + W034-like proof + Kissat`; perform rotating repeat orders and charge parsing, feature, LP, source verification and fallback. Retain timeouts as censored observations, not completed solves.

**E. Decision.** The W034-based path is a candidate only if it produces **new external certified UNSAT cases beyond standard local propagation/DPLL/XOR**, and shows positive *total* savings after overhead on an independent workload. Otherwise record the negative result; treat structural scores as predictive features and evaluate held-out conditional mutual information against runtimes, with baseline SATzilla-style features, instead of asserting an exact shortcut.

## Mathematical boundary

Weighted Walsh positivity is a sufficient UNSAT certificate, **not** a complete SAT procedure. Selecting a useful subformula may itself be hard. Bounded local search and optional statistical ranking can reduce expected work on some distributions without changing worst-case NP-completeness. Neither a wave analogy nor statistical predictive accuracy is a proof that P equals NP.

## Prior-art landmarks to compare

- Soos, Nohl, Castelluccia, *Extending SAT Solvers to Cryptographic Problems* (2009), for XOR/Gaussian reasoning: https://www.msoos.org/wordpress/wp-content/uploads/2011/03/Extending_SAT_2009.pdf.
- Xu, Hutter, Hoos, Leyton-Brown, *SATzilla: Portfolio-based Algorithm Selection for SAT* (2008), for structure-aware solver selection: https://doi.org/10.1613/JAIR.2490.
- Braunstein et al., *Survey Propagation: An Algorithm for Satisfiability* (2005), for statistical physics and clustered SAT solution spaces: https://doi.org/10.1002/RSA.20057.
- Study of structural SAT parameters and backdoors is established; distinguish local certificate extraction from known width/backdoor techniques before claiming novelty.

**Status:** design memo only. No W036 runtime or success data have yet been produced.
