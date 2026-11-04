# R-026 — native certificate bundle file-hash manifests

Status: **GREEN**, [GitHub Actions #41759581109](https://github.com/joeyst8/witnora-core/actions/runs/41759581109).

Rust now computes the exact UTF-8 SHA-256 `files` digest map for the
existing certificate bundle format. See
`rust/witnora-ve/src/bundle_manifest.rs` and the
`certificate_file_digests_native` PyO3 entry point. The native
implementation sorts names, rejects duplicate file names, and fails on
empty/NUL names. The Python adapter
`certificate_bundle_file_hashes(..., backend="rust")` preserves the
original output structure.

The public `export_certificate_bundle(..., hash_backend="rust")`
opt-in now uses native Rust to fill the actual export's
`manifest.json.files` digests; the normal Python export is unaffected.

## Independent tests

- 1,200 deterministic random UTF-8 certificate text maps, including
  non-ASCII, control and newline characters, compared to Python
  `hashlib.sha256`, plus duplicate/invalid-name controls.
- Genuine SAT, UNSAT and multi-component `.wcert` exports using the
  opt-in Rust hash path matched the original Python manifests and
  payload files exactly, and were accepted by Witnora's existing
  `verify_certificate_bundle`.
- All previous Rust proof, arithmetic and independent Ganak checks
  passed in the same dedicated gate.

## Limits

This is an incremental replacement of the **file-hash manifest**
inside bundle generation, not full native Rust certificate file
construction, directory/JSON writing, DRAT/LRAT production or
independent verifier migration. Python remains the default and
independent reference. Lean trust is unchanged. The draft research
branch remains unmerged; no original Python was deleted.
