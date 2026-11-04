# Witnora Rust Migration: R-009 through R-013

Research branch: `research/w-crc-001-asymmetric-v1`; draft PR #122  
Date: November 4, 2026. Lean TC-063 PR #121 unchanged.

## Verified milestones

| Milestone | Native capability | Independent checks | CI |
| --- | --- | --- | --- |
| R-009 | Standalone Rust `--fused-dimacs` exact counting (no Python) | Native Rust parser tests, SAT/UNSAT model count smoke gates; underlying R-008 [18/18 Ganak verification](RUST_008_FUSED_NATIVE_SOURCE.md) | [green #41744565521](https://github.com/joeyst8/witnora-core/actions/runs/41744565521) |
| R-010 | Native Kosaraju 2-SAT solver and witnesses, opt-in `backend="rust"` | 2,800 Rust truth-table/witness cases + 1,600 Python-original decision/witness comparisons; standalone `--two-sat-dimacs` SAT/UNSAT gates | [green #41744784538](https://github.com/joeyst8/witnora-core/actions/runs/41744784538) |
| R-011 | Canonical signed-clause normalization, DIMACS output, variables and strict subsumption | 1,600 full Python-normalization+DIMACS+subsumption differentials and native Rust unit tests | [green #41745105632](https://github.com/joeyst8/witnora-core/actions/runs/41745105632) |
| R-012 | Exact source-evidence DIMACS parser retaining every original signed numeric token spelling, raw clause, and canonical normalized formula | 1,200 Python-original text evidence comparisons and malformed-header controls | [green #41745396189](https://github.com/joeyst8/witnora-core/actions/runs/41745396189) |

R-013 has a native indexed unit-propagation/RUP-witness
producer and randomized differential gate but is **pending that gate**;
a Rust implementation by itself is not a verified replacement.

## Concrete interfaces

Two Python-free native Rust commands:

```sh
# Exact model count (or explicit s INCOMPLETE on finite budget)
printf 'p cnf 2 2\n1 0\n-2 0\n' |
  rust/witnora-ve/target/release/witnora-ve --fused-dimacs

# 2-SAT decision plus validated satisfying assignment (or UNSAT)
printf 'p cnf 2 2\n1 0\n-2 0\n' |
  rust/witnora-ve/target/release/witnora-ve --two-sat-dimacs
```

These are the first standalone Rust executable migration paths.
The Python package remains an independent reference while other
modules are migrated.

The following existing Python functions now have **opt-in** native
operation (their defaults stay Python until complete parity):

- `count_signed_cnf_crc(..., source_backend="rust_fused")`
- `solve_2sat(formula, backend="rust")`
- `find_first_subsumption(formula, backend="rust")`
- `parse_dimacs_with_text_evidence(text, backend="rust")`
- `indexed_unit_conflict_witness(database, clause, backend="rust")` (R-013 pending)

Exact original token spellings matter: a DIMACS clause such as
`+01 -002 0` must preserve those strings in the evidence record,
even though canonical CNF simplifies them to signed integers. The
native parser reproduces that behavior on its documented numeric
and resource limits. Rust-side i32 literal and 100k-clause limits
are stricter than unbounded Python parsing; outside those limits
the native path must explicitly refuse rather than reinterpret.

## Formal soundness boundaries

- R-010 produces a validated SAT witness or an UNSAT decision;
  it **does not yet emit a Lean-checkable proof certificate**.
  Calling it with the Python certificate logger is refused.
- R-012 source-evidence output is compared against the original
  parser and canonicalizer; this does not constitute a theorem
  proving the Rust parser's total correctness.
- R-013 only proposes untrusted RUP propagation units. The
  existing Lean `GeneralRUP` proof checker and reference
  replay remain the authority. Any replacement of that trust
  boundary requires a new formal verification step.
- No change has been merged to main or to TC-063 PR #121.

## Full-migration acceptance criteria

The baseline file-by-file audit identified **560 original Python
files**, comprising 148 core modules, 117 research/scripts,
and 295 tests. This is much larger than the W-CRC counting
subsystem. The tracked manifest
`research/python_to_rust_manifest.json` records the original
SHA and status of every file plus new interoperability bridges.

A full Rust transition requires equivalent Rust code for the
remaining core modules, all active CLIs/benchmarks, tests
(including adversarial controls), proof/certificate import and
replay, and every relevant CI/release workflow. The original
Python code must only be retired after those conditions are met.
This report documents concrete progress, **not** a completed
repository-wide migration.
