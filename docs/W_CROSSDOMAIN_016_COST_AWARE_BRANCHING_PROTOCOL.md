# W-CROSSDOMAIN-016 — Prospective cost-aware statistical-wave branching test

**Frozen protocol before examining W-016 solver outcomes.** This follows the mixed/negative W-014 and W-015 pilots; it does **not** inherit their seen six-variable source instances. The hypothesis is deliberately falsifiable: a cheaply computed four-clause Walsh cross-frequency might change DPLL's actual work when used as a branching heuristic, but it can also do worse than degree. The outcome criterion is **total work and wall time**, not predictor MSE.

## New formula populations (no post-outcome selection)

Generate **96 formulas**, each with `n=12` active Boolean variables, 3 distinct variables per clause. Use a fixed 32-bit xorshift generator (`seed ^= seed << 13; seed ^= seed >> 17; seed ^= seed << 5`, modulo `2^32`) and seed each instance as `family_seed ^ ((index+1) * 0x9E3779B9 mod 2^32)` for indices `0..31`. Draw variables as `random % 12` (reject duplicates within a clause) and signs from successive `random & 1` bits. Do not reject, reseed or filter generated instances on solver outcomes.

1. **Planted-SAT**: base seed `0xC0FFEE11`, 48 clauses; reject a clause only when it would falsify the known planted all-zero assignment, so every instance is SAT. Sign sampling and rejection are entirely determined by the fixed generator.
2. **Uniform-boundary**: base seed `0xC0FFEE22`, 48 independent random 3-clauses, with no planted solution or SAT/UNSAT filtering.
3. **Embedded-UNSAT control**: base seed `0xC0FFEE33`, all eight signed clauses on variables 1,2,3, followed by 48 independently random 3-clauses, guaranteeing UNSAT while preserving an intentionally easy local contradiction as a negative/structural control.

These are small bounded tests, not industrial SAT benchmarks, and source generator differences are not interchangeable with a genuinely representative distribution. Report SAT vs UNSAT per family; do not assume all boundary instances have both classes.

## Frozen feature and DPLL methods

One common **source-level** parity row of four distinct clauses per instance, selected without reading signs, labels, or search outcomes: start with clause index 0, then greedily add the lowest-index remaining clause achieving maximum total unsigned variable overlap with the selected clauses, until four clauses are chosen. Count the selector's scope-overlap comparisons separately.

For that four-clause set `C`, use `S_C(x)=(-1)^(sum v_c(x))` and the exact 16-term inclusion-exclusion expansion from W-014. In the same pass accumulate the unnormalized first-order Walsh moments `sum_x S_C(x)*(-1)^(x_i)` for all 12 variables; a term contributes zero to a moment if its variable is not fixed. Compute Shannon mutual information `I(X_i;S_C)` under **uniform Boolean assignments**, not the (generally intractable) uniform satisfying-assignment distribution.

Choose among these complete, static variable orders, with **false branch before true branch**:

- **ascending**: 0,1,...,11 (negative control);
- **degree**: descending unsigned source variable occurrence count, ties by ascending index (primary baseline);
- **wave**: descending mutual information rounded to 12 decimal places to make numeric ties stable across machines, ties by higher degree then ascending index;
- **gated wave**: same wave order if `max_i I(X_i; S_C) >= 0.020000000000` bits; otherwise degree order. This fixed threshold is a simple prior heuristic motivated by W-015's already-observed 0.013/0.054-bit scales; do not tune on W-016 outcomes.

All methods use identical simple recursive DPLL: unit propagation until a fixed point, early contradiction, stop on the first satisfying assignment, no learned clauses or restarts, and whole-clause scan count for propagation and all-satisfied checks. Verify each reported SAT verdict against a direct `2^12` truth-table oracle, at least on fixed control instances in both Rust and independent Python; no false result may pass CI.

## Cost and correctness measures

For every family and method report average DPLL recursive nodes, whole-clause scans, SAT counts and paired win/tie/loss relative to degree. Record frequency selector's unsigned clause-pair comparisons, 16 subset-term evaluations, selected-clause and literal visits, moment updates, and the total overhead; **do not equate these heterogeneous work units to DPLL scans**. For wall time, measure the full per-instance degree baseline against complete feature+sort+solve wave and gated-wave pipelines, using Rust `Instant` on the same source/runner, repeated 20 times and alternated in execution order. Report measured total elapsed time per method with the caveat of CI-host noise. Timing is a descriptive measurement, never a correctness assertion.

Both **conditional branch gain** and unfavorable cases are required report content; any fraction of datasets may fail the hypothesis. No outcome-dependent selection or retry is allowed. Independent Python controls must reconstruct the 32-bit source generator and verify control sources, truth-table SAT verdicts, and DPLL counts for designated case indices `[0,1,31]` in each family. The Rust executable and its independent oracle must run in GitHub Actions; no numerical improvement is a pass/fail requirement.

## Interpretation boundary and prior art

The study tests only one small spectral statistic and simple DPLL, not general polynomial-time SAT, not `P = NP`, and not a new Walsh transform. Existing information-theoretic branching and algorithm-selection work—Gilpin/Sandholm (2007), Xu et al. SATzilla—and statistical-physics survey propagation are relevant methodological precedents (linked in `W_CROSSDOMAIN_015_STATISTICAL_WAVE_BRANCHING.md`). A small positive scan-count result is **insufficient** if feature overhead or wall time loses. A negative result remains part of the research record.
