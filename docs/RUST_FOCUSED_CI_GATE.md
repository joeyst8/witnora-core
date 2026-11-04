# Focused native Rust migration CI

The existing full Rust migration gate runs a long collection of independent
benchmarks and has `cancel-in-progress: false` serialization. A slow or stale
workflow completion can hold up verification of later source-module ports.

The read-only focused gate uses a **separate concurrency group**, builds the
same Rust crate and Python wheel, runs native library tests and exercises
R-067 hidden-separator, R-068 symbolic-implication, R-069 planted-source,
and R-070 SAT-library structural fingerprint differential tests without the
unrelated Ganak benchmark suite.

This is an additional gate, not a replacement for the full suite or Lean.
It never commits, modifies certificates, merges pull requests, or declares
mathematical proof. A green focused gate supports the named component tests;
the broader full gate remains necessary for release-level validation.

The workflow also listens to `pull_request` synchronization and limits that
event to draft PR #122, in addition to research-branch pushes. This addresses
the possibility that a newly added, non-default-branch workflow is not
discovered immediately under the push-only subscription. Both paths remain
read-only and share the focused workflow's separate concurrency group.
