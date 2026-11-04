# R-057 — Integrated native sparse matrix to GF(2) basis gate

**Status:** Pending CI, 2026-11-04. Workflow: https://github.com/joeyst8/witnora-core/actions/runs/41861799019

The integration test `tests/test_sparse_pipeline_rust.py` is committed and referenced by `.github/workflows/rust-ve.yml`. It combines two independently verified modules:

1. `sparse_parity_checks.py` native R-056 matrix placement and verification, with Python's seeded MT19937 stream preserved at the adapter boundary.
2. `gf2_sparse_row_basis.py` native R-053 exact original-row subset selection, arbitrary-width coefficient reconstruction and independent verifier.

The test compares 250 seeded source CNFs through both native and Python stages, verifies native row-space rank via an independent pivot basis, enumerates every violation vector for small clause counts and confirms the selected basis accepts exactly those vectors accepted by the original sketch. It additionally compares every source assignment's clause-violation vector and the small finite audits, and stresses rank 136 coefficients beyond 128 bits with a synthetic row-space (explicitly **not** a valid odd-column sketch).

**No test result is claimed yet.** GitHub currently serializes Rust workflow runs on the research branch with `cancel-in-progress: false`, so R-057 remains queued. Once green, move this entry to verified milestones and update the draft PR. It adds a cross-module integration check, **not a new original Python file port**: migration counts remain 44 parallel, 516 not migrated, zero retired. No source CNF-to-parity equivalence or Lean kernel theorem is claimed.
