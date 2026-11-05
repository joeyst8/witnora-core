# R-281–R-300: independent held-out witness optimality and research sign-off

The first 19 named gates, R-281–R-299, test a research-only shortest
odd-parity cycle witness finder against an *independent exhaustive simple-cycle
subset enumerator* (maximum 13 graph edges). The remaining R-300 gate
checks the manifest frontier, original source-file counts, preserved default
Python/RUP/DRAT boundaries, and CI wiring.

## Held-out evidence

The frozen 72-case test samples new connected graphs of 3–8 vertices, with
up to four random consistent chords and one deliberately inconsistent edge.
It includes 24 additional SAT controls, checks the original CNF by exhaustive
truth-table enumeration, checks the shortest inconsistent cycle by an
independent edge-subset oracle, and subjects both full and cycle-guided
candidate proofs to independent original-CNF RUP and real pinned `drat-trim`.

**Local outcome:** all 72 contradictory-CNF cases passed both independent
checkers, all 24 SAT controls remained satisfiable, and the witness path was
shorter on 16/72 cases, tied on 56/72, and longer on 0/72. This is evidence
within this frozen, narrow synthetic family only; it does not predict results
on arbitrary formulas or on representative SAT competition instances.

An additional exploratory **200-case local** run with the same pinned
external verifier passed (67 SAT controls; 42 shorter witness proofs, 158
ties, zero regressions). This extended run is not part of the frozen 72-case
native CI gate and should not be presented as such.

### Named gates

| Gates | Research boundary |
| --- | --- |
| R-281–R-286 | Exhaustive minimum odd-cycle oracle on 3–8 vertices |
| R-287 | Held-out sample accounting |
| R-288 | Oracle edge cap fails closed |
| R-289 | Non-binary XOR graph input rejected |
| R-290 | BFS minimum cycle length matches independent enumeration |
| R-291 | Deterministic replay on frozen new seeds |
| R-292 | No witness-regression and pinned improvement count |
| R-293 | Paired SAT-control accounting |
| R-294 | SAT graph has no contradictory cycle |
| R-295 | Sparse variable relabeling |
| R-296 | Clause-order invariance |
| R-297 | No checker means no external certification |
| R-298 | Invalid external checker fails closed |
| R-299 | Independent held-out seed-window replay |
| R-300 | Read-only full frontier/accounting/default-gate audit |

The milestone series R-181–R-300 consists of test and research-development
checkpoints; it does **not** mean 120 additional original Python files have
been migrated. The 560 original Python files and 470/76/14 status split remain
unchanged. The default application path is still Python; Lean and real
external DRAT verification are independent trust boundaries.

```shell
WITNORA_DRAT_TRIM=/path/to/drat-trim python -m unittest tests.test_xor_heldout_281_299 -v
python -m scripts.benchmark_xor_heldout_281_299 --samples 72 --compare-rust --drat-trim /path/to/drat-trim
python -m unittest tests.test_r300_manifest_audit -v
python -m scripts.audit_witnora_r300
```

**Status:** R-300 focused native CI
[#41958473142](https://github.com/joeyst8/witnora-core/actions/runs/41958473142)
passed, including the pinned independent verifier, Rust/Python comparisons
and R-300 audit. Readiness means research branch saved and regression-gated
for further review; it is not a release, main-branch merge, complete Rust
migration, general SAT performance guarantee or P-vs-NP proof.
