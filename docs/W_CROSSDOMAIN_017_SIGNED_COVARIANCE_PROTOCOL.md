# W-CROSSDOMAIN-017 — Frozen signed clause-covariance geometry pilot

**Preregistered before W-017 outcomes.** Objective: connect finite SAT source geometry, exact uniform-assignment statistics, and the spin-glass notion of signed/frustrated interactions. This is a structural/mathematical experiment, **not** a proposed solver speedup.

## Exact observable

Let `v_c(x)` indicate that width-three clause `c` is violated by uniformly random Boolean assignment `x`. Let `K_cd = 64 * Cov(v_c,v_d)`; this is an **integer** symmetric covariance matrix. Diagonal `K_cc=7`. For two distinct source clause occurrences `c,d`, let `s` be the number of variables they share and `incompatible` mean the two clauses' *violation requirements* disagree on any shared variable. Then:

- If incompatible, `K_cd=-1`;
- If compatible, `K_cd=2^s-1` (so disjoint clauses give zero).

This identity is elementary exact probability, not a new theorem. The resulting matrix is positive semidefinite because it represents a real covariance, though its **off-diagonal entries are signed**.

Build the signed interaction graph with nonzero off-diagonals. Predeclare the following integer geometric statistics:

- `negative_pairs`: number of negative off-diagonal entries among unordered clause pairs (coincides with the previous incompatible-pair count);
- `positive_mass`: sum of positive off-diagonal coefficients;
- `negative_mass`: sum of absolute negative off-diagonal coefficients;
- `signed_mass = positive_mass - negative_mass`;
- `negative_triangle_mass`: sum of absolute negative products `K_ab*K_bc*K_ca` over unordered distinct clause triples;
- `positive_triangle_mass`: sum of positive such products.

For `E(x) = sum_c v_c(x)` on a formula with `m` clauses, exact variance satisfies

`64 * Var(E) = 7m + 2*signed_mass`.

This must match direct enumeration of all `2^12` assignments. Source-global Boolean gauge flips (invert a variable in **every** clause containing it) must preserve these statistics exactly. The sign-product around a triangle is a convenient gauge-compatible cycle statistic, **not** a physical frustrated-energy theorem.

## Previously unseen source generators

Reuse the **algorithmic specification** (not instances) of W-016 for `n=12`, 3 distinct variables per clause, xorshift32 seed evolution, 32 instances per family, and case seed `family_seed XOR ((index+1)*0x9E3779B9 mod 2^32)`:

- **New planted SAT:** family seed `0xD17C0DE1`, 48 accepted clauses, all-zero assignment guaranteed satisfying;
- **New uniform boundary:** seed `0xD17C0DE2`, 48 random clauses, no outcome filtering;
- **New embedded UNSAT:** seed `0xD17C0DE3`, eight contradictory source clauses on variables 1–3 plus 48 random clauses.

These 96 new formulas are distinct from the already-inspected W-016 population; no outcome-dependent generator tuning is allowed.

## Falsifiable prediction diagnostic

For each family report exact model counts, degree-ordered DPLL node counts and clause scans, and all covariance geometry statistics. For **each** frozen family independently compute the ordinary Pearson correlation of DPLL clause scans with the following **three predeclared scalar features**: (1) negative-pair count, (2) signed covariance mass, (3) negative triangle mass. Report all three coefficients (including null/negative associations), their means and ranges. No threshold, winner declaration, significance test, or prospective generalization claim is allowed from this small pilot.

An improvement in a descriptive correlation does **not** imply a faster branching algorithm. Higher-order constraints can share first and second moments while differing in satisfiability or search cost. The covariance graph is not a sufficient statistic for arbitrary SAT.

## Verification and prior work

Implement the exact integer pair covariance and signed triangular products in **Rust** with bounded memory and no external numerical linear algebra. Require Rust enumeration of energy variance and SAT verdicts on all 96 cases; additionally check identity/gauge invariance on fixed case indices `[0,1,31]` in each family. Add an independent **Python** literal truth-table / covariance / degree-DPLL oracle for the nine frozen controls in GitHub Actions. Do not require a positive predictive result for CI success. Preserve experimental output and performance limitations in the draft.

Primary precedents:

- Forney, *Codes on Graphs: Duality and MacWilliams Identities* (2011), <https://arxiv.org/abs/0911.5508> (factor-graph Fourier duality).
- Chertkov and Chernyak, *Loop calculus in statistical physics and information science*, *Physical Review E* 73, 065102 (2006), <https://doi.org/10.1103/PhysRevE.73.065102> (belief-propagation/loop expansion, conceptually related but distinct from this simple covariance triangle).
- O'Donnell, *Analysis of Boolean Functions* (2021), <https://arxiv.org/abs/2105.10386> (Fourier/statistical perspective).

No direct implication for `P = NP` or general complexity bounds is claimed.
