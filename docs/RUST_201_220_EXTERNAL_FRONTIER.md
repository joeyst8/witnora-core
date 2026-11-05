# R-201–R-220: independently checked proof-boundary experiments

Research-validation milestones, **not** migrated Python file counts.

This batch upgrades the bounded R-181–R-200 SAT/UNSAT matrix with a separately
built third-party `drat-trim` executable. The GitHub Actions workflow pins the
upstream verifier at immutable source revision
`2e3b2dc0ecf938addbd779d42877b6ed69d9a985` and runs the full 480-case
Python/Rust/native proof matrix **with external certificate checks enabled**.

| Gate | External check or trust-boundary test |
| --- | --- |
| R-201 | Width-1 original-CNF proof acceptance |
| R-202 | Width-2 acceptance |
| R-203 | Width-3 acceptance |
| R-204 | Sparse variable-label acceptance |
| R-205 | Overlapping nonlinear background acceptance |
| R-206 | Source clause shuffling/duplication acceptance |
| R-207 | Additional held-out proof seed batch |
| R-208 | Premature proof prefix rejection before contradiction |
| R-209 | Same proof rejected against weakened SAT original |
| R-210 | Forged empty clause rejected on SAT original |
| R-211 | Empty proof is not accepted |
| R-212 | Missing external checker is explicitly `NOT_RUN` |
| R-213 | Invalid verifier path never claims verification |
| R-214 | Unrelated executable cannot pose as successful verifier |
| R-215 | Proof clause budget one under threshold fails closed |
| R-216 | Proof byte budget one under threshold fails closed |
| R-217 | Exactly sufficient caps pass and proof is externally accepted |
| R-218 | External status changes only when real checker is supplied |
| R-219 | Repeated checking is deterministic |
| R-220 | Full matched SAT/UNSAT external checker batch |

**Subtle external-checking boundary:** An external proof checker can accept a
prefix that has already derived contradictory unit clauses, even without a
final textual `0` line. R-208 therefore tests a prefix *before* the actual
contradiction. The internal RUP-subset checker separately requires that an
empty clause be present in its own proof format.

Local result with the pinned verifier: all 20 external tests passed; 480/480
seeded cases passed with 240 original-CNF UNSAT proofs accepted independently.
This does not establish general SAT speed, proof complexity, Lean refinement,
or full Python-to-Rust migration.

Run:

```shell
WITNORA_DRAT_TRIM=/path/to/drat-trim python -m unittest tests.test_xor_external_201_220 -v
python -m scripts.benchmark_xor_frontier --seeds 10 --compare-rust --drat-trim /path/to/drat-trim
```

**Status:** focused native CI
[#41955834503](https://github.com/joeyst8/witnora-core/actions/runs/41955834503)
passed, including the pinned external `drat-trim` gate. Python remains the
default and the research branch stays unmerged.
