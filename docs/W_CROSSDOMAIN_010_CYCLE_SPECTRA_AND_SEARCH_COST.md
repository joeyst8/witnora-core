# W-CROSSDOMAIN-010 — Cycle-violation spectra versus deterministic DPLL search cost

**Status:** finite, exploratory Rust experiment and independent Python CLI oracle. GitHub Actions runs provide the native verification record. This is a **six-variable, signed 2-SAT pilot**, not a statement about worst-case hardness, algorithmic complexity classes, or SAT lower bounds.

## Question and null

W-CROSSDOMAIN-009 found that a predeclared triangle-violation parity spectrum can distinguish CNFs with identical graph, `#SAT`, and *full* violation-energy histograms. This experiment tests whether that extra information predicts the number of recursive nodes visited by a simple, fully specified DPLL **model counter**, within groups matched on the entire energy histogram. The null is **no improvement in left-one-out prediction**.

The analogy to a discrete spin/frustration observable is only a source of hypotheses. Signed literal flips are exact Boolean gauge transformations; Fourier projection and character duality already have a substantial history in coding and factor graphs. DPLL branch ordering and problem decomposition also have established literature; we do not propose a new solver or theorem here.

## Finite protocol

1. Use the exact W-CROSSDOMAIN-009 indexed seven-edge graph on six Boolean variables: `(1,2), (1,3), (1,4), (2,3), (2,5), (4,6), (5,6)`. Each endpoint gets one independent literal polarity, giving `4^7 = 16,384` signings. The triangle clause-index row `[0,1,3]` was fixed in W-CROSSDOMAIN-009, before this experiment.
2. Quotient by flips of each variable and all its literal occurrences (a truth-preserving change of assignment coordinates). Canonicalizing the first incident literal positive yields exactly `2^(14-6) = 256` representatives, one per 64-signing orbit.
3. For each representative, enumerate all `2^6 = 64` truth assignments directly to obtain the *entire* eight-coefficient violation histogram `A` and its triangle-even part `E`. Independently compare `E` with Witnora's exact Walsh/Fourier implementation.
4. Run a **full-model-counting** DPLL with deterministic unit propagation, early conflicting-clause rejection, and free-variable multiplicity when every clause is satisfied. Count **recursive calls including leaves**, not wall-clock microseconds. Use two fixed, opposite variable orders: ascending `[1,2,3,4,5,6]` and descending `[6,5,4,3,2,1]`. Confirm both model counts equal `A[0]`.
5. The baseline predicts recursive-node count by the mean of *other* representatives with the same `A`. The proposed feature predicts by the mean of *other* representatives with the same `(A,E)`. If this finer group has only one member, fall back to the baseline. Exclude energy groups that have only one member from **both** estimators. This is a leave-one-out (LOO) squared-error comparison over a fixed eligible set, not in-sample R².
6. As a conditional null control, shuffle the `E` labels **only within identical-`A` groups**, preserving their subgroup-size distribution. Use 1,000 fixed-seed Fisher-Yates permutations and count how often the improvement is at least as large as observed; add one to numerator and denominator to avoid a zero empirical tail probability. This is exploratory permutation accounting, not an independent confirmatory p-value.

## Finite observations

The original exploratory enumeration indicated the following; the Rust CLI recomputes and emits these metrics as JSON, and CI checks independent source-literal and DPLL oracles:

| Quantity | Ascending order | Descending order |
|---|---:|---:|
| Signing representatives | 256 | 256 |
| Distinct full-energy groups | 80 | 80 |
| Distinct energy-plus-triangle spectra | 135 | 135 |
| Energy groups split by triangle spectra | 30 | 30 |
| Eligible LOO representatives | 243 | 243 |
| Baseline energy-only LOO MSE | 2.7700 | 2.5282 |
| Energy-plus-triangle LOO MSE | 1.6033 | 1.1986 |
| Fractional reduction in LOO MSE | **42.1%** | **52.6%** |
| Conditional permutations matching/exceeding observed (1,000) | 0 | 0 |

If these exact values reproduce, they establish **added finite-family predictive information** about the chosen DPLL search-tree metric beyond the entire energy profile. The `0/1,000` permutation result corresponds to an exploratory add-one tail estimate of `1/1,001`, **not** to a guarantee of generalization. LOO cross-validation reduces direct self-prediction but does not remove graph selection, experimental-search, or family-overfitting bias.

**Important negative control:** the specific W-CROSSDOMAIN-009 matched-energy witness (`2603` versus `2607`) has different triangle spectra but **the same DPLL cost of three recursive calls under both variable orders**. The aggregate 256-orbit predictive signal does not imply that every pair separated by the cycle spectrum has different search cost.

## Why this is not a complexity breakthrough

- Every source formula is **2-CNF**, which has a polynomial-time decision procedure. A DPLL model counter is a deliberately fixed diagnostic, not a competitive 2-SAT solver or a proxy for the intrinsic complexity of the input.
- These 256 examples share one tiny indexed graph. The effect may disappear under different graph sizes, distributions, automorphisms, 3-SAT, CDCL, learned-clause strategies, or out-of-sample testing.
- The experiment was designed after observing W-CROSSDOMAIN-009's informative witness, and preliminary results were examined while specifying the pilot. Therefore the permutation result is exploratory regardless of how small its conditional p-value is.
- Predictor labels use **exact enumeration** of the violation landscape, which can itself cost exponential work. The pilot does *not* demonstrate that computing the diagnostic is efficient on general CNF instances.
- Equal energy histograms and a changed cycle signature do not imply a difference in SAT satisfiability, complexity class, proof length, or any universal search runtime.

## Implementation / repeatability

- `rust/witnora-ve/src/aux_cycle_cost.rs`: exhaustive canonicalization, native DPLL cost, independent Fourier comparison, LOO and within-energy permutations; native unit tests include signed gauge-flip controls and the prior matched-energy witness.
- `rust/witnora-ve/src/bin/witnora_cycle_cost.rs`: standalone JSON report; all source clauses and node counts for four reference signings are included.
- `tests/test_cycle_cost_audit_rust.py`: independent Python oracle reconstructs each reference signing from raw incidence bits, enumerates all assignments, and independently implements fixed-order model-counting DPLL.
- `.github/workflows/rust-migration-fast.yml`: Rust CLI compilation, the Python oracle test, and a JSON report are required steps of the focused CI gate.

## Next genuine falsification step

Freeze the triangle-spectrum feature and test it on **held-out non-isomorphic graphs with comparable n, m, density and cycle structure**, and a separate matched 3-CNF family. Report negative results, cross-family transfer, feature-computation costs, and sensitivity to solver algorithm (unit-propagating DPLL versus CDCL), with baselines such as component size, treewidth, backdoors and structural branching. A predeclared train/test split or prospective held-out family must precede any confirmatory significance claim.

## Relevant primary literature

- G. David Forney Jr., *Codes on Graphs: Duality and MacWilliams Identities*, IEEE Transactions on Information Theory, 2011, <https://arxiv.org/abs/0911.5508>.
- Jinbo Huang and Adnan Darwiche, *A Structure-Based Variable Ordering Heuristic for SAT*, IJCAI 2003, <https://ijcai.org/proceedings/2003/166>.
- E. A. Hirsch, *On the limit of branching rules for hard random unsatisfiable 3-SAT*, Discrete Applied Mathematics, 2003, <https://www.sciencedirect.com/science/article/pii/S0166218X02004080>.
