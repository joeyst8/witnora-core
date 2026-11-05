# W-CROSSDOMAIN-006 — Exact source-CNF violation partition polynomial

**Status:** experimental Rust implementation and independent tests written; native Rust CI not yet verified. This is an implementation of established factorization mathematics, **not a novel SAT or #SAT algorithm**.

## Cross-domain connection

For a source CNF (F) on (n) variables, define its *energy* at assignment (x) as the number of violated source clauses:

\[
E_F(x)=\sum_{C\in F}\mathbf{1}[C(x)=\mathrm{false}],\qquad
P_F(q)=\sum_{x\in\{0,1\}^n}q^{E_F(x)}.
\]

The coefficient at degree zero is exactly the satisfying-assignment count: \([q^0]P_F(q)=\#\mathrm{SAT}(F)\). The full integer polynomial tracks every number of violated clauses. Setting \(q=e^{-\beta}\) yields the familiar finite-system statistical-mechanics partition-function viewpoint. This connection is prior art; it does not alone give a practical general-purpose counting algorithm.

If the source *primal graph* breaks into variable-disjoint components \(F_1,\dots,F_k\), then assignments and energies split and the partition polynomial factors exactly:

\[
P_F(q)=q^e\prod_{i=1}^kP_{F_i}(q),
\]

where \(e\) counts empty clauses. Unused variables are singleton components with polynomial 2. The proof follows by distributing the product of sums over independent assignment domains; an empty clause adds exactly one violation to every assignment. This is a standard sum-product identity, closely related to factor graphs and convolution of densities of states.

## Rust implementation

- `rust/witnora-ve/src/aux_violation_tensors.rs`: `factorized_violation_profile(source, nvars, max_component_variables)` validates source literals, finds connected primal components by union-find, exactly enumerates assignments *within each component*, and uses checked-`u64` polynomial convolution to combine coefficients.
- `rust/witnora-ve/src/lib.rs`: Python-wheel binding `aux_factorized_violation_profile_native` for experimental comparisons.
- `tests/test_factorized_violation_profile_rust.py`: an independent, source-literal-level Python truth-table oracle for 240 seeded CNFs, an analytic 24-variable control, and rejection controls. The native gate asserts that the binding exists; it cannot silently pass all native cases as skips in CI.
- `.github/workflows/rust-migration-fast.yml`: native wheel differential test wired immediately after wheel build.

**Explicit limits:** up to 32 source variables, 64 source clauses, and 14 variables per component. An oversized component fails closed. This exact implementation currently has no parity-row coupling, no conditional decomposition over separators, no tensor-network contraction across shared variables, and no speedup claim for connected hard formulas.

## Falsifiable controls

1. **Independent oracle:** For random CNFs with at most eight variables (including empty, repeated, and tautological clauses), compare every coefficient against assignment-by-assignment enumeration. Rust unit tests independently compare the existing exhaustive Rust violation oracle; the Python gate compares direct literal evaluation.
2. **Analytic family:** Twelve disjoint clauses \((x_1\lor x_2)\land\cdots\land(x_{23}\lor x_{24})\) give \(P(q)=(3+q)^{12}\), so zero-energy count is \(3^{12}=531441\) and the sum of all coefficients is \(4^{12}=16777216\). The Rust path needs only twelve local 2-variable enumerations plus convolution, instead of a 24-variable truth table.
3. **Reject false generality:** With the same family and `max_component_variables=1`, the function must reject it. The implementation is intentionally unable to decompose across a connected component without a valid separator condition.
4. **CI tracking:** Python-only analytic assertions ran locally. Rust toolchain/native wheel unavailable in the current scratch execution environment; native test and compilation remain pending on GitHub CI.

## Research question for W-CROSSDOMAIN-007

Can an exact *separator-conditioned* polynomial be combined with Witnora's existing ANF separator machinery to accelerate models of connected, low-treewidth CNFs **without** changing the source model count? Compare against established variable elimination and junction-tree baselines; log separator state counts, conditioning work, and wall-clock timing. A positive result would be engineering/performance evidence unless we prove a distinct theorem. A negative result should be recorded, not buried.

## Prior literature (primary)

- Frank R. Kschischang, Brendan J. Frey, Hans-Andrea Loeliger, **“Factor Graphs and the Sum-Product Algorithm,”** *IEEE Transactions on Information Theory* 47(2), 2001: <https://www.isiweb.ee.ethz.ch/papers/arch/aloe-2001-1.pdf>.
- Scott Kirkpatrick, Géza Györgyi, Naftali Tishby, Lidror Troyansky, **“The Statistical Mechanics of k-Satisfaction,”** *NeurIPS 1993*: <https://proceedings.neurips.cc/paper_files/paper/1993/hash/a5cdd4aa0048b187f7182f1b9ce7a6a7-Abstract.html>. (Statistical-physics SAT perspective.)

**Claim boundary:** exact factorization is valid for *variable-disjoint source components*; the empirical structural descriptors in W-CROSSDOMAIN-005 did not determine #SAT, and this polynomial method does not contradict that falsification.
