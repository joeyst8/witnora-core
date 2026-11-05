# R-179/R-180: research-branch readiness boundary

**R-179** is a reproducible read-only manifest audit. It checks that the
original 560 Python files still exist, statuses sum correctly, the XOR proof
milestones are gap-free, the branch is research-scoped, and experimental
proof/verification controls default to their previous Python/fail-safe paths.

**R-180** is the sign-off checkpoint *after* the final focused CI has passed:
the operator must record the exact CI run, audit the unchanged Lean and
external DRAT trust boundaries and mark the research effort as ready for
further review **only**, not merged, released, or fully migrated.

The R-number frontier tracks scoped research work and regressions, **not**
560 separately migrated source files. A green R-180 gate is not a complete
Python-to-Rust migration, a Lean proof, a new SAT complexity result, or proof
of superiority over an independent solver.

**Status:** R-175–R-179 focused CI #41952269269 is green. The final R-180
manifest-frontier audit is pending CI; do not treat this file as a release
approval, main-branch merge or complete Python-to-Rust migration.
