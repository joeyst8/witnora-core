# R-036: native pre-CD transitions and component-local suffix

**Verified green:** https://github.com/joeyst8/witnora-core/actions/runs/41769073739

## Scope

The R-035 single-root CD stream checker is extended with
`component_context_replay::replay_prefixed_root_cd`, which verifies
an arbitrary sequence of root-local proof transitions **before** a CD
step and then resumes component-local transitions after authenticated
child CNFs have been created. Global step indices and first failure
messages are preserved across the CD boundary.

`replay_prefixed_component_certificate_native` and the opt-in Python
adapter `replay_prefixed_component_certificate_in_rust` expose this
scoped capability without changing the default Python verifier.

## Independent verification

`tests/test_component_prefix_rust.py` creates **240** deterministic
multi-stage streams with a valid unit-propagation prefix, subsequent
component decomposition and per-child unit replay. It compares
complete results against Python's `verify_collapse_path`, including
corrupted prefix assignments, CD input hashes, component counts,
context IDs and final formula hashes. The full Rust, Python and Ganak
workflow passed, preserving R-001 through R-035 checks.

## Exclusions

Exactly one root CD is supported. Nested CD, arbitrarily interleaved
component root contexts, component-result claims and final SAT/UNSAT
soundness are not yet provided by this native replay. Original
Python code and Lean proof trust remain unchanged, with 24 original
Python files partially mirrored and 536 not yet migrated.
