# R-035: native single-root CD with component-local proof stream

**Verified green:** https://github.com/joeyst8/witnora-core/actions/runs/41768449283

## Scope

A new Rust module `component_context_replay.rs` checks one root
component-decomposition (CD) step, materializes authenticated child
CNFs, then follows further component-scoped local proof transitions
using the independently tested `local_replay` checker. It maintains
per-component states, verifies global step numbering, input and output
hashes, component ownership, and the canonical recombined final formula.

The PyO3 `replay_root_component_certificate_native` and opt-in
`witnora_core.verifier_rust.replay_root_component_certificate_in_rust`
adapter intentionally reject nested CD rather than silently claiming
support. Default Python behavior is unchanged.

## Tests

`tests/test_component_stream_rust.py` generates **360** deterministic
disconnected CNF proof streams with root CD and component-local UP
steps. Complete authentic paths and forged CD component counts,
incorrect component IDs, missing scope tags, corrupted assigned
literals and final hashes are cross-checked against the **full**
Python `verify_collapse_path` reference. Valid final reconstructed
formula states match exactly. The entire Rust, Python and Ganak
verification workflow was green.

## Trust boundary

This checker is a **bounded proof-transition stream verifier**:
nested component decompositions, global certificate result records,
assignment-merging and SAT/UNSAT status soundness remain outside this
Rust milestone. No original Python sources were removed. Lean proofs
and final certificate trust have not been modified. Inventory remains
24 partially mirrored and 536 untouched original Python files.
