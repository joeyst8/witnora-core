# Rust migration checkpoint: R-097 through R-113

This record documents implementation versus independent verification. It is
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

## Implemented, native verification outstanding

| Milestones | Scope | Verification boundary |
| --- | --- | --- |
| R-107 | GF(2) ANF algebra | First wheel build failed due Rust type inference; fix committed later |
| R-108 | Exact bounded symbolic Shannon counter | Requires successful rerun of compiled Python extension comparisons |
| R-109 | ANF residual component sizes | Requires native 340-case and separator-search comparison |
| R-110 | Bounded ANF separator selection | Requires complete candidate/budget native comparison |
| R-111 | Structured ANF counter with forced units and component splits | Requires full value and internal-statistic comparison |
| R-112 | Composed native separator-conditioned counting | Requires native composition comparison |
| R-113 | Native algebra in clause/source/row parity pipeline | Requires CNF/row/basis output comparison |

The GitHub connector confirmed each fast-forward branch update, but
`github_fetch_commit_workflow_runs` returned no *pull-request-triggered*
focused runs for R-109 through R-113. Consequently, no pending item is
promoted to a verified status. The last verified manifest counts remain
76 `parallel_reference`, 9 `partial_native_verified`, 475 `not_migrated`
out of 560 Python entries. The partially migrated modules include other
historically verified counterparts; milestone counts are not file counts.

## Resume protocol

1. Resolve the GitHub Actions trigger / PR visibility gap or obtain a
   working Rust toolchain with PyO3 to run the focused native gate.
2. Verify R-107 through R-113 in ascending order, fixing all differential
   or Rust compilation errors before counting any promotion.
3. Update `research/python_to_rust_manifest.json` only for independently
   verified paths, with exact CI run identifiers.
4. Continue R-114 onward. Next promising targets are the remaining source
   ANF evaluation and separator-conditioned experimental kernels, then the
   larger proof/replay and runner modules; each needs a separate differential
   or proof-gate definition.
5. Retain Python fallbacks, independent benchmarks, and Lean kernel trust
   until the entire 560-file migration is verified. Never merge the research
   branch into `main` without explicit review and approval.

No P-vs-NP, TC-063, or mathematical novelty claim is promoted by this work.
