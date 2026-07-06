# Finite Strictness Certificate Format

The v2.10 certificate type is `FINITE_STRICTNESS_CERTIFICATE`.

Required top-level fields:

- `certificate_id`
- `lower_grammar`
- `upper_grammar`
- `bound_profile`
- `cap_c`
- `claim_scope`
- `instances`
- `lower_bound_evidence`
- `upper_bound_evidence`
- `checker_status`
- `strictness_status`
- `forbidden_interpretations`
- `scalable_family_status`

The only successful strictness status for v2.10 is
`FINITE_STRICTNESS_CERTIFIED`.

This status is finite. It certifies only the listed finite instances under the
restricted grammar and bound profile.

It is not `PROVEN_FAMILY_THEOREM`.

It is not full `G0_BASE` strictness.

It is not hierarchy completeness.

It is not P vs NP progress.

## Instance Record

Each `InstanceStrictnessRecord` contains:

- `instance_id`
- `formula_hash`
- `family`
- `lower_result`
- `upper_result`
- `instance_checker_status`
- `claim_boundary`

The lower result includes a width obstruction certificate and the restricted
route result. The upper result includes the XOR upper-bound certificate,
extraction status, SAT/UNSAT result, and native certification level.

## Checker Rule

The checker recomputes the formula hash, replays the width obstruction, replays
the G1 XOR certificate, verifies the finite claim boundary, and rejects any
certificate that claims a scalable family theorem, full `G0_BASE` strictness,
hierarchy completeness, P vs NP progress, `HARD`, or `UNKNOWN`.
