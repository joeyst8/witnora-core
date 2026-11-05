# W-CROSSDOMAIN-007 — Exact cutset-conditioned source violation polynomial

**Status:** Rust implementation and independent controls written; native compilation/tests await GitHub CI. **Prior-art construction** from cutset conditioning, polynomial sum-product, and Witnora's existing separator-conditioned ANF counter. It is not a new general #SAT result.

## The connection and the identity

W-CROSSDOMAIN-006 multiplies source-violation partition polynomials only when the original formula is variable-disconnected. A connected graph can sometimes become disconnected after fixing a small *separator* of variables. Cutset conditioning trades \(2^{|S|}\) separator assignments for independent smaller residual problems.

For source CNF \(F\), variable separator \(S\), and each fixed assignment \(s\in\{0,1\}^{S}\), form \(F\vert_{S=s}\) by removing every clause satisfied by \(s\), and deleting the fixed literals from every remaining clause. **Remove separator variables from the residual assignment universe**; otherwise a naïve free-variable factor would multiply the answer by \(2^{|S|}\) incorrectly.

For the number of violated source clauses \(E_F(x)\) and the polynomial \(P_F(q)=\sum_xq^{E_F(x)}\):

\[
P_F(q)=\sum_{s\in\{0,1\}^{S}}P_{F\vert_{S=s}}(q),\qquad
P_{F\vert_{S=s}}(q)=q^{e_s}\prod_j P_{F_{s,j}}(q).
\]

Here \(e_s\) counts residual empty clauses, and \(F_{s,j}\) are variable-disjoint components after conditioning. The equality follows from partitioning original assignments by their *unique* restriction to \(S\); each source clause's violation indicator is unchanged by substitution.

## Implementation

- Rust: `conditioned_violation_profile(source, nvars, separator, max_component_variables, max_separator_variables)` in `rust/witnora-ve/src/aux_violation_tensors.rs`. Input separator variable IDs are **one-based**, as in Witnora's ANF separator API. Validates duplicates and literals, enumerates each separator assignment, simplifies the source clauses, remaps unfixed variables densely, calls the W-CROSSDOMAIN-006 exact factorized oracle, and adds coefficients with overflow checking.
- PyO3: `aux_conditioned_violation_profile_native` in `rust/witnora-ve/src/lib.rs`.
- Independent Python controls: `tests/test_cutset_violation_profile_rust.py` compares every polynomial coefficient against direct literal truth tables for 160 seeded formulas, plus invalid-input and analytic families. The focused Rust workflow **imports both required bindings explicitly**, then executes the tests.

**Caps:** original formula at most 32 variables and 64 clauses; at most eight fixed separator variables and 14 variables per residual connected component. An oversized component causes an error. No automatic separator search, no general bounded-treewidth inference implementation, and no parity-row constraints are included here. The running time can still be exponential; a separator that fails to split residual components gains nothing.

## Analytic, connected falsification control

Take a 25-variable **connected star** formula containing the 24 clauses \((h\lor x_i)\) for \(1\le i\le24\). Its primal graph is connected; with component cap one, the unconditional W-CROSSDOMAIN-006 method rightly rejects it.

Fixing hub \(h\) yields two branches:

1. \(h=1\): all 24 clauses are satisfied; 24 leaves are free, contributing \(2^{24}\) at degree zero.
2. \(h=0\): each clause becomes the independent unit clause \((x_i)\), contributing \((1+q)^{24}\).

Therefore the **exact** connected-source polynomial is

\[
P_F(q)=2^{24}+(1+q)^{24},\quad
\#\mathrm{SAT}(F)=2^{24}+1=16,777,217,
\quad P_F(1)=2^{25}=33,554,432.
\]

This family tests both energy preservation and the absence of separator double-counting. It is deliberately easy under conditioning, not evidence of a universal speedup. In the favorable branches the method enumerates only one-variable components, but polynomial convolution and separator-branch overhead still need measured timing.

## Next experimental gates

1. **Compile/run GitHub CI**: verify Rust unit tests and independent Python-to-native parity; no local native wheel/toolchain was available when this implementation was written.
2. **Comparator**: compare performance and exact counts against Witnora's existing ANF source pipeline and its native separator-conditioned counter on small families; don't assume they solve identical tasks when one computes the *full polynomial* and the other just \(\#SAT\).
3. **Adversarial connected graphs**: include graphs that remain a large connected component after the chosen separator, triggering fail-closed behavior; include wrong separators and multiple separator sizes.
4. **Selection rule**: test a deterministic budgeted separator search with a declared state/cost predictor versus brute force and the existing `anf_separator_conditioning.rs::find_separator` heuristic. Baseline methods are prior art.

## Primary literature

- Rina Dechter, **“Bucket Elimination: A Unifying Framework for Reasoning,”** *Artificial Intelligence* 113 (1999), 41–85: <https://www.sciencedirect.com/science/article/pii/S0004370299000594>. Demonstrates the conditioning-versus-elimination time/space tradeoff.
- Rina Dechter, **“Enhancement Schemes for Constraint Processing: Backjumping, Learning and Cutset Decomposition,”** *Artificial Intelligence* 41 (1990): <https://www.sciencedirect.com/science/article/pii/0004370290900463>.
- Kschischang, Frey and Loeliger, **“Factor Graphs and the Sum-Product Algorithm,”** *IEEE Transactions on Information Theory* 47(2) (2001): <https://www.isiweb.ee.ethz.ch/papers/arch/aloe-2001-1.pdf>.

**Claim boundary:** Exact under validated source semantics and caps, contingent on native differential verification. This is an integration of established ideas, not a solution of P vs NP or a proof that graph topology alone determines #SAT.
