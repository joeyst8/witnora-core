# R-050: native iterative articulation hints for TC-063

**Full CI green:** https://github.com/joeyst8/witnora-core/actions/runs/41840498387

## Migration

Ported `witnora_core/separator_structural_priority.py` to `rust/witnora-ve/src/separator_structural_priority.rs`. The Rust implementation uses an explicit iterative Tarjan-style DFS with discovery and low-link values to identify articulation vertices in undirected, symmetric primal graphs. It also produces the full deterministic singleton priority order: cut vertices first, ranked by descending degree and vertex ID, followed by every remaining vertex exactly once. The original Python functions are unchanged; Rust adapters are opt-in.

## Verification

`tests/test_separator_priority_rust.py` compared **1,500** seeded random undirected graphs (1–30 vertices) with the original Python outputs **and an independent remove-the-vertex connectivity oracle**. A separate series of paths up to 512 vertices checked deep iterative traversal and exact articulation enumeration. Invalid asymmetric graphs fail closed on the Rust path. Full Rust compiler/unit, Python and Ganak CI passed.

## Trust

This is a fast heuristic for prioritizing candidate vertices in TC-063. The exact recognizer must still validate accepted candidates and preserve the exhaustive fallback. Neither detecting a cut vertex nor reordering candidates constitutes a Lean proof or a complexity-class result.

Migration inventory after R-050: **38** parallel Rust counterparts, **522** not migrated, **0** original Python files removed.
