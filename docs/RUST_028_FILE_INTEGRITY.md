# R-028 — independent Rust certificate file-integrity checks

Status: **GREEN**, [GitHub Actions #41760669462](https://github.com/joeyst8/witnora-core/actions/runs/41760669462).

`rust/witnora-ve/src/bundle_manifest.rs:first_digest_failure`
independently checks the supplied manifest's ordered file SHA-256
entries against UTF-8 payload contents. It returns the first error
in the existing Python verifier's format (`missing file NAME` or
`file hash mismatch for NAME`), and rejects duplicate physical
file names.

The new native `verify_certificate_file_digests_native` PyO3
entry point is used by the opt-in
`verify_certificate_bundle(..., file_hash_backend="rust")`.
The existing Python integrity check remains the default.

## Verification

- 1,200 deterministic randomized certificate file sets covering
  correct contents, missing entries and changed payloads, checked
  against Python's original first-failure behavior.
- Real SAT, UNSAT and multi-component `.wcert` files passed the
  Python and opt-in Rust verifier paths equally.
- Tampering with the `certificate_hash.txt` payload caused the
  Rust and Python verification paths to reject identically with
  `failed_check="file_hash"`.
- All previous native proof, counting and certificate differential
  checks remained green in the same complete CI workflow.

## Limits

This is the **file-digest layer** of bundle verification. The
remaining Python semantic replay, trust level checks, certificate
schema validation, DRAT/LRAT and Lean proofs are not replaced by
this milestone. Python remains the default implementation and
independent reference. Draft PR remains unmerged. No Python files
have been removed.
