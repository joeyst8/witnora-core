# Rust migration checkpoint: R-097 through R-134

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
| R-121–123 | XOR support normalization, evaluation, substitution | Focused Rust push CI #41940786252 passed |
| R-124–125 | Batch XOR system substitution, full Gaussian solver with trace | Focused Rust push CI #41941245719 passed |
| R-126–127 | XOR assignment verification and bounded complete XOR CNF | Focused Rust push CI #41941696815 passed |
| R-128–130 | Witness clause overlap, composed and full native source XOR detection | Focused Rust push CI #41942185395 passed |
| R-131–132 | Native XOR sidecar parser and signed-clause resolvent | Focused Rust push CI #41942614415 passed |

## Implemented, native verification outstanding

| Milestones | Scope | Verification boundary |
| --- | --- | --- |
| R-133 | Native sparse GF(2) min-fill row-operation schedule | Requires native 120-seed exact trace comparison |
| R-134 | Native sparse XOR elimination order report | Requires native 100-seed report comparison |

GitHub Actions push runs were initially invisible to the
`github_fetch_commit_workflow_runs` wrapper, which filters to pull-request
events; the Actions REST run collection exposed them. Focused push CI
#41936430000 verified R-107–R-110. Early R-111 failures exposed an ambiguous
`BigUint` shift literal; after that fix, CI #41939496083 exposed faulty
random 3-CNF test fixtures. The subsequent corrected full CI #41940030217
passed, establishing R-111–R-119. Focused CI #41940376154 passed R-120.
Focused CI #41940786252 passed R-121–R-123, and focused CI #41941245719
passed R-124–R-125. Focused CI #41941696815 passed R-126–R-127.
Focused CI #41942185395 passed R-128–R-130. R-131–R-132 are implemented
and verified by CI #41942614415. R-133–R-134 remain pending native CI.
Current manifest counts are 76 `parallel_reference`, 14
`partial_native_verified`, 470 `not_migrated` out of 560 Python entries. Distinct
milestone numbers are not the same as distinct source-file counts.

## Resume protocol

1. Inspect push-triggered GitHub Actions workflow runs through the Actions
   REST collection; retrieve failed job logs to diagnose the native gate.
2. Verify R-133 through R-134, fixing any differential
   or Rust compilation errors before counting any promotion.
3. Update `research/python_to_rust_manifest.json` only for independently
   verified paths, with exact CI run identifiers.
4. Continue R-135 onward. Next promising targets are the remaining native
   experimental kernels, then the
   larger proof/replay and runner modules; each needs a separate differential
   or proof-gate definition.
5. Retain Python fallbacks, independent benchmarks, and Lean kernel trust
   until the entire 560-file migration is verified. Never merge the research
   branch into `main` without explicit review and approval.

No P-vs-NP, TC-063, or mathematical novelty claim is promoted by this work.
