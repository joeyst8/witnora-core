# Rust migration checkpoint: R-097 through R-118

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

## Implemented, native verification outstanding

| Milestones | Scope | Verification boundary |
| --- | --- | --- |
| R-111 | Structured ANF counter with forced units and component splits | Native build was blocked by `BigUint` shift type inference in a test; explicit shift type now patched |
| R-112 | Composed native separator-conditioned counting | Requires native composition comparison |
| R-113 | Native algebra in clause/source/row parity pipeline | Requires CNF/row/basis output comparison |
| R-114 | Arbitrary-width ANF assignment evaluation | Requires native 350-seed and high-bit comparison |
| R-115 | One-call native clause violation compilation | Requires native 400-seed comparison |
| R-116 | One-call native source-CNF compilation | Requires native 220-seed comparison |
| R-117 | One-call native parity-row construction | Requires native 162-seed sketch/basis comparison |
| R-118 | Native parity-ANF geometry metrics | Requires native 216-seed geometry comparison |

GitHub Actions push runs were initially invisible to the
`github_fetch_commit_workflow_runs` wrapper, which filters to pull-request
events; the Actions REST run collection exposed them. Focused push CI
#41936430000 verified R-107–R-110. The R-111 onward failures through
#41938700797 were caused by an ambiguous shift literal in an R-111 Rust
unit test. The fix is staged for a new CI run. Manifest counts remain
76 `parallel_reference`, 11 `partial_native_verified`, 473 `not_migrated`
out of 560 Python entries after the R-107–R-110 evidence update. Distinct
milestone numbers are not the same as distinct source-file counts.

## Resume protocol

1. Inspect push-triggered GitHub Actions workflow runs through the Actions
   REST collection; retrieve failed job logs to diagnose the native gate.
2. Verify R-111 through R-118 in ascending order, fixing all differential
   or Rust compilation errors before counting any promotion.
3. Update `research/python_to_rust_manifest.json` only for independently
   verified paths, with exact CI run identifiers.
4. Continue R-119 onward. Next promising targets are the remaining native
   separator-conditioned experimental kernels, then the
   larger proof/replay and runner modules; each needs a separate differential
   or proof-gate definition.
5. Retain Python fallbacks, independent benchmarks, and Lean kernel trust
   until the entire 560-file migration is verified. Never merge the research
   branch into `main` without explicit review and approval.

No P-vs-NP, TC-063, or mathematical novelty claim is promoted by this work.
