# Witnora Rust migration — R-001

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
