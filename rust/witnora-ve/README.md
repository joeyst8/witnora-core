# Witnora Rust migration — R-001/R-002/R-003/R-004/R-005/R-006

The `witnora-ve` executable **and optional PyO3 in-process extension**
are a native, bounded, exact #SAT **component counter**, ported from Python's W-CRC-015 indexed
sum-product variable elimination. It is **not** a full SAT solver,
proof of a new complexity class, or a replacement for Lean's formal
certificate checker. The existing Python code remains a differential
reference until native verification is complete.

## Build and test

```sh
cargo test --manifest-path rust/witnora-ve/Cargo.toml --release
cargo build --manifest-path rust/witnora-ve/Cargo.toml --release
python -m pip install "maturin>=1.9,<2"
maturin build --manifest-path rust/witnora-ve/Cargo.toml --release --features python --out rust/witnora-ve/wheels
python -m pip install rust/witnora-ve/wheels/*.whl
WITNORA_RUST_VE_BIN=rust/witnora-ve/target/release/witnora-ve \
  python -m unittest tests.test_crc_rust_backend -v
```

The binary accepts a strict line-oriented text protocol on stdin:

```
p witnora-ve 3 2 3 100000
v 1 2 3 0
1 2 0
2 3 0
```

The first line selects exactly **three explicit variables**, two
clauses, max intermediate factor scope 3 and 100,000 operations.
The `v` line lists exactly those variables, ending in zero. Each
following clause has signed literals ending in zero. The native
output is either `EXACT <models> <operations> <width> <variables>`
or `INCOMPLETE`; malformed inputs produce an explicit error and
a nonzero process exit.

`num-bigint` preserves exact model counts beyond 64/128 bits.
Bounds and invalid source inputs fail closed; there are no guessed
counts on budget refusal. This is standard exact variable
elimination with worst-case exponential intermediate width.

Python can select `component_backend="variable_elimination_rust"`
inside `count_source_by_separator`. If the PyO3 extension is installed,
its **in-process** entry point is preferred. Otherwise configure
`WITNORA_RUST_VE_BIN` to use the executable. The default remains
Python enumeration. Passing an explicit `binary_path` to the bridge
forces the CLI path for differential tests. Compare complete timings:
subprocess startup costs more than the native kernel on small inputs.

## Native source simplification (R-003)

The same crate also exports `simplify_source_native`, an **opt-in**
source-preserving 2-CNF/CNF preprocessor. It removes tautologies and
duplicates, performs unit propagation while retaining forced unit
clauses, and applies the exact consensus identity
`(A ∨ x) ∧ (A ∨ ¬x) ⇔ A` in deterministic, bounded passes.
It preserves the **entire assignment set**, not just satisfiability;
explicit source variable counts are kept even if clauses disappear.

Python calls it via `witnora_core/crc_rust_preprocess.py` and
`count_signed_cnf_crc(..., source_preprocessor="rust_consensus")`.
The `"none"` default is unchanged. The native extension must be
installed; budget exhaustion returns incomplete instead of inventing a
result. It is not a Lean-certified transformation.

To verify in a development checkout after installing the PyO3 wheel:

```sh
WITNORA_RUST_VE_BIN=rust/witnora-ve/target/release/witnora-ve \
  python -m unittest tests.test_crc_rust_preprocess -v
WITNORA_RUST_VE_BIN=rust/witnora-ve/target/release/witnora-ve \
  python -m scripts.benchmark_rust_preprocess
```

[Verified R-003 CI](https://github.com/joeyst8/witnora-core/actions/runs/41736318985)
passed nine native Rust tests, four Python source tests and 12/12 exact
Ganak count comparisons. For n=64 pairwise-forcing CNF, 4,032 original
clauses reduced to 63; full source-count time improved from 185.03 ms to
3.40 ms on that benchmark runner **with preprocessing included**.
An unchanged parity family slowed from 18.32 to 23.27 ms, so selective
admission/benchmarking is necessary. These are narrow pilot results,
not generic SAT/#SAT superiority. See
`docs/RUST_003_SOURCE_PREPROCESS.md` for full methodology and limits.

## Adaptive admission gate (R-004)

For source families that have no direct binary consensus pairs,
`source_preprocessor="rust_adaptive"` invokes the native polarity-mask
admission check, then **returns the original source unchanged** if no
opportunity is seen. Any admitted source still passes through the
fully exact, bounded R-003 transformation. This opt-in heuristic may
miss useful preprocessing, but skipping a transformation cannot make
the model count incorrect. The original `"none"` default remains.

[Verified R-004 CI](https://github.com/joeyst8/witnora-core/actions/runs/41737533969)
passed 10 Rust tests, five Python integration tests including 120 new
full-model-set controls and 12/12 independent Ganak counts. The gate
skipped all four parity cases and admitted all eight forcing cases.
In n=64 parity, raw 27.27 ms vs always-preprocess 29.82 ms vs
adaptive 28.15 ms (admission overhead included). In n=64 forcing,
raw 257.01 ms vs adaptive 3.82 ms on the same runner.
These are two-repeat controlled measurements, **not** a general
SAT solver improvement. See `docs/RUST_004_ADAPTIVE_SOURCE_ADMISSION.md`.

## Exact small-XOR extraction (R-005)

The crate now implements `extract_small_xors_native` to identify
**complete** 1-, 2-, and 3-variable XOR clause blocks and leave
incomplete patterns in the residual CNF. It produces arbitrary-precision
equation support masks (up to variable ID 256) and preserves the exact
source model set. The strict Python bridge is
`witnora_core/crc_rust_xor.py` and the source counter opts in via
`count_signed_cnf_crc(..., source_extractor="rust")`; the original
`"python"` remains the default. This works with opt-in
`source_preprocessor="rust_adaptive"` or `"rust_consensus"`.

After building/installing the PyO3 wheel, verify with:

```sh
WITNORA_RUST_VE_BIN=rust/witnora-ve/target/release/witnora-ve \
  python -m unittest tests.test_crc_rust_xor -v
WITNORA_RUST_VE_BIN=rust/witnora-ve/target/release/witnora-ve \
  python -m scripts.benchmark_rust_xor
```

[Verified R-005 CI](https://github.com/joeyst8/witnora-core/actions/runs/41738553647)
passed 13 Rust tests, four new Python tests with 280 exact-output and
model-set differential cases, and **12/12 independent Ganak matches**.
On n=64 pairwise parity, full adaptive-preprocessing plus source-count
latency fell from 38.08 ms with Python extraction to 21.06 ms with
Rust extraction on the same hosted runner (~1.81x). On n=64 forcing,
it fell 5.43 to 4.59 ms (~1.18x). Two-repeat case studies are not
broad solver benchmarks. Complete controls, data and caveats:
`docs/RUST_005_EXACT_XOR_EXTRACTION.md`.

## Exact batched right Walsh coefficients (R-006)

The new `right_walsh_native` PyO3 entry point computes the entire
requested set of right-CNF Walsh coefficients in **exact dyadic
arithmetic**, using standard component-wise inclusion-exclusion.
The native operation takes canonical zero/one violation masks and
outputs decimal numerator/denominator pairs; no floating-point
rounding is involved. Strict Python `Fraction` conversion is in
`witnora_core/crc_rust_walsh.py`.

Both `count_asymmetric_boundary` and `count_signed_cnf_crc` can opt
in via `coefficient_backend="rust_inclusion_exclusion"`.
The `"python"` default stays unchanged. The Rust path preserves
the Python inclusion-exclusion subset limit and adds a
`max_rust_coefficient_operations` limit for batched Walsh modes.
When a native cap refuses, the opted-in path returns incomplete
**without silently switching to the Python Shannon/orbit oracles**.

After installing the PyO3 wheel, the verification and benchmark are:

```sh
WITNORA_RUST_VE_BIN=rust/witnora-ve/target/release/witnora-ve \
  python -m unittest tests.test_crc_rust_walsh -v
WITNORA_RUST_VE_BIN=rust/witnora-ve/target/release/witnora-ve \
  python -m scripts.benchmark_rust_walsh
```

[Green R-006 CI](https://github.com/joeyst8/witnora-core/actions/runs/41740113548)
passed **17 Rust tests**, four new Python differential tests including
whole small CNF Walsh spectra and full affine/source counts, and
**16/16 independently counted Ganak cases**. On n=60 with three
three-variable parity blocks crossing 20 disjoint OR components,
full affine-plus-coefficient time was **0.7021 ms Python versus
0.2218 ms Rust**, ~3.17x for this specific family. The benchmark
deliberately excludes earlier source preparation and source XOR
extraction; three very short repeats are not a general solver ranking.
See `docs/RUST_006_RIGHT_WALSH_COEFFICIENTS.md`.

## Migration policy

- Preserve Lean TC-063 formal proof artifacts unchanged.
- Preserve the Python indexed backend as an independent reference.
- Compare exact models, operation charges, widths, and source
  refusals on random/structured controls and independent Ganak.
- Run an isolated Rust GitHub Actions gate on each research change.
- Do not silently fall back from Rust to Python, or accept a Rust
  integer as a formal proof certificate.
- Port additional algorithms only after this stage is verified,
  benchmarked, and reviewed.
