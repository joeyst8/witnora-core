# Native G14/G5 three-size benchmark (v47)

Draft PR #48. CI: https://github.com/joeyst8/witnora-core/actions/runs/41241367721

## Results

Three Python-generated structured UNSAT-cover instances from the same family, each with two separator branches, a different selected UNSAT component per branch, and authentic native G5 initial rows and indexed operations.

| Components per branch | Source clauses | Lean source check (one run) | Max RSS |
|---|---:|---:|---:|
| 2 | 12 | 0.93 seconds | 346,632 KiB |
| 3 | 16 | 1.13 seconds | 357,616 KiB |
| 4 | 20 | 1.39 seconds | 371,188 KiB |

All generated Lean source checks succeeded. Each source-level UNSAT theorem's axiom report was `[propext, Classical.choice, Quot.sound]`; no `sorry` or `Lean.ofReduceBool`. The existing generator's negative controls also checked omitted component and invalid G5 reference rejection for all three sizes. Python tests asserted exact residual-component counts and distinct branch-selected native G5 UNSAT components.

The emitter printed SHA-256 hashes of each source's Python DIMACS bytes to aid reproducibility; those hashes are not yet independently bound to a remote/original TC-063 source identity.

## Interpretation and next work

The timings are single measurements of small, related formulas in one CI environment; no asymptotic claim or generalization to difficult TC-063 instances follows. Proof source length, clause count and component count all changed together, so the benchmark does not isolate a single complexity driver.

Next: locate the original TC-063 source and G5/G14 artifact identities, run their integrity/format preflight, and enumerate the exact checker premises that fail. Do not claim target verification before all source and certificate inputs pass Lean.
