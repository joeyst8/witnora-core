# Rust migration checkpoint: R-097 through R-123

This record distinguishes implementation from independent verification. It is
not a claim of a complete Python-to-Rust replacement and does not amend any
Lean trust boundary.

## Verified in native GitHub CI

| Milestones | Scope | Evidence |
| --- | --- | --- |
| R-097 | Exact bounded DSATUR k-colorability | Focused Rust CI #41932752484 passed |
| R-098–099 | Bounded local recoloring, Kempe swaps | Focused Rust CI #41933655931 passed |
| R-100–101 | Two-step Kempe repair, greedy clique bound | Focused Rust CI #41934106459 passed |
| R-102–103 | Frozen selector signals/rules, greedy DSATUR witness | Focused Rust CI #41934598441 passed |
| R-104–105 | Components, graph bounds, constructive nonedge matching | Focused Rust CI #41934932659 passed |
| R-106 | Selector confusion aggregation | Focused Rust CI #41935280778 passed |
| R-107–110 | ANF algebra, bounded counter, residual components, separator search | Focused Rust push CI #41936430000 passed |
| R-111–119 | Structured and conditioned counters, native source/row/geometry and scope-adjacent operations | Focused Rust push CI #41940030217 passed full Rust library, wheel and Python differential gate |
| R-120 | Exact ANF polynomial scope masks | Focused Rust push CI #41940376154 passed |

## Implemented, native verification outstanding

| Milestones | Scope | Verification boundary |
| --- | --- | --- |
| R-121 | GF(2) support toggle/sort normalization | Requires native 400-seed comparison |
| R-122 | XOR partial-assignment evaluation | Requires native 500-seed comparison |
| R-123 | XOR partial substitution preserving equation metadata | Requires native 500-seed comparison |

GitHub Actions push runs were initially invisible to the
`github_fetch_commit_workflow_runs` wrapper, which filters to pull-request
events; the Actions REST run collection exposed them. Focused push CI
#41936430000 verified R-107–R-110. Early R-111 failures exposed an ambiguous
`BigUint` shift literal; after that fix, CI #41939496083 exposed faulty
random 3-CNF test fixtures. The subsequent corrected full CI #41940030217
passed, establishing R-111–R-119. Focused CI #41940376154 passed R-120.
R-121–R-123 remain implemented and pending native CI.
Current manifest counts are 76 `parallel_reference`, 12
`partial_native_verified`, 472 `not_migrated` out of 560 Python entries. Distinct
milestone numbers are not the same as distinct source-file counts.

## Resume protocol

1. Inspect push-triggered GitHub Actions workflow runs through the Actions
   REST collection; retrieve failed job logs to diagnose the native gate.
2. Verify R-121 through R-123, fixing any differential
   or Rust compilation errors before counting any promotion.
3. Update `research/python_to_rust_manifest.json` only for independently
   verified paths, with exact CI run identifiers.
4. Continue R-124 onward. Next promising targets are the remaining native
   experimental kernels, then the
   larger proof/replay and runner modules; each needs a separate differential
   or proof-gate definition.
5. Retain Python fallbacks, independent benchmarks, and Lean kernel trust
   until the entire 560-file migration is verified. Never merge the research
   branch into `main` without explicit review and approval.

No P-vs-NP, TC-063, or mathematical novelty claim is promoted by this work.
