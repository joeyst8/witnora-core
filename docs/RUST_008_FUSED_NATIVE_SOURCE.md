# Witnora R-008: Fused Exact Rust Source-to-Count

Date: 2026-11-04  
Research branch: `research/w-crc-001-asymmetric-v1` (draft PR #122)  
Status: **Verified R-008**, no merge

## What changed

Previously, the source-CNF pipeline crossed Python/Rust boundaries
for source preprocessing, complete k≤3 XOR extraction, GF(2)
projection, left Fourier expansion, right inclusion-exclusion
coefficients, and the final exact contraction.

`rust/witnora-ve/src/fused_source.rs` now runs **all of those
operations in one Rust function**. Python integration is an optional
single-call wrapper, `witnora_core/crc_rust_fused.py`, selected using
`count_signed_cnf_crc(source, nvars, source_backend="rust_fused")`.
All intermediate rational coefficients remain exact arbitrary-precision
signed dyadics, and the count is checked nonnegative and integral.
The native algorithm returns an explicit incomplete result on its hard
caps and emits no guessed model count. The original Python path
remains the default/reference.

## Verification

Dedicated [green Rust CI run #41743900472](https://github.com/joeyst8/witnora-core/actions/runs/41743900472).

- Rust crate unit tests passed.
- Four R-008 Python integration test methods passed.
- Random source: **210 seeded small formulas**, each under
  `none`, `rust_consensus`, `rust_adaptive`: **630 differential
  counts** matching exhaustive truth tables and the original Python
  pipeline, plus source-validity/refusal controls.
- Independent exact model counter **Ganak matched 18/18** benchmark
  cases. Structured sources used 12–60 variables, 3-OR and complete
  3-XOR blocks; forcing families used 8, 32, 64 variables.
- 64-variable forcing family contained **4,095 source clauses**,
  simplified and counted exactly as two models.
- Large 60-variable case yielded
  **79,792,266,297,612,001 exact models** and matched Ganak.

## Whole-source runtime comparison (release CI runner)

Both timed arms include source preprocessing and extraction and
start with the same original CNF. The baseline is the staged
Rust-PyO3 path with Rust preprocessing, Rust XOR, Rust left and
Rust right coefficient engine; the challenger is one native fused
Rust-PyO3 call. Two repetitions per method per instance, 12-second
per-run cap, plus independent Ganak (not included in the timing ratio).

| Source family | staged Rust | fused Rust | fused/staged |
| --- | ---: | ---: | ---: |
| Four separate 3-OR blocks (n=12) | 1.9968 ms | 0.0411 ms | 0.021 |
| Twenty 3-OR blocks (n=60) | 0.3411 ms | 0.1501 ms | 0.440 |
| Twenty blocks, six complete XOR gadgets (n=60) | 0.4770 ms | 0.1791 ms | 0.375 |
| Dense forcing (n=64, 4,095 clauses) | 3.4496 ms | 2.7384 ms | 0.794 |

All **18/18** instances were faster in this specific comparison.
The observed median fused/staged ratio was **0.333**. These are
tiny and structured instance families, not a broad #SAT benchmark.
The gains arise in part from avoiding repeated Python/Rust calls;
they are not a complexity-theory discovery.

## Hard limitations

- The native right-side method is exact **bounded inclusion-exclusion**
  with component factoring. More entangled CNFs can exhaust budgets.
- No formal Lean theorem about the Rust implementation has been proven;
  the Rust code is experimentally differentially verified only.
- This migration is not complete. The repository contained **560 original
  Python files at the baseline audit** (148 core, 117 scripts,
  295 tests). The active manifest
  `research/python_to_rust_manifest.json` tracks these original
  files individually. No original Python source was removed.
- Separate R-009 DIMACS CLI and R-010 two-SAT work are subsequent
  migration milestones, not part of this R-008 verification.

## Next acceptance gate

Keep the original Lean TC-063 proof PR #121 unchanged.
Port the remaining core algorithms and proof-aware workflows into
native Rust, preserve original source semantics on independent
controls, and remove Python only after the equivalent Rust
implementation and workflows pass.
