# R-027 — Rust certificate identity SHA-256

Status: **GREEN** in the complete native Rust gate
[GitHub Actions #41760143662](https://github.com/joeyst8/witnora-core/actions/runs/41760143662).

The certificate hash in `CollapsePath.certificate_hash` is computed
by SHA-256 over Python's *compact*, sorted-key JSON form
(`json.dumps(payload, sort_keys=True, separators=(",", ":"))`).
This format is intentionally distinct from R-025 pretty stable JSON.

The new Rust `compact_certificate_hash_native` entry point produces
both exact compact JSON and SHA-256, using the strict recursively
validated proof-data subset of null, boolean, signed i64, string,
lists/tuples and string-keyed maps. Python now offers the explicit
`CollapsePath.certificate_hash_with_backend(backend="rust")`
opt-in. The existing `certificate_hash` property retains its
original Python semantics.

## Verification

- 1,200 randomized nested payloads produced byte-identical compact
  JSON and independent `hashlib.sha256` parity against Python.
- Genuine SAT, UNSAT, and multi-component certificate paths reconstructed
  from standard `.wcert` exports produced identical native and
  original Python certificate identity hashes.
- The full R-001..R-027 CI workflow, including independently counted
  SAT/#SAT source cases, was green.

## Limits

This stage migrates the **identity hash computation** but does not
replace native certificate payload construction, full general-purpose
JSON (floats deliberately reject), complete file export, trust levels,
external proof checking or independent verification. The default stays
Python and the Lean checker remains unchanged. No files were removed
from the original 560-file migration inventory.
