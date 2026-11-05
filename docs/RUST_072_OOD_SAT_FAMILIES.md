# R-072 — Out-of-distribution SAT family constructors (native verified)

All five canonical CNF construction kernels in `ood_sat_families.py` now have
opt-in Rust equivalents: pigeonhole, graph coloring, bounded complete-graph
Tseitin XOR (including K4), N-queens and planted satisfiable 3-CNF assembly.
The two named benchmark bundles propagate the backend selection to every
member. The Python source remains the default reference implementation.

Python preserves its original seeded MT19937 witness, variable samples and
literal draws for planted 3-CNF; Rust validates the supplied witness and
three-distinct-variable signed clauses before assembling the exact canonical
formula. No RNG translation is claimed.

The focused gate compares complete clause lists and SHA-256 source identities
over deterministic grids (35 pigeonhole, 80 graph-coloring, 8 N-queens,
10 Tseitin), 200 seeded planted sources, and 12 named benchmark bundle runs,
plus invalid input controls. The independent source tests continue to run.

This is an experimental generator migration. No statement that a source is
computationally hard or that Rust establishes a SAT theorem follows from
source identity alone. [Focused CI #41885387466](https://github.com/joeyst8/witnora-core/actions/runs/41885387466)
passed Rust library tests, wheel build and all R-072 source comparisons.
The module now counts as `parallel_reference`, bringing the total to
**50/560** verified Python-file counterparts.
