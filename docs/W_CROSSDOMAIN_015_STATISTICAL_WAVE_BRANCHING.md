# W-CROSSDOMAIN-015 — Statistical information vs. DPLL branching: an exploratory negative result

**Research status: mathematical proposal and independent Python diagnostic only. No Rust solver feature or prospective speedup has been established.**

This follows the fully verified W-CROSSDOMAIN-014 result. The objective is to connect the cheap four-clause Walsh correlator to statistics and information theory while distinguishing *prediction of instance hardness* from *selection of a beneficial solver action*. This diagnostic was proposed after observing W-014 outcomes, so the familiar P1/P2 source families are **not** independent holdouts.

## Exact information-theoretic bridge

Let `S_C(x) = (-1)^(sum_{c in C} violation_c(x))`, the four-clause Walsh character from W-014. Under the **uniform distribution over all Boolean assignments** (not the uniform distribution over satisfying assignments), write `mu = E[S_C] = B_C / 2^n`.

The parity-even probability is `p_even = (1+mu)/2`; its binary entropy is `H_2(p_even)`. Thus merely replacing the scalar `mu` with its entropy **does not add information** and even discards the sign of `mu`.

For each unassigned variable `i`, define a new, variable-specific first-order cross-frequency

`h_i = E[S_C(x) * (-1)^(x_i)]`.

Then `E[S_C | x_i=0] = mu + h_i` and `E[S_C | x_i=1] = mu - h_i`. The information carried by fixing `x_i` about selected-clause parity is

`I(x_i; S_C) = H_2((1+mu)/2) - 0.5 * H_2((1+mu+h_i)/2) - 0.5 * H_2((1+mu-h_i)/2)`.

All these coefficients can in principle be accumulated **in the same 16 selected-clause subset expansion** as W-014: for each consistent term, a fixed variable contributes `+` or `-` its weighted assignment count to its first moment, while an unfixed variable contributes zero. The additional work to accumulate the per-variable moments and entropy must still be measured; the original 28.625 mean selected-clause visits was for **one scalar frequency only**.

This is existing Boolean Fourier and Shannon information theory, not a new entropy theorem. Information-theoretic branching has also been studied for mixed integer programming; unlike the present idea, that work measured uncertainty over its optimization relaxation. Statistical physics has likewise informed SAT survey-propagation heuristics.

## Exploratory variable-order diagnostic

Independent Python truth-table oracle, 4,096 gauge-canonical signings of each previously seen six-variable all-SAT P1 and P2 graph; same source clauses and fixed `[0,1,2,3]` Walsh row as W-014.

**Predefined diagnostic rule in this test:** compute the exact Shannon mutual information above for each of the six variables, then sort the entire static DPLL variable order by decreasing information, breaking ties by increasing variable index. DPLL is otherwise unchanged. Compare fixed ascending, fixed descending, and the structural degree heuristic (most clause occurrences, ties by increasing index). This exercise measures DPLL scans without adding feature extraction overhead.

| Graph | Ascending mean scans | Descending mean scans | Degree mean scans | Mutual-information mean scans | MI scans / degree scans |
| --- | ---: | ---: | ---: | ---: | ---: |
| P1 Pasch offset | 353.230 | 372.902 | **334.112** | 351.592 | **1.0523** |
| P2 Pasch shared vertices | 317.209 | 434.591 | **307.823** | 336.359 | **1.0927** |

Paired source counts against degree: P1 information-guided **1,820 wins / 66 ties / 2,210 losses**; P2 **1,744 wins / 95 ties / 2,257 losses**. This simple maximization of information about **parity**, even when exact, is a **negative result against degree branching** on both frozen families.

For illustration, on P1 source signing mask `1`, selected-parity mean `mu=0.375`. Mutual information in bits for variables 1 through 6 is approximately `[0, 0.05358, 0.05358, 0.05358, 0.05358, 0.01318]`. The resulting order used 230 DPLL clause scans versus 337 for ascending order, but source signing mask `12345` went the other way: 392 versus 330. Individual success examples therefore cannot establish general utility.

## One simple cross-family statistical gate

As a second *retrospective exploratory* diagnostic, learn the average signed difference `degree_scans - MI_scans` on all 4,096 rows of one seen family, grouped by (a) pair-violation conflict count or (b) `(pair-conflict count, wave bias)`; require at least 10 training rows in a group. Use MI branching on an instance of the other seen family only if its training-group mean difference is positive, otherwise use degree. This is graph-family transfer, but **not a prospectively independent test** because both graph families were previously examined.

| Training family -> test family | Degree baseline scans | Pair-only gate scans | Pair + wave gate scans | Pair + wave gate reduction |
| --- | ---: | ---: | ---: | ---: |
| P1 -> P2 | 307.823 | 306.625 | 307.297 | **0.171%** |
| P2 -> P1 | 334.112 | 332.234 | 332.065 | **0.612%** |

These scan-count gains are extremely small, and adding computation for Walsh moments, Shannon entropy, and the gate can readily reverse them. Importantly, the wave-augmented gate did not consistently improve over the cheaper **pair-only** gate. **No end-to-end time gain is established**.

## Research inference and next falsifiable experiment

1. The frozen W-014 frequency carried some information about *instance-level DPLL tree size*, but the parity-targeted Shannon information did **not** by itself yield a better variable order than a cheap structural heuristic.
2. A variable's information about **selected-clause parity** is an imperfect surrogate for information about **future unit propagation, conflicts, learned clauses, or search pruning**. This explains why a statistically predictable feature need not offer useful control.
3. Prospectively choose **new** graph families with both SAT and UNSAT formulas and larger variable counts; separate training and test by graph/generator, not by signing alone.
4. Measure a cost-aware *conditional treatment effect*: expected DPLL work saved by wave/physics/statistics guidance after accounting for the cost of computing the feature. Compare with degree, standard activity-based heuristics where applicable, and pair-only models; include timeout and tail-latency results.
5. Investigate cheap evidence about **propagation/conflict response**, possibly through bounded lookahead or belief/survey-propagation-style messages, instead of maximizing entropy reduction in a single four-clause parity variable. Predeclare the scoring rule and sign/generator splits **before** looking at their solver outcomes.

This document records a negative engineering result and a connection between Fourier analysis, Shannon information, statistical physics and solver branching. It provides **no general SAT runtime bound and no evidence for `P = NP`**.

### Established work informing this direction

- O'Donnell, *Analysis of Boolean Functions* (2021), <https://arxiv.org/abs/2105.10386>.
- Gilpin and Sandholm, *Information-Theoretic Approaches to Branching in Search* (IJCAI 2007; **mixed integer programming**, not this DPLL experiment), <https://ijcai.org/proceedings/2007/368>.
- Xu, Hutter, Hoos and Leyton-Brown, *SATzilla: Portfolio-based Algorithm Selection for SAT*, <https://arxiv.org/abs/1111.2249>.
- Mézard and Zecchina, *Random K-satisfiability problem: From an analytic solution to an efficient algorithm*, *Physical Review E* 66 (2002), <https://doi.org/10.1103/PhysRevE.66.056126>.
