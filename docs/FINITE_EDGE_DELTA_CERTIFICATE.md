# Finite Edge Delta Certificate

v2.11 introduces `FINITE_EDGE_DELTA_CERTIFICATE` for hierarchy edges where the
lower grammar has replay evidence but no certified lower-bound obstruction.

For the current edge:

- lower grammar: `G1_XOR`
- upper grammar: `G2_SYMMETRY_CERTIFIED`
- evidence grade: `FINITE_EMPIRICAL_EDGE_DELTA_CERTIFIED`
- claim scope: `FINITE`

The lower replay records `LOWER_REPLAY_NO_COLLAPSE` for selected cycle
3-coloring instances. This is bounded replay evidence only. It is not a proof
of non-membership in `W_B(G1_XOR)` and not a lower-bound theorem.

The upper replay records native G2 symmetry witness reconstruction. The checker
verifies the symmetry certificate path and verifies that the reconstructed SAT
assignment satisfies the original CNF.

## Certificate Files

The v2.11 runner emits:

- `finite_edge_delta_certificate.json`
- `finite_edge_delta_checker_result.json`
- `instance_edge_delta_records.json`
- `lower_g1_replay_summary.json`
- `upper_g2_replay_summary.json`
- `finite_edge_delta_summary.csv`
- `edge_delta_claim_boundary.json`
- `FINITE_EDGE_DELTA_G1_G2_REPORT.md`

## Claim Boundary

`FINITE_EMPIRICAL_EDGE_DELTA_CERTIFIED` records a finite replayed delta, not a
lower-bound strictness theorem.

Unlike v2.10's finite strictness certificate, v2.11 does not provide certified
lower-bound obstruction for the lower grammar.

This does not prove `G1_XOR` is strictly weaker than
`G2_SYMMETRY_CERTIFIED` as a theorem.

This does not prove a family theorem.

This does not prove P vs NP.

Native symmetry certificates are not DRAT unless a DRAT proof is separately
exported and checked against the original CNF.
