# Finite Edge Delta Certificate Format

The v2.11 certificate type is `FINITE_EDGE_DELTA_CERTIFICATE`.

Required top-level fields:

- `certificate_id`
- `lower_grammar`
- `upper_grammar`
- `bound_profile`
- `claim_scope`
- `evidence_grade`
- `instances`
- `lower_evidence`
- `upper_evidence`
- `checker_status`
- `forbidden_interpretations`
- `family_theorem_status`
- `strictness_theorem_status`

For the G1-to-G2 edge, the successful evidence grade is
`FINITE_EMPIRICAL_EDGE_DELTA_CERTIFIED`.

This status means:

1. The lower grammar replay returns bounded non-acceptance under the configured
   profile.
2. The lower replay is not treated as a lower-bound proof.
3. The upper grammar emits a checked witness or certificate.
4. The claim scope is finite.

## Instance Record

Each `InstanceEdgeDeltaRecord` contains:

- `instance_id`
- `formula_hash`
- `family`
- `lower_result`
- `upper_result`
- `instance_checker_status`
- `claim_boundary`

The lower result records `LOWER_REPLAY_NO_COLLAPSE` and has no lower-bound
certificate. The upper result records G2 symmetry witness reconstruction and
direct SAT assignment verification against the original CNF.

## Checker Rule

The checker recomputes the formula hash, replays the G1 bounded non-acceptance,
replays the G2 witness reconstruction, verifies the finite claim boundary, and
rejects certificates that claim lower-bound strictness, a G1-vs-G2 family
theorem, hierarchy completeness, P vs NP progress, `HARD`, or `UNKNOWN`.

`FINITE_STRICTNESS_CERTIFIED` remains reserved for certificates whose lower
side has a certified obstruction, such as v2.10's width lower bound.
