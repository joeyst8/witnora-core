# Witnora Rust migration — R-138–R-156 checkpoint

This is a proof-boundary-preserving migration record. Milestone numbers are
development checkpoints, **not** 1:1 counts of the 560 original Python files.

| Milestone | Work | Current verification |
| --- | --- | --- |
| R-138–R-142 | Native XOR proof encoding/format/size/cap control and bounded variable-elimination candidate | Focused CI #41946908938; full native CI #41946908913 green |
| R-143–R-144 | Native source-row maps and source values, 180-seed differential | Same two green runs |
| R-145–R-146 | Parent-ID and GF(2) row-operation semantic validation, 420-seed differential | Focused CI #41947535584 green |
| R-147–R-148 | Native canonical XOR result encoding and source clause-union, 450 seeded comparisons | Focused CI #41947535584 green |
| R-149–R-150 | Parent-row resolution closure and expected-encoding admission with exact proof-line/cap comparison | Focused CI #41948198829; full native CI #41948198826 green |
| R-151–R-152 | Whole row-trace candidate assembly with exact status, output and budget accounting | Focused CI #41948721033; full native CI #41948719469 green |
| R-153–R-154 | Opt-in exporter backend and unchanged independent RUP/`drat-trim` verification gate | Focused CI #41949183652 green |
| R-155–R-156 | Optional dual Python/Rust RUP verification and fail-closed disagreement | Implemented; **native CI pending** |

All native interfaces are optional. The unmodified Python reference remains
the default. Native derivation produces candidate clauses, never a trusted
UNSAT verdict. Independent RUP, `drat-trim` and Lean checks remain mandatory
where the existing workflow requires them.

## Proposed R-157–R-180 sequence (NOT IMPLEMENTED)

| Proposed numbers | Required work and acceptance gate |
| --- | --- |
| R-157–158 | Canonical source-CNF identity admission and mismatch failure before proof certification |
| R-159–162 | Proof replay, independent `drat-trim`, source-CNF identity and integrity preservation |
| R-163–166 | Diagnostic metadata, error precedence, missing external checker and timeout cases |
| R-167–170 | Source-to-proof end-to-end parity across XOR CNF families, randomized and adversarial out-of-distribution tests |
| R-171–174 | CLI/runner dispatch, artifact handling, Python fallback behavior and reproducible benchmarking |
| R-175–178 | Independent full regression against existing verification gates; memory/time/overflow and large-instance tests |
| R-179–180 | Final research-branch readiness audit, exact manifest update, explicit remaining Python/Lean gaps and independent CI sign-off |

This proposed sequence is a guide, not evidence of completion. Stop and repair
any failing intermediate gate before promoting further milestone numbers. No
merge into `main` is authorized by this checkpoint.
