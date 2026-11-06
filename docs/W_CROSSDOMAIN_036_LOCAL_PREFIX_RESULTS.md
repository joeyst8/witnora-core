# W036-A — Source-verified local signed-incidence prefix gate: negative external result

## Protocol and evidence

- Original W036 protocol: `docs/W_CROSSDOMAIN_036_LOCAL_CERTIFICATE_PROTOCOL.md`.
- Deterministic selector: `scripts/w036_local_gate.py`; 1%, 2%, 5% original source prefix budgets, at most three anchors, 16/32/64 source-clause caps. Only exact original source clauses retained.
- GitHub Actions run [42164804233](https://github.com/joeyst8/witnora-core/actions/runs/42164804233), **passed**.
- Code commit `9fde5693b585ce91d2ea52ca1f90ada0140ed5b1`.
- Frozen sixteen cases: eight original independently SHA-verified INRIA VLSAT2 external CNFs plus the eight source-frozen W030 synthetic/decoy controls. Original external labels and compressed/decompressed hashes are those in W022/W032; synthetic source bytes match W030 manifest.
- Original raw evidence: `research/results/w036_local_raw.json.gz`. Compressed SHA256 `31788a3aeed1544ebb95f53179455a5c9ada7e0c07d89e11178599ed3f79dea8`, decompressed SHA256 `002602484baebbe92dd85410fe94f804675ed9bb71de918b60f23ffc2cf0b115`.
- Each record retains prefix clauses and bytes read, selector time, selected original source indices plus source-selected SHA256, and bounded DPLL/unit/global Fourier/weighted Fourier outcomes with separate times. Weighted positives must pass exact integer source-clause re-verification, and a positive on a SAT source aborts.

## Main result — source cases with at least one UNSAT proof

Each entry below is a **count of distinct source formulas**, not repeated candidate/neighborhood trials. There are eight external cases and eight frozen controls.

| Source group | Prefix | Neighborhood cap | Unit propagation | Bounded DPLL | Global Fourier | Weighted Fourier LP |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| External VLSAT2 | 1%, 2%, or 5% | 16, 32, or 64 | **0/8** | **0/8** | **0/8** | **0/8** |
| Frozen controls | 1% | 16 | 0/8 | 0/8 | 0/8 | 0/8 |
| Frozen controls | 1% | 32 or 64 | 0/8 | **1/8** | 0/8 | 0/8 |
| Frozen controls | 2% | 16 | 0/8 | 0/8 | 0/8 | 0/8 |
| Frozen controls | 2% | 32 or 64 | 0/8 | **1/8** | 0/8 | 0/8 |
| Frozen controls | 5% | 16 or 32 | 0/8 | 0/8 | 0/8 | 0/8 |
| Frozen controls | 5% | 64 | 0/8 | **1/8** | 0/8 | 0/8 |

The sole success is `w030_d8192_r0_unsat_corefirst`: bounded DPLL on source-selected clauses found a contradiction. The weighted Fourier certificate produced no proofs, so it delivered **zero incremental source-certified value** above the classical DPLL baseline in this pilot. No false UNSAT classifications were observed on source-labeled SAT cases.

## Cost and selector robustness

Median individual computation times on the eight external cases (not whole-pipeline measurements):

- Prefix read: approximately **0.167, 0.282, and 0.484 ms** for 1%, 2%, and 5%, respectively.
- Local neighborhood construction: approximately **0.69 ms** per 16-clause cap selection, **0.66 ms** per 32-clause cap, **0.77 ms** per 64-clause cap (all anchor ranking included).
- Per selected neighborhood: bounded DPLL median **0.129 ms**, weighted LP + integer audit median **1.614 ms**.

The single control success at 1% or 2% was found with a 32-clause cap, but **disappeared at 5% with that same cap** and reappeared at a 64-clause cap. This non-monotonic behavior is caused by changing anchor-neighborhood selection when more source clauses are observed, not by a source proof becoming invalid. It is a risk for adaptive gating and makes monotonic detection or a persistent proof cache worth testing.

## Boundaries and decision

W036-A is **only a prefix-local proof-coverage and separate-component timing experiment**. It is *not* a cost-inclusive Kissat versus hybrid benchmark, and no general external SAT speedup is established. The source verification/decompression cost is common setup, excluded from the measured prefix-gate component times. We did not run the pinned Rust XOR extractor on every selected neighborhood in this first stage; the prior global W032 extractor is not equivalent to a local XOR comparison.

The current weighted LP detector is not competitive as an unconditional prefix gate: 0/8 external certificates and more CPU per neighborhood than bounded DPLL. Recommended W036-B test is a single **fixed** (not post-selected) gate budget and proof mechanism, with exact Rust XOR and Kissat complete pipeline, or a redirect to structurally informative **predictive statistics** with proper held-out evaluation. Any future claims must charge source reads, selection, fallback, subprocess and proof checking.

No P-versus-NP conclusion follows.
