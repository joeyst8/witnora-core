# R-025 — byte-compatible native certificate JSON and SHA-256

Status: **GREEN**, [dedicated Rust differential gate #41757030196](https://github.com/joeyst8/witnora-core/actions/runs/41757030196).

## Scope

A new native Rust serializer in `rust/witnora-ve/src/certificate_json.rs`
reproduces Python's `json.dumps(data, indent=2, sort_keys=True) + "\\n"`
byte-for-byte for an explicit proof data subset: Unicode strings,
signed 64-bit integers, booleans, nulls, lists, tuples and dictionaries
with string keys. The implementation reproduces Python's ASCII escape
policy (including UTF-16 surrogate pairs for non-BMP code points),
stable key sorting, line breaks, indentation, and trailing newline.
It computes SHA-256 directly over the emitted UTF-8 bytes.

The `stable_certificate_json_native` PyO3 function returns both
serialized text and hash. Python's existing `stable_json(data)`
remains the default. Callers can explicitly opt in via
`stable_json(data, backend="rust")`. The native interface rejects
non-string map keys, integers larger than signed i64, floats and
unsupported types rather than silently changing certificate bytes.

## Verification

`tests/test_certificate_json_rust.py` compares 1,600 seeded,
randomly nested JSON-compatible inputs with the original Python
serializer and independent `hashlib.sha256` digests. It includes
Unicode, emoji, escaped control characters, tuples, nulls and ordered
objects, plus explicit invalid input controls.
All earlier native, original Python and Ganak checks also passed in the
same CI gate.

## Limitations

This milestone does **not** implement full `.wcert` bundle export,
certificate manifest generation, filesystem and DRAT proof export,
floating-point JSON compatibility or general Python JSON semantics.
Those remain independent migration stages. Python remains default;
Lean trust and the original verifier remain untouched. No Python
files were deleted and the full 560-file transfer is not complete.
