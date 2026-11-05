# R-092: targeted graph-theorem challenge native path

This completes the earlier R-060 partial port, which covered special-graph
constructors but left all challenge evaluation in Python. Native Rust now
computes the exact graph invariants using the R-089 backend and tests both
max/chromatic conjecture forms over the complete predeclared ordered case list.
Python remains responsible for frozen seeded sample generation and report
metadata; the opt-in `backend="rust"` returns identical counterexample lists.

The differential gate compares three complete bounded challenges, a triangle
invariant evaluation and malformed input. Counterexamples are empirical
refutations only; surviving claims are not automatically proved or novel.

Status: native Rust library, extension wheel and complete differential tests
passed in GitHub Actions #41926333458.
