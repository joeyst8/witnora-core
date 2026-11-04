# R-073 — Benchmark source families (native verified)

The bounded benchmark and theorem-example CNF family helpers in `families.py`
now have opt-in Rust backends. Rust constructs canonical blocked-clique,
bounded-treewidth chain, multiple BCE component, mixed-component, unit
contradiction and tautological-noise formulas. For seeded random 2-CNF and
3-CNF generators, Python retains its exact MT19937 draw and rejection stream;
Rust canonicalizes the sampled raw clauses without changing source identity.

The new native differential suite includes deterministic cases of 40 widths
and multiple BCE component counts, 400 seeded random 2/3-CNF samples, exact
clause-list and SHA-256 comparisons, and invalid-input controls. Python
remains the default reference backend, and no theorem or complexity result
is inferred from these generator tests. [Focused CI #41885949696](https://github.com/joeyst8/witnora-core/actions/runs/41885949696)
passed Rust library tests, native wheel build, and R-073 differential suites.
This module is now `parallel_reference`: **51/560** source files verified.
