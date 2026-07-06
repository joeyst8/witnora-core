# Finite Strictness Certificate

v2.10 defines a reusable finite strictness certificate for the restricted edge
`G0_WIDTH_C` versus `G1_XOR_FOR_STRICTNESS`.

The certificate checks a finite list of witness instances. For each instance it
replays two obligations:

1. `G0_WIDTH_C` rejects the formula because the exact width obstruction exceeds
   cap `c`.
2. `G1_XOR_FOR_STRICTNESS` accepts the formula because exact XOR extraction and
   native GF(2) certificate verification succeed.

`FINITE_STRICTNESS_CERTIFIED` is a machine-checked finite-instance certificate,
not a scalable family theorem.

This does not prove full `G0_BASE` strictness.

This does not prove the hierarchy is strict.

This does not prove P vs NP.

Scalable Tseitin/expander strictness remains a proof obligation.

## Certificate Files

The v2.10 runner emits:

- `finite_strictness_certificate.json`
- `finite_strictness_checker_result.json`
- `instance_strictness_records.json`
- `finite_strictness_summary.csv`
- `width_obstruction_replay_summary.json`
- `xor_upper_bound_replay_summary.json`
- `scalable_family_proof_obligations.json`
- `FINITE_STRICTNESS_CERTIFICATE_REPORT.md`

## Claim Boundary

The lower grammar is restricted to `G0_WIDTH_C`. The certificate does not make
a claim about UP, PLE, SUB, BCE, components, 2SAT, or all safe preprocessing
routes in full `G0_BASE`.

Native XOR certificates are not DRAT unless a DRAT proof is separately exported
and checked against the original CNF.

## Relationship To Finite Edge Delta Certificates

v2.11 adds `FINITE_EMPIRICAL_EDGE_DELTA_CERTIFIED` for hierarchy edges where the
lower grammar only has bounded replay non-acceptance. That is not a lower-bound
proof.

`FINITE_STRICTNESS_CERTIFIED` remains reserved for finite certificates like
v2.10 where the lower grammar rejection is backed by a certified obstruction,
such as width lower bound greater than the configured cap.

v2.12's external reproducibility package preserves this distinction in the
evidence summary and claim-boundary table.
