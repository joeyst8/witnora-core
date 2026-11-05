# R-221–R-240: measured proof-growth boundary

The new controlled scaling family encodes both possible parities of the
*same* width-`w` XOR, each as its complete original CNF. Each instance is
UNSAT. The research-only benchmark records exact original-CNF digest,
certificate digest, source clauses, proof clauses and bytes, while separately
checking internal RUP and external `drat-trim` acceptance.

**Observed on widths 1–10:** this specific exporter generates exactly
`2**w - 1` proof clauses and peak proof width `w - 1` for this family. This
is an exponential **output-size observation about this implementation**, not
a general lower bound on resolution, proof complexity or SAT algorithms.

| Width | Source CNF clauses | DRAT proof clauses | DRAT proof bytes |
| ---: | ---: | ---: | ---: |
| 1 | 2 | 1 | 2 |
| 2 | 4 | 3 | 11 |
| 3 | 8 | 7 | 39 |
| 4 | 16 | 15 | 115 |
| 5 | 32 | 31 | 307 |
| 6 | 64 | 63 | 771 |
| 7 | 128 | 127 | 1,859 |
| 8 | 256 | 255 | 4,355 |
| 9 | 512 | 511 | 9,987 |
| 10 | 1,024 | 1,023 | 23,553 |

R-221–R-230 individually pin widths 1–10. R-231–R-233 check the exact
recurrence and byte-growth pattern; R-234–R-236 check proof-count and byte
cap cutoffs; R-237 independently enumerates the original CNFs on widths
1–6; R-238 pins deterministic source and proof hashes; R-239 enforces
explicit external-verifier reporting; and R-240 tests the bounded input
domain. Separate tests cover real `drat-trim` and Rust/Python equality.

The local external checker accepted proofs for all widths 1–10, and a
separate exploratory width-12 sample reached 4,095 proof clauses and
122,869 proof bytes. The width-12 sample is **not** part of the focused
regression gate because of its much higher internal RUP verification cost.

```shell
WITNORA_DRAT_TRIM=/path/to/drat-trim python -m unittest tests.test_xor_scaling_221_240 -v
python -m scripts.benchmark_xor_proof_scaling --max-width 10 --compare-rust --drat-trim /path/to/drat-trim
```

**Status:** focused native Rust CI
[#41956471056](https://github.com/joeyst8/witnora-core/actions/runs/41956471056)
passed, including independent external proof verification and Rust/Python
comparison. No production behavior, default Python path, source-file status,
Lean kernel or main branch is changed by this study.
