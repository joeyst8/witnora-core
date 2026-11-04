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
