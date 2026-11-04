# R-080: Rust claim-boundary scanner

The release-text heuristic in `witnora_core/claim_boundary.py` now has a
native Rust scanner for claim phrases, conservative context markers, exact
finding order and human-readable context windows. The existing Python scanner
remains the default; `backend="rust"` also supports file aggregation through
the unchanged Python I/O layer.

The differential suite compares 240 seeded context windows, Unicode-adjacent
text, standalone HARD/UNKNOWN boundaries and multi-file aggregation. The
scanner is a textual guardrail, not a formal proof of claim correctness.

Verified: **focused Rust CI #41911341176 passed** library tests, native wheel
build, and all Python/Rust differential suites. The manifest now records R-080
as `parallel_reference`.
