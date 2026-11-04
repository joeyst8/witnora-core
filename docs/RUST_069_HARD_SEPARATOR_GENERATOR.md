# R-069 — Seeded planted hard-separator CNF generator (native verified)

The single public generator in `hard_separator_families.py` now has an opt-in
native Rust assembly path. Python preserves the exact `Random(seed)` stream,
including 3-variable samples, random literal signs and the forced positive
literal when all sampled signs are negative. Rust independently builds the
canonical XOR boundaries, checks sampled local 3-CNF rows, and canonicalizes
the complete source formula.

The native differential gate covers all 12 preregistered `(blocks,core_vars,
width)` combinations across 8 deterministic seeds each: **96 exact
source-CNF hashes, complete clause lists and metadata records**, plus the
all-true planted satisfying assignment and invalid-grid rejection.

# [Focused native CI run #41881170943](https://github.com/joeyst8/witnora-core/actions/runs/41881170943)
passed on 2026-11-04: Rust library unit tests, production-wheel compilation,
and all three R-067/R-068/R-069 Python/Rust differential suites. In particular,
the R-069 suite checked all **96** seeded hard-separator source instances.
The corresponding Python module is now marked `parallel_reference` (48 of 560
source files verified), not retired. The planted witness establishes SAT for
those constructed instances; the word “hard” in the experiment name is
not a proof of computational hardness or a complexity-theory result.

## Native fixture correction

The focused [Rust run #41880243498](https://github.com/joeyst8/witnora-core/actions/runs/41880243498)
compiled the crate and passed 95 library tests, but the R-069 unit fixture
incorrectly reused a first-block clause on the second block. The native
generator correctly returned `invalid planted signed clause`. The fixture
now uses block-specific variables and separately asserts rejection of the
cross-block contamination. The subsequent focused run #41881170943 passed
both the corrected unit fixture and the 96-case differential gate.
