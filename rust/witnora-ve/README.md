# Witnora Rust migration — R-001/R-002/R-003/R-004

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
