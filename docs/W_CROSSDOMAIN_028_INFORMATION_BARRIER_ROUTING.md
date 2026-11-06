# W028: an information-limited gate cannot solve the W024 routing problem

**Status:** derived proposition from the independently verified W024
constructed pair; research-design guidance, not a new P/NP theorem.

## The connection

W024 proved that a deliberately matched SAT formula `F_sat` and UNSAT
formula `F_unsat` share **exactly** the following features: variable
count, clause count, literal degrees, unsigned triple supports,
aggregate clause-polarity histogram, all first/second sign moments,
and signed-incidence pair Gram matrix. Their individual solutions differ
(32 versus 0). The useful information first appears when an *indexed*
third-order parity sign is coupled to the cycle structure of the
underlying variable triples.

W027 adds a practical constraint: running indexed parity extraction is
not free. Its exploratory pilot found an UNSAT cost saving but a SAT
preprocessing penalty. We would like a cheap gate to **run** the
extractor on the UNSAT case and **skip** it on the SAT case.

## Precise restricted impossibility

Let `phi(F)` be exactly the W024 low-order statistics listed above,
and let `g(phi)` be any deterministic gate that chooses `RUN` or `SKIP`
from those features alone. W024 establishes

    phi(F_sat) = phi(F_unsat).

Therefore, by substitution,

    g(phi(F_sat)) = g(phi(F_unsat)).

Thus no such gate can simultaneously **skip the SAT partner** and
**run on the UNSAT partner** for this matched pair. This is true
regardless of how much computation the gate spends on `phi` once the
features are given. It is an information-availability barrier for this
restricted gate family, not a computational-complexity lower bound.

For a randomized gate using only `phi` and fresh independent randomness,
its probability of choosing `RUN` is also identical for the two
partners. On a balanced population consisting of this matched pair,
any probabilistic score formed solely from `phi` has ROC AUC 0.5.
No classifier of these exact features can outperform chance at
*discriminating this pair*, although always-run or always-skip may
have different decision costs.

## Geometry, physics, statistics and computer science

- **Geometry:** both inputs have identical second-order signed Gram
  representation, so that geometry cannot route them differently.
- **Physics:** the differing information is analogous to a signed
  cycle frustration / gauge holonomy not visible in those pair moments.
- **Information theory:** the two inputs occupy the same equivalence
  class under `phi`; no subsequent processing of `phi` can recover
  their differing label.
- **Statistics:** in this paired test distribution, a low-order-only
  gate has equal true-positive and false-positive run rates; the
  decision threshold requires expected preprocessing costs and label
  prevalence, which W027 measures separately.
- **Algorithms:** future routing must consult additional indexed
  parity/cycle information, reuse metadata obtained for some other
  task, or accept that it cannot selectively avoid cost on this pair.

## Next falsifiable experiment

Use the W024 matched pairs as one controlled stratum. Compare three
*cost-inclusive* routes: an all-run extractor, a low-order-only gate,
and a gate using an explicitly bounded amount of indexed third-order
evidence. Freeze gate features and thresholds on separate training
instances and time on heldout relabelings plus outside-of-family CNFs.
Any speed or classification advantage must pay for feature extraction.
Do not infer that this test separates P from NP.

Primary source evidence: [W024 verified moment barrier](W_CROSSDOMAIN_024_MOMENT_INFORMATION_BARRIER_RESULTS.md)
and [W027 full solver protocol](W_CROSSDOMAIN_027_COST_INCLUSIVE_SOLVER_PROTOCOL.md).
