# HV-016 — Full 20-second Pono incumbent gate

**Frozen protocol:** [HV016_HIGH_BOUND_INCUMBENT_PROTOCOL.md](HV016_HIGH_BOUND_INCUMBENT_PROTOCOL.md). **Machine-readable outcomes:** [hv016_high_bound_incumbent.json](../research/results/hv016_high_bound_incumbent.json). **Date:** 2026-11-10 America/Chicago.

The same Pono 2.0 binary and unmodified SHA-pinned HKU HLS array model were used as in HV-015. To remove HV-015's early CLI bound exhaustion, both engines were configured with `--bound 1000000`, under an independently enforced **20-second wall cutoff** and **2 GiB virtual-memory cap**.

| Engine (known prior art) | Literal result | Exit | Interpretation |
| --- | --- | ---: | --- |
| Pono IC3SA + Bitwuzla | No stdout/stderr verdict | 124 | External `timeout` terminated at 20s → **UNKNOWN** |
| Pono k-induction + Bitwuzla | No stdout/stderr verdict | 124 | External `timeout` terminated at 20s → **UNKNOWN** |

Neither produced a counterexample, unbounded proof, or witness. This does **not** establish the circuit is unsafe or safe; it establishes that these **exact established configurations did not decide it at the fixed budget**. No Witnora method or speedup was tested here.

## Next scientific decision

The circuit remains a useful *candidate for difficult but concrete safety verification*: bounded original bad-state queries were UNSAT at depths up to 16 (HV-010/012), unchecked handwritten invariants failed independent Cerbtora induction (HV-011/014), and the two public Pono controls now both fail to decide in 20s. Future comparisons must use the same task, resource budget and proof checker, and longer incumbent checks must be declared before running. Existing IC3SA and BTOR2 correctness-certificate frameworks remain prior art; no discovery is claimed.
