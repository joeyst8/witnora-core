# Witnora research prior-art gate (2026-11-05)

## Required workflow for every new research problem

Before calling a technique new, or starting a large implementation:

1. **Specify the problem** precisely: source representation, outputs, claimed
   structure, resource bounds, and a falsifiable result.
2. **Search primary literature** (original papers, proceedings, author
   preprints, verified code/reproducibility artifacts). Record search terms,
   dates, citations, and how each result relates to the proposed method.
3. **Inspect existing Witnora code** to avoid reimplementing a proven
   technique that is already available in Rust or Python.
4. **Reproduce an established baseline** on the exact input family, including
   malformed/adversarial cases and independent source-CNF checks.
5. **Implement applicable improvements in Rust by default**, retaining
   independent Python/Lean/external reference checks. Follow upstream code
   licensing and attribution; reuse mathematical ideas with proper citation,
   not unlicensed copied source code.
6. **Benchmark and falsify** on held-out instances against credible external
   solvers. Distinguish known methods, engineering improvements, restricted
   new theorems, and unsupported generality. If literature already solves
   the problem, acknowledge that explicitly and test whether Witnora needs
   adaptation instead of claiming novelty.

Do not elevate a model count, hash match, heuristic cut, or candidate proof
to verified SAT/UNSAT without the applicable independent evidence gate.
This workflow is a research requirement, not automatic permission to
download and execute third-party code or merge unreviewed changes.

## Cross-disciplinary discovery track

Actively test connections from other fields—algebraic topology, coding theory,
information theory, statistical mechanics/partition functions, tensor-network
contraction, spectral graph theory, and algebra—when they can be translated to
an **exact statement** about Witnora's source constraints. Do not stop at an
analogy. Every proposed bridge needs:

1. An explicit mapping from signed source CNF to the external mathematical
   object, with assumptions and information lost in the mapping.
2. A literature check in **both** domains; a known identity or technique is
   not Witnora novelty.
3. A small exact counterexample/falsification test, including source formulas
   that share the proposed feature but have different answers.
4. An opt-in Rust diagnostic or algorithm, independent finite tests, and
   source/proof authority kept separate.
5. A held-out benchmark against existing Witnora routes and external solvers.
   Retire the feature if it does not improve prediction or execution.

The first tracked test is
[W-CROSSDOMAIN-001 topology × #SAT](W_CROSSDOMAIN_001_TOPOLOGY.md). Its
flag-complex Betti number is established mathematics; only a future
reproducible solver benefit or separately proved new theorem could support
a genuine Witnora contribution.

The second tracked cross-domain test is
[W-CROSSDOMAIN-002 signed-graph balance × XOR](W_CROSSDOMAIN_002_SIGNED_CYCLES.md).
It shows why a graph's unlabeled topological holes cannot determine parity
consistency, and reuses the existing Rust source-bound odd-cycle machinery.

## Initial application: W-STRUCT-001/002 small separators and #SAT

The W-STRUCT-001 finding (same n, clause count and primal density, different
minimum separators) is elementary graph structure, **not a novel parameter**
or an established predictor of solver runtime. The literature already
contains stronger structural measures and algorithms:

| Primary work | Established result / relevance | Witnora consequence |
| --- | --- | --- |
| Samer and Szeider, *Algorithms for Propositional Model Counting* (2010), https://www.ac.tuwien.ac.at/files/pub/SamerSzeider10.pdf | Exact #SAT dynamic programming using primal, dual, and incidence tree decompositions; width-dependent complexity. | Compare separator signatures to width-based baselines. Avoid claiming small separators alone solve #SAT generally. |
| Slivovsky and Szeider, *A Faster Algorithm for Propositional Model Counting Parameterized by Incidence Treewidth* (2020), https://pmc.ncbi.nlm.nih.gov/articles/PMC7326555/ | Algebraic transforms improve the dependence on incidence width. | Evaluate existing width/DP paths before proposing new transforms. |
| Bacchus, Dalmao and Pitassi, *Algorithms and Complexity Results for #SAT and Bayesian Inference* (2003), https://eccc.weizmann.ac.il/eccc-reports/2003/TR03-003/index.html | Memoized DPLL/component caching provides a known exact-counting algorithmic framework. | Use as an algorithmic baseline for dynamic decomposition. |
| Sharma et al., *GANAK: A Scalable Probabilistic Exact Model Counter* (2019), https://meelgroup.github.io/publication/ijcai19_ganak/ | Engineering improvements through probabilistic component caching and heuristics. | Compare counts/runtimes while retaining independent exact or proof checks; Ganak's default cache has a small correctness-risk qualification. |
| *Proofs for Propositional Model Counting* (SAT 2022), https://drops.dagstuhl.de/entities/document/10.4230/LIPIcs.SAT.2022.30 | Model-counting proof traces for major exact approaches. | Keep proof/certificate production separate from independent checking. |

### Already implemented locally; do not duplicate blindly

- `rust/witnora-ve/src/treewidth.rs`: bounded exact width/order search
  and independent order-width verification; **not** a general tree-decomposition
  #SAT dynamic-programming engine.
- `rust/witnora-ve/src/anf_separator_conditioning.rs`: bounded exact
  separator conditioning for polynomial/ANF scope families.
- `rust/witnora-ve/src/crc_cutset_count.rs`: bounded exact cutset-conditioned
  counting for the CRC representation.

The next W-STRUCT-002 gate is therefore **an apples-to-apples experiment**:
matched-size/density sources with measured separator profiles, source-exact
counts, native Witnora routes, and external counters. Record preprocessing,
runtime, peak memory, state budgets, and all incomplete cases. Only implement
a new Rust method if the controlled comparison reveals a real gap in these
existing paths.

**Current status:** literature triage and code mapping complete; no general
novelty, performance win, or new formal theorem is established by this note.
