# Witnora Rust migration — R-138–R-179 checkpoint

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
| R-155–R-156 | Optional dual Python/Rust RUP verification and fail-closed disagreement | Focused CI #41949612200 green |
| R-157–R-158 | Original DIMACS canonical source identity and fail-closed rejection | Focused CI #41949970796 green |
| R-159–R-160 | Dual Python/native source-DIMACS canonical parser agreement and failure gate | Focused CI #41950366667 green |
| R-161–R-162 | Native emitted proof candidate syntax/count/size auditing and fail-closed mismatch | Focused CI #41950774606; full native CI #41950774608 green |
| R-163–R-166 | Held-out contradictory XOR proofs, independent RUP, tampering and source-order metamorphic tests | Focused CI #41951202624 green |
| R-167–R-170 | Mixed nonlinear source-CNF and resource-cap differential stress | Focused CI #41951668179 green |
| R-171–R-174 | Opt-in native proof controls surfaced in certificate exporter and CLI | Focused CI #41951668179 green |
| R-175–R-178 | Adversarial relabel/caps/malformed-trace/missing-source controls | Implemented; **CI pending** |
| R-179 | Read-only manifest accounting and default trust-gate audit | Implemented; **CI pending** |
| R-180 | Final research-branch readiness sign-off | **Not yet reached** |

All native interfaces are optional. The unmodified Python reference remains
the default. Native derivation produces candidate clauses, never a trusted
UNSAT verdict. Independent RUP, `drat-trim` and Lean checks remain mandatory
where the existing workflow requires them.

## Final gate

R-180 may be signed only after the focused R-175–R-179 run is green and this
checkpoint identifies its exact run. It will mean completion of the scoped
**research milestone batch**, not the entire 560-file migration or Lean proof.
No merge into `main` is authorized by this checkpoint.
