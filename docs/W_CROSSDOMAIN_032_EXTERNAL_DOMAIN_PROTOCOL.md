# W032 external-domain validation — frozen source pilot

**Preregistered before timing.** This is a controlled external-domain
falsification of the W030 incremental Rust XOR source-certificate precheck,
not a representative SAT competition or a proof about P versus NP.

## Frozen inputs and source provenance

- All **eight original INRIA/CADP VLSAT2 DIMACS files** previously frozen and
  independently checked in W022, retaining exact published SAT/UNSAT labels,
  compressed SHA-256, uncompressed SHA-256, variable and clause counts.
- Four source-verified, planted-SAT near-XOR decoys from the W027 generator,
  unchanged and byte-hashed, to detect invalid parity proofs or excessive
  false-positive routing.
- Two source-verified W026 matched synthetic SAT/UNSAT sanity controls with
  8,192 noise clauses, also byte-hashed. They are **not** counted in the
  external-domain primary result.

Exactly 14 cases and the full manifest are frozen in
`research/results/w032_case_manifest.json`, derived without redownloading or
relabeling any official publisher input. `scripts/w032_external_cases.py`
regenerates the manifest independently. No substitute or generated CNF may
replace a missing official external source.

## Arms and measurement

1. Plain Kissat `rel-4.0.4` at pinned commit
   `8af8e56f174b778aef3aa45af9f739b2a5f492c2`;
2. Original W027 Rust parity certificate scan and unchanged-CNF Kissat on
   `NO_CERTIFICATE`;
3. W030 incremental Rust source-prefix scan and unchanged-CNF Kissat on
   `NO_CERTIFICATE`.

Use three interleaved repeats per case and arm: **126 total timed
invocations**, of which **72 are on official external CNFs**. Keep the same
**6-second end-to-end wall cap and 2GiB address-space cap** for every arm;
this pilot cap is intentionally shorter than W027's 30s full external suite
and must not be presented as comparable absolute runtimes. Source downloads
and source-hash audits happen **outside** the timed solver pipeline. Parsing,
subprocess cost, Rust precheck, fallback Kissat, and independent model/XOR
proof validation are included in the measured pipeline.

An additional unmeasured W030 diagnostic invocation records the number of
source clauses read before proof. Original source clauses must independently
validate any reported XOR certificate. A `NO_CERTIFICATE` never claims SAT;
an external time-limited Kissat `TIMEOUT` is **censored**, not a solved result.

## Precommitted analysis and falsification rules

The **primary external outcome** is the per-arm number of completed SAT/UNSAT
solver answers versus 6-second timeouts among 24 external invocations per
arm. Also report the number of independently verified early UNSAT source
certificates and mean read fraction across eight external sources.

Only for cases jointly solved in all three repeats by **all three arms** may
we calculate relative wall times, presenting their individual ratios rather
than a selected-subset claim about all external cases. The frozen analyzer
`scripts/analyze_w032_external.py` checks this censoring rule.

**A cross-domain advantage is not supported** if no external UNSAT
certificate is found and the paired solved-case latencies are indistinguishable
from or worse than plain Kissat after all precheck overhead. A genuine
external proof found by W030 must pass independent source-clause auditing and
label checks. Missing inputs, wrong digests, incorrect labels, bad SAT models,
or invalid proofs fail CI and require a transparent corrective rerun.

This is a negative-control-heavy experiment. No trial selection, threshold
tuning, source rearrangement, or extrapolation to arbitrary NP-complete
instances is permitted after the manifest is frozen.
