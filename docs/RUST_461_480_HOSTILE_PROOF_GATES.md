# R-461–R-480: hostile original-CNF proof boundary

The fail-closed tests use the nonlinear-background UNSAT family to exercise
adversarial mutations at the proof exporter boundary:

- Omit a selected row's encoded source clause from the original CNF and reject
  both semantic source provenance and proof emission.
- Forge the selected row parity, or supply duplicate, missing, negative or
  Boolean indices, and reject the source/dependency witness.
- Accept candidate proofs with exact clause/byte caps, but reject each cap
  reduced by one. Zero budgets must also fail closed.
- Keep independent SAT original-CNF controls distinct from UNSAT candidates.
- Require unchanged-original internal RUP verification and separately pinned
  `drat-trim`; Rust/Python candidate equality is also checked in focused CI.

The test intentionally does not assert that arbitrary *deletions* of CNF source
clauses preserve satisfiability: they need not. It asserts only that the
original-source proof gate rejects modified input before claiming a certificate.

Reproduce:

```sh
WITNORA_DRAT_TRIM=/path/to/pinned/drat-trim python -m unittest tests.test_xor_hostile_461_480 -v
python -m scripts.benchmark_xor_hostile_461_480 --samples 32 --drat-trim /path/to/pinned/drat-trim
```

No new Rust production behavior is enabled by these research-only tests.
