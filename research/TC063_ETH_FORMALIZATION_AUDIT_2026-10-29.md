# TC-063 formalization and OpenAI ETH construction audit (2026-10-29)

Status: **research audit / open proof obligations**, not a verified Lean proof, algorithmic breakthrough, or benchmark result.

## Source boundaries

- Witnora: `theory/TC063_BOUNDED_SEPARATOR_AFFINE_HARDENED_THEOREM.md`, `paper/WITNORA_COLLAPSE_HIERARCHY_EXTERNAL_REVIEW_DRAFT.md`.
- OpenAI: [ETH announcement](https://openai.com/index/building-scientific-understanding-with-academic-communities/) and [Lean scope note 378](https://github.com/openai/math/blob/main/lean/docs/378.md).
- OpenAI's public Lean scope states, for every fixed `k >= 2`, exact counting of satisfying assignments of canonical k-CNF in time `(L+1)^O_k(1) * 2^O_k(n (log log n)^2 / sqrt(log n))`, with a polynomial tape-cell bound. Its manuscript asserts a sharper bound. These must not be conflated.
- Neither project claims/establishes P=NP. ETH false is not equivalent to P=NP. The independent interpretation of OpenAI's research remains under review.

## A formal mathematical target for TC-063

Fix a Boolean CNF formula F with variables partitioned into a separator S and residual variables R. For each assignment a to S, suppose residual components C_1(a), ..., C_t(a) are disjoint in variables and the reduction is equivalence-preserving:

  F(a,b) iff for all i, C_i(a, b restricted to variables(C_i)),

where b ranges over assignments to R. It follows by elementary finite-set reasoning:

1. **SAT lifting / exhaustiveness:** F is satisfiable iff there exists a separator assignment a such that every C_i(a) is satisfiable. A witness for each independent component combines with a to give an F witness, which must be checked against the original clauses.
2. **UNSAT cover:** F is unsatisfiable iff every separator assignment a has at least one unsatisfiable component C_i(a).
3. **Exact counting (conditional extension):** If component variables partition R and each component's satisfying assignments can be counted exactly, then #SAT(F) = sum over separator assignments a of the product over i of #SAT(C_i(a)). Any free variables not contained in a component contribute a factor 2 per free variable. This formula depends on *disjointness* and preservation of the original formula; products without those conditions are invalid.
4. **Runtime (conditional):** Given a separator found in polynomial time, an exact affine extractor/checker running in polynomial time, and at most poly(n) residual components per branch, enumeration costs `2^|S| * poly(|F|)`. This is polynomial only for fixed |S| (or more generally |S| = O(log |F|)). If |S|=n, this degenerates to ordinary brute force.

These are *conditional target theorems*, not certified statements about the current code. The current TC-063 file lists eight proof obligations. A Lean formalization must bridge its abstract semantics with the concrete DIMACS parser, certificate format, and G5 implementation.

## Lean 4 development plan with explicit gates

Use a pinned Lean 4 + mathlib toolchain in a separate `formal/` directory. Start with no project-specific axioms and no `sorry` in the proof-bearing target.

- Gate A: model finite variables (`Fin n`), literals, clauses, CNF satisfaction, partial assignments, and restriction; prove restriction preserves satisfaction.
- Gate B: model separator assignments and variable-disjoint residual components. Prove the decomposition equivalence as an explicit *assumption* initially; then discharge it from an independently specified and checked decomposition certificate.
- Gate C: prove the SAT lifting and UNSAT cover equivalences. Obtain a direct original-CNF model check, rather than merely trusting a residual solver.
- Gate D: represent affine equations over `ZMod 2` (or `Bool`) and prove exact CNF extraction soundness, Gaussian elimination SAT/UNSAT correctness, and certificate soundness for the supported G5 scope.
- Gate E: prove an actual finite computational cost bound for separator enumeration, component checking, certificate generation, and certificate verification, including bit encoding and formula size; distinguish `2^c poly(n)` from unconditional polynomial time.
- Gate F: state one composed theorem whose assumptions are all discharged by implementations or verified certificates; audit `#print axioms`, forbidden placeholders, and trusted inputs.

A Lean file proving just a propositional lifting lemma is not a formal verification of the Python pipeline. Conversely, a passing Python test or native verifier is not a Lean kernel proof.

## What can and cannot transfer from OpenAI ETH

OpenAI's claimed universal fixed-k CNF subexponential algorithm and Witnora's separator/affine method are structurally different:

- Witnora: discover a small separator, enumerate `2^c` branches, then exactly solve affine components. Strength: independently checkable local transformations and witness reconstruction. Bottleneck: arbitrary CNFs may have no such small separator/affine residual structure.
- OpenAI: published formal claim gives a subexponential-time exact counting machine for canonical fixed-k CNFs, with an explicit asymptotic bound. This is not an affine-separator theorem and not a polynomial-time SAT solver.
- A *hypothetical* universal procedure that transforms every fixed-k CNF into Witnora-certified instances with `c = O(n (log log n)^2 / sqrt(log n))`, and with all reductions, branch count, and affine checking overhead controlled by polynomial factors, would yield a subexponential algorithm by the conditional runtime bound. **No such universal structural reduction has been established.** Claiming one would be the hard research step, not a routine integration.
- For exact counting, a witness-only/equisatisfiability-preserving transformation is insufficient. The reduction must be **parsimonious**, or maintain a proven correction for multiplicity of assignments. Auxiliary Tseitin variables and elimination steps must be counted with care.
- Potential *research interface*, not a claim of transfer: feed OpenAI-style canonical k-CNF inputs into Witnora, measure separator profiles and affine residual coverage, and use those statistics to test a *falsifiable* structural conjecture. Positive measurements on finite families cannot prove a universal asymptotic bound.

## Independent benchmark protocol (not yet executed)

Comparators: a pinned release of CaDiCaL and Kissat for SAT/UNSAT decision, CryptoMiniSat for XOR-heavy cases, and a trusted independent DRAT checker for supported UNSAT certificates. Use separate runs with identical hardware, input, time/memory limits, pinned versions, and controlled random seeds.

Families:
- SAT Competition official CNF instances, clearly split into held-out SAT and UNSAT classes.
- CNFgen pigeonhole, Tseitin, parity/XOR, and planted/random 3-CNF across growing sizes.
- SAF(c,r) synthetic positive controls with known separator and exactly affine components.
- Negatives: families with no supported decomposition, high treewidth, and malformed/unsafe native certificates.

For each case record SHA256 of DIMACS input; family; n, m, clause length; known truth status; separator c; residual affine coverage; preprocessing and search wall times separately; peak RSS; return code; SAT witness direct check; native proof status; *external* UNSAT proof checker exit status; and independent comparator result. A timeout/unknown cannot be called UNSAT. Missing benchmark families must be reported NOT_RUN, not omitted.

Publish machine-readable raw results, command lines, environment, licenses, and scripts. Pre-register comparisons. Plot scaling of log(runtime) against n for fixed c and growing c. Report solved-instance counts and solver time as empirical performance only. No finite benchmark establishes P=NP, ETH false, or an infinite-family theorem.

## Current verdict and next executable milestone

The source review supports **a conditional TC-063 theorem plan and a falsifiable bridge hypothesis**, not a fully discharged Lean proof or a completed third-party benchmark. This environment had no `lean` or `lake` command, so no Lean kernel compilation was performed. No independent solver benchmark was executed for this audit.

Next milestone: create and run a pinned Lean/mathlib project proving Gates A-C, then link its abstract certificate semantics to Witnora's actual G5 and decomposition checker before using the word *verified*. In parallel, run the benchmark protocol with pinned binaries and publish raw results. Every unproved obligation remains open.
