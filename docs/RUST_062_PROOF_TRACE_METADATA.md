# R-062 — Native UNSAT trace metadata recognizer (partial, pending CI)

An opt-in Rust predicate reproduces the conservative format/status-field
screen used by `is_supported_native_unsat_trace`. The Python adapter checks
types before crossing the native boundary; metadata fields must match exact
known literals. It does **not** replay a collapse path, validate a proof,
certify UNSAT, or export DRAT/LRAT/FRAT.

The native differential gate covers both recognized UNSAT reason strings,
600 deterministic randomized mutations of five fields, and null input.
Native PyO3 CI must pass before the function is treated as verified. The
source `proof_trace.py` remains partially migrated because the native proof
trace property comes from its Python certificate model.

## Malformed-input gate correction

GitHub Rust run [#41868911840](https://github.com/joeyst8/witnora-core/actions/runs/41868911840)
compiled and passed preceding R-057 through R-061 steps, but R-062 uncovered
that the original Python reference raised `TypeError` for an unhashable
`unsat_reason` list/dict. The Python reference now fails closed (returns
False) for non-string reasons, consistent with the Rust opt-in wrapper.
This is input hardening, not acceptance of a new trace or a proof claim.
