# W027 Phase 1: frozen exploratory end-to-end smoke test

Status: **prospective smoke-test addendum** to the larger preregistered
W027 protocol. Commit before running the first solver comparison.

This is **not** the full 96-pair / 8-external-file W027 study, and its
timings must not be presented as the final W027 speedup estimate.

## Pinned cases and arms

- Synthetic W026 source: D=0 and D=8192, replicate r=0, both SAT and
  UNSAT partners: four CNFs. Use the exact previously verified W026
  generator, with an independent planted-witness check.
- W022 publisher-pinned external files: vlsat2_684_9417 (UNSAT) and
  vlsat2_1000_22250 (SAT). Require the original decompressed SHA-256
  hashes from research/results/w022_external_vlsat2.json.
- Three arms: plain Kissat rel-4.0.4, Witnora Rust precheck then Kissat
  on the unaltered source CNF unless proof-certified UNSAT, and
  CryptoMiniSat release/v5.17.0 if reproducibly buildable. Record exact
  source commits rather than relying only on tag names.
- Three repetitions per source/arm; rotate arm order by sample index
  and repetition. One Ubuntu host; 2 GiB per-process address-space
  cap and **6-second wall limit per full arm invocation**, including
  Witnora preprocessing. Time spent downloading/building is excluded.

## Correctness and raw data

- Validate SAT models against all original source clauses. Reject
  unverified or missing SAT witnesses as errors.
- Independently reconstruct every source 3-XOR quartet and verify the
  source-row XOR identity of every Witnora short-circuit certificate.
- Treat timeouts as censored observations, preserve all repetitions,
  record source hash, solver source SHA, time cap, exit code, full
  pipeline wall time, preprocessing duration, downstream duration,
  and error statuses. Never treat a timeout as a verdict.
- If CryptoMiniSat cannot build reproducibly, report its arm as
  unavailable and continue a transparently reduced two-arm smoke.
- Record per-case median timings only where a solver actually returned
  a checked verdict; do not use censored samples in a speedup ratio.

Phase 1 is a pipeline/correctness test. Completion of W027 itself
requires the entire separately frozen full-study protocol.
