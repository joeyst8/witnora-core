# R-046: source-bound native parity-spoke discovery

**Green full gate:** https://github.com/joeyst8/witnora-core/actions/runs/41836911014

## Migration

`witnora_core/spoke_discovery.py` is now reproduced by `rust/witnora-ve/src/spoke_discovery.rs` across all three exports: exact binary-XOR equations, canonical two-edge spoke paths, and contradictory endpoint-syndrome discovery. The implementation reuses the independently tested complete source-CNF two-clause XOR matcher from R-041. The original Python functions are unchanged. Rust access is explicit through the `_rust` adapters and PyO3.

## Independent tests

`tests/test_spoke_discovery_rust.py` compared **1,200** seeded random CNFs and **100** planted contradictory two-spoke routes against the original Python equation lists, path tuples, and full candidate dictionaries. Every returned equation witness was independently compared with the canonical complete XOR source encoding and checked as a subset of the actual source formula. Incomplete single-clause patterns were rejected. Full Rust unit, Python differential and Ganak CI passed.

## Trust

Every contradiction remains `UNVERIFIED_STRUCTURAL_CANDIDATE` and `NOT_LEAN_VERIFIED`. The source-bound Lean certificate checker is separate and unchanged. These are established GF(2) parity consistency observations, not new SAT inference, proof acceptance or polynomial-time complexity claims.

Migration inventory: **34** parallel-reference Python modules, **526** pending, **0** original Python modules removed.
