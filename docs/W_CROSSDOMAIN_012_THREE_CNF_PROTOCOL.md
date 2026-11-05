# W-CROSSDOMAIN-012 — Prospective signed 3-CNF incidence-geometry pilot

**Preregistered before evaluating any outcomes.** This asks whether the W-CROSSDOMAIN-010/011 fixed syndrome-spectrum feature retains predictive value for a **3-uniform clause hypergraph**, not just graphs of signed 2-clauses. This is an exact finite **model-counting search-cost diagnostic**, not a result about P versus NP or general SAT hardness.

## Frozen 3-CNF families

Every clause has three *distinct* variables and exactly one independent literal-polarity bit per occurrence. Each graph has six variables and six indexed 3-clauses; the total signing space is `2^(6*3) = 262,144`. All six variables occur, and the 64 variable-flip gauge transformations form free orbits, so there are exactly **4,096** representatives per family.

- **T1 — cyclic triple-overlap ring:** `(1,2,3), (2,3,4), (3,4,5), (4,5,6), (5,6,1), (6,1,2)`. Every variable has incidence degree three.
- **T2 — skew-incidence control:** `(1,2,3), (1,2,4), (1,3,5), (1,4,6), (2,3,5), (4,5,6)`. Incidence degrees, sorted decreasing, are `(4,3,3,3,3,2)`. These degree sequences prove the incidence hypergraphs are not isomorphic.

The **only** tested added feature is the even-parity distribution of violation indicators for **predeclared clause indices `[0,2,4]`**, conditioned on the total number of violated source clauses. The formula's full `A_0..A_6` violation-energy histogram is the baseline. The even-parity distribution of *all* six violations is a **negative control**: it is completely determined by `A` and must never appear to add information.

## Frozen measurement and falsification criterion

1. Enumerate all 262,144 signings per family and quotient by all variable flips to 4,096 canonical representatives. Do not sample or reselect instances based on results.
2. For each representative, enumerate all 64 total assignments and compute `A` and the `[0,2,4]` even syndrome `E` from actual source clauses. Verify `E` independently using Witnora's Rust Fourier/parity projector. Validate model counts using complete fixed-order DPLL with unit propagation.
3. Fix two DPLL variable orders (ascending `1..6` and descending `6..1`); count **recursive visits** as the primary outcome. Count all clause scans in direct feature enumeration (`6 * 64 = 384` per formula) and DPLL propagation/termination as a secondary work comparison. This does **not** imply wall-clock equivalence, hardware efficiency, or scalability.
4. Within each separate hypergraph, compute baseline energy-only vs `(A,E)` **leave-one-out** MSE. Exclude singleton energy groups from both estimators and fall back to energy-only for singleton syndrome subgroups, exactly as in W-CROSSDOMAIN-010. Report number of eligible representatives and any zero-variance baseline explicitly.
5. Run 1,000 seeded, within-energy-group label permutations per graph. The strictly frozen replication criterion is **positive MSE improvement and add-one conditional permutation tail at most `0.0125` for all four graph/order combinations**. If any fail, mark the criterion **NOT MET**; never change rows, family, order, threshold, or exclusion rule in response.
6. Also compute the fraction of representatives for which 384 direct-feature clause scans exceed the DPLL clause-scan count. This is a rough **workload warning**, not a normalized wall-time estimate; the feature is computed exactly and may be much more costly than the search it proposes to predict.

## Essential mathematical boundary

**All formulas in these particular families are satisfiable.** Each width-three clause rules out only `2^(6-3) = 8` of the 64 assignments. Six such clauses together can rule out at most `6*8 = 48` assignments, leaving **at least 16 models**. Therefore these instances cannot challenge UNSAT decision hardness, even though they are syntactically 3-CNF. This is a deliberately bounded diagnostic of model-counting search-tree *variation*, not a proof-hard family.

The feature may capture correlation without providing a useful solver strategy. In particular, computing its entire exact distribution already evaluates every assignment; a general algorithm that required that much work would be unhelpful for hard SAT. Negative results and cost disadvantages are valid outcomes.

## Implementation and independent verification

- Build a new bounded Rust module and JSON CLI with exhaustive signing quotient, source-literal truth tables, native Fourier cross-checks, fixed DPLL instrumentation and conditional permutations.
- Add an independent Python source/assignment/DPLL oracle for selected signings on each frozen family, including a direct check that all-clause parity adds exactly zero information to the energy histogram.
- Require both Rust unit tests and the separate independent oracle stage in GitHub Actions; save results and links **after** the checks complete.

## Existing mathematics and algorithmic background

- G. David Forney Jr., *Codes on Graphs: Duality and MacWilliams Identities*, IEEE Transactions on Information Theory (2011), <https://arxiv.org/abs/0911.5508>.
- Jinbo Huang and Adnan Darwiche, *A Structure-Based Variable Ordering Heuristic for SAT*, IJCAI (2003), <https://ijcai.org/proceedings/2003/166>.
