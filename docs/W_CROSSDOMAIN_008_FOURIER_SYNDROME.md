# W-CROSSDOMAIN-008 — Exact Fourier projections of clause-violation syndromes

**Status:** Rust implementation and independent controls prepared; native CI has not yet verified the Rust compilation or differential gate. **Research claim: integration of established coding-theory and factor-graph mathematics, not a new #SAT algorithm.**

## Why these fields connect

Witnora already studies source-clause violation vectors \(v_F(x)\in\mathbb F_2^m\), parity rows \(H\), and the distribution of violations by Hamming weight. Coding theory asks for **weight enumerators conditioned on parity syndromes**; statistical mechanics calls the unconditioned polynomial a finite-system partition function; sum-product reasoning exploits independent primal components. Forney's work on graphical codes and MacWilliams identities establishes the Fourier/partition-function connection in a more general setting (references below).

For a parity matrix \(H\in\mathbb F_2^{r\times m}\), a target syndrome \(b\in\mathbb F_2^r\), and clause violations \(v_j(x)=1\) precisely when source clause \(j\) is false, define:

\[
Q_{H,b}(q)=\sum_{x:\,Hv_F(x)=b} q^{\lvert v_F(x)\rvert}.
\]

Character orthogonality gives an **exact** projection:

\[
Q_{H,b}(q)=\frac1{2^r}\sum_{\lambda\in\mathbb F_2^r}
(-1)^{\lambda\cdot b}\!
\sum_{x\in\{0,1\}^n}
(-1)^{\lambda\cdot Hv_F(x)}q^{\lvert v_F(x)\rvert}.
\]

When the *source primal graph* splits into variable-disjoint components, each inner polynomial factorizes by component **even if a parity row refers to clauses in different components**. Thus Fourier transformation moves an XOR-coupling convolution into independent component-wise multiplication. Empty source clauses are handled by an explicit fixed energy shift and fixed syndrome; unused variables still contribute a factor of two.

### Crucial negative finding (claim boundary)

For **homogeneous** parity \(b=0\), every satisfying assignment has \(v_F(x)=0\), so:

\[
[q^0]Q_{H,0}(q)=\#\mathrm{SAT}(F).
\]

For **nonzero** syndrome \(b\ne0\), the constant coefficient is zero. Consequently, this Fourier projection gives *no direct advantage for determining #SAT via the zero-energy coefficient*. Its defensible use is an exact diagnostic of **near-solution violation spectra and cross-component parity interactions**; any stronger algorithmic claim needs a separate argument and measured evidence.

## Rust and verification design

- `rust/witnora-ve/src/aux_fourier_violation.rs`: `fourier_parity_violation_profile(source, nvars, rows, rhs, max_component_variables)`.
- CNF literals are one-based signed IDs; parity row entries are **zero-based clause indices**. Repeated indices in a row cancel mod 2. Missing clause indices and mismatched RHS lengths fail closed.
- For each disconnected primal component, enumerate local assignments once into a histogram indexed by `(violated_clause_count, syndrome)`. Apply an exact integer Walsh–Hadamard transform along the syndrome axis; multiply signed polynomial coefficients across components; inverse-project at only the requested syndrome with an exact divisibility check.
- Register `aux_fourier_parity_violation_profile_native` via the Python wheel. Native CI explicitly imports this symbol before running independent Python literal-evaluation controls.
- Strict limits: \(n\le32\) variables, \(m\le64\) clauses, \(r\le8\) parity rows, and \(\le14\) variables in any original primal component. Coefficients and intermediate sums use checked 64-bit integer operations; a failed cap or arithmetic check is an error, never a partial result.

## Falsifiable controls

1. **Global coupling across twelve independent clause blocks.** For 12 disjoint positive binary clauses, each has local polynomial \(3+q\). A single parity row spanning all 12 clauses enforces either an even or odd number of violations:

   \[
   Q_{\mathrm{even}}(q)=\frac{(3+q)^{12}+(3-q)^{12}}2,\qquad
   Q_{\mathrm{odd}}(q)=\frac{(3+q)^{12}-(3-q)^{12}}2.
   \]

   The even spectrum has only even-degree coefficients and has \([q^0]Q=3^{12}=531441\). The odd spectrum has only odd-degree coefficients and has zero constant coefficient. Their sum is \((3+q)^{12}\), and their combined value at \(q=1\) equals \(4^{12}=16777216\). The source has 24 variables, too many for Witnora's 14-variable exhaustive oracle, while the source components each have two variables.

2. **Independent source-literal truth tables.** `tests/test_fourier_parity_violation_rust.py` checks all weight coefficients for 240 seeded small CNFs against Python clause evaluation, including contradictory, redundant, empty, and duplicate-index parity rows with both homogeneous and nonhomogeneous RHS. A separate Python check of **96 random character-sum identities versus direct parity filtering passed locally** without a native wheel; the Rust differential tests remain pending.
3. **Regression to no parity rows.** With \(r=0\), the result must match W-CROSSDOMAIN-006 and the exhaustive source polynomial.
4. **Failure controls.** Out-of-range clause indices, malformed literals, mismatched RHS lengths, and oversized primal components must produce errors.

## Next research directions

- Treat each formula's *syndrome-conditioned energy profile* as a reproducible structural fingerprint and compare it against direct counting, topology-only metrics, ANF geometric invariants, and null/randomized controls. Track whether any signal remains after conditioning on graph structure and variable count.
- Compare the transformed-domain implementation with a **direct XOR-syndrome dynamic program** on the same families. Walsh–Hadamard is an algebraic acceleration for XOR convolution, but its overhead may dominate when \(r\) is small; timing is required.
- For connected source formulas, first combine with exact separator conditioning (W-CROSSDOMAIN-007) and only then apply the Fourier projection to the residual components, ensuring parity RHS updates are source-exact. This is standard cutset conditioning plus Fourier algebra, not automatically novel.

## Primary sources

- G. David Forney Jr., **“Codes on Graphs: Duality and MacWilliams Identities,”** *IEEE Transactions on Information Theory* (2011): <https://arxiv.org/abs/0911.5508>. Establishes Fourier duality for partition functions of normal factor graphs.
- F. J. MacWilliams, **“A Theorem on the Distribution of Weights in a Systematic Code,”** *Bell System Technical Journal* (1963): <https://onlinelibrary.wiley.com/doi/abs/10.1002/j.1538-7305.1963.tb04003.x>.
- Kschischang, Frey and Loeliger, **“Factor Graphs and the Sum-Product Algorithm,”** *IEEE Transactions on Information Theory* 47(2) (2001): <https://www.isiweb.ee.ethz.ch/papers/arch/aloe-2001-1.pdf>.

The implementation must be judged by exact parity with its independent controls and its documented limits. A mathematically valid diagnostic is not, by itself, a new general #SAT solver.
