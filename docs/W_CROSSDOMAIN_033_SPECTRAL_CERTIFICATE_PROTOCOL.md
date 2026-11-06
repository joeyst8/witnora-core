# W033 — Exact Walsh–Fourier unsatisfiability lower bound

**Status:** exploratory mathematically sound sufficient certificate, not a new theorem claim or general SAT solver.

## Mathematical reduction

Represent a Boolean assignment by spins `s_i` in `{−1,+1}`. For a source clause `C` with distinct variables and literal polarities `t_i` in `{−1,+1}`, its violation indicator is

`I_C(s) = 2^(−|C|) ∏_(i in C) (1 − t_i s_i)`.

For a CNF with clause widths at most `w`, let `E(s) = Σ_C I_C(s)` be the number of violated clauses. Collect the Walsh coefficients of every clause into **exact integers** `b_S` such that

`E(s) = 2^(−w) (b_empty + Σ_(S nonempty) b_S ∏_(i in S) s_i)`.

Every nonconstant basis function is in `{−1,+1}`. The triangle inequality therefore gives the source-independent, efficiently verifiable lower bound

`E(s) >= 2^(−w) (b_empty − Σ_(S nonempty) |b_S|)`.

**Certificate:** if the integer numerator `b_empty − Σ|b_S|` is strictly positive, every assignment violates at least one clause and the original input is UNSAT. No DPLL search, statistical approximation, tolerance, or unverified SAT classification is required. Cost is `O(Σ_C 2^|C|)` time with sparse coefficient storage, useful only for bounded-width clauses. This is a sufficient condition and not a complete polynomial-time procedure for SAT.

For wider-source CNFs, applying the certificate to a source-derived **subset** containing only clauses of length ≤3 is also sound: proving that subset UNSAT proves the full CNF UNSAT. Skipping source clauses can only reduce certificate power, never create a false UNSAT certificate.

## Reproduced local microtests

`python -m unittest tests.test_w033_walsh_bound -v`

- Exact exhaustive truth-table check on **1,000 seeded random formulas** with 1–5 variables, including repeated literals, tautologies and empty clauses. No false UNSAT certificates observed; the computed integer lower bound held in each case.
- All eight 3-variable forbidden assignments (eight 3-clauses) yield constant violation count one and an exact UNSAT certificate.
- A three-clause implication-chain UNSAT formula with no 3-XOR cube is certified.
- A seeded formula of 35 **distinct** 3-clauses over five variables, with no complete 8-pattern triple cube, is certified; exhaustive enumeration independently found a minimum of two violated clauses.
- Explicit negative test: unrelated extra clauses can make the global L1 bound negative despite an existing UNSAT cube. Thus a full-source negative result **does not imply the formula is SAT** and prefix/subset selection may be crucial.

These examples establish soundness and extra coverage over the *specific* W030 complete-triple-XOR detector, but not novelty over SAT literature or standard solver preprocessing. The identity follows from classical Fourier analysis of Boolean functions.

## Source-verified external exploration

1. Reuse the exact eight frozen INRIA VLSAT2 identifiers, compressed source hashes and uncompressed content hashes from W022/W032. No source substitution.
2. Independently parse the original CNF. Retain clauses of width 0–3, recording the number of skipped wider clauses. The retained CNF is a source-derived subformula.
3. Compute the exact spectral coefficients and integer lower bound; record sparsity, width counts and full Python wall time (not a downstream solver speed benchmark).
4. Any `UNSAT_CERTIFIED` result on a publisher-labeled SAT case is a hard validation failure. A `NO_CERTIFICATE` result has **no SAT/UNSAT implication**.
5. Test the seeded 35-clause micro-witness and negative clutter control separately from external cases. Report external certificate count and calculation overhead, not a universal speedup.

The intended next step, **if external proof coverage is absent**, is proof-aware subformula selection or a cheap structural gate, compared directly against standard SAT preprocessing. Do not interpret a frequency analogy as a physical oracle or a P=NP result.

## Prior-art connections

- The spectral representation is a direct use of the established Walsh basis and triangle inequality. We make **no claim that this proof rule is new**.
- Gaussian/XOR extraction is already used by CryptoMiniSat; see Soos, Nohl, Castelluccia, *Extending SAT Solvers to Cryptographic Problems* (2009), https://www.msoos.org/wordpress/wp-content/uploads/2011/03/Extending_SAT_2009.pdf.
- Formula features and solver selection are established topics, including Xu et al., *SATzilla: Portfolio-based Algorithm Selection for SAT* (2008), https://doi.org/10.1613/JAIR.2490.
