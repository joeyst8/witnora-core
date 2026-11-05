# R-261–R-280: contradictory constraint-cycle witness pilot

The experimental `scripts/benchmark_xor_cycle_frontier.py` constructs
connected graphs of *complete*, two-variable XOR CNF constraints from planted
assignments, then flips a closing edge to create an inconsistent cycle.
Additional chords increase the graph's cycle rank. The current general
native/Python sparse row schedule is compared with a **research-only**
shortest contradictory parity-cycle witness extractor.

The cycle witness uses BFS over `(vertex, cumulative parity)` states. It does
not use privileged knowledge of the flipped edge or the planted assignment;
the independent original-CNF RUP checker and pinned `drat-trim` verify proofs
from both the full source set and the smaller witnessed source subset.

| Graph vertices | Chords | Shortest inconsistent cycle | Baseline proof clauses | Cycle-guided proof clauses |
| ---: | ---: | ---: | ---: | ---: |
| 3 | 0 | 3 | 5 | 5 |
| 4 | 0 | 4 | 7 | 7 |
| 5 | 1 | 3 | 5 | 5 |
| 6 | 1 | 5 | 9 | 9 |
| 8 | 2 | 4 | 7 | 7 |
| 10 | 3 | 5 | 13 | 9 |
| 12 | 4 | 3 | 5 | 5 |
| 16 | 5 | 6 | 25 | 11 |
| 20 | 6 | 6 | 31 | 11 |
| 40 | 10 | 11 | 67 | 21 |

R-261–R-270 pin the ten graph configurations. R-271 validates that the
returned edge set is a closed, inconsistent cycle; R-272–R-273 independently
check cycle rank and exact original-CNF source accounting; R-274–R-276 check
relative proof lengths and the observed `2*cycle_length-1` witness pattern;
R-277–R-279 protect the SAT control, relabeling and clause permutations;
R-280 demands rejection when a source clause supporting the witness is
removed from the original CNF.

This is a restricted witness-selection improvement, **not** a complexity
theorem, general SAT solver or trusted UNSAT claim without the external gate.
Native Rust remains opt-in and the production Python path is unchanged.

```shell
WITNORA_DRAT_TRIM=/path/to/drat-trim python -m unittest tests.test_xor_cycles_261_280 -v
python -m scripts.benchmark_xor_cycle_frontier --compare-rust --drat-trim /path/to/drat-trim
```

**Status:** focused native CI
[#41957568052](https://github.com/joeyst8/witnora-core/actions/runs/41957568052)
passed, including Rust/Python comparison and external certification of both
proof candidates. No merge/release approval.
