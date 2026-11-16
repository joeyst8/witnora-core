# HV-015 — Pono 2.0 incumbent baseline on a published HLS array circuit

**Date:** 2026-11-10 America/Chicago. **Predeclared protocol:** [HV015_PONO_2_BASELINE_PROTOCOL.md](HV015_PONO_2_BASELINE_PROTOCOL.md). **Raw structured result:** [hv015_pono2_array_baseline.json](../research/results/hv015_pono2_array_baseline.json).

## Fixed target and provenance

- Unmodified SoSy-Lab/HKU `processed_hl_arr_access_32_arr.btor2`, SHA-256 `93fb87c152dc8b7fc3e709f1d56a6ab1178ac782340a1b84b86ee69f8fa40c49`.
- 26 BTOR2 state nodes, 10 input nodes, one array sort, one bad/property output `b0`.
- Pono 2.0 tag `v2.0.0` commit `c81aa363f4c1b1d4f05669478d9a94c16a0d4b44`; CLI `--version` printed `c81aa36-dirty` because we modified only isolated build-script concurrency (`contrib/setup-smt-switch.sh`), not the model-checking source.
- Public dependencies: smt-switch v1.1.3; Bitwuzla pinned `122f27f9518269cd9c1ebf0efced37dfd7f845e6` (0.8.2-dev); cvc5 1.3.3; btor2tools pinned `fb69ee3b95e8baa5f0a9a6b0b19ee8beaad52932`. Local-only GNU M4 1.4.19, Bison 3.8.2 and Flex 2.6.4 were required to build from source. The executable and dependencies built successfully.
- Resource enforcement: `timeout --signal=TERM --kill-after=2s 20s` plus `bash -c 'ulimit -v 2097152; exec ...'` (2 GiB virtual-memory cap). No benchmark edits.

## Predeclared runs

| Established engine | CLI engine options | Literal stdout | Exit | Classification |
| --- | --- | --- | ---: | --- |
| Pono 2.0 IC3SA | `--engine ic3sa --smt-solver bzla` | `unknown\nb0\n` | 255 | UNKNOWN, under ~3s; not timed out |
| Pono 2.0 k-induction | `--engine ind --bound 16 --smt-solver bzla` | `unknown\nb0\n` | 255 | UNKNOWN, under ~2s; not timed out |

These **do not** prove the circuit safe or unsafe. Pono's `pono.cpp` invokes `prover->check_until(pono_options.bound_ + has_monitor)`; the CLI default `--bound` is 10. Thus the IC3SA run is a *shallow bounded result*, and neither run consumes the 20-second budget. It is **invalid** to conclude that IC3SA's full available 20-second search cannot solve the benchmark. A separate, frozen, high-bound follow-up is warranted.

## Novelty and certification verdict

Pono's array-aware IC3SA and k-induction are published prior art (Pono 2.0, FM 2026). Likewise, correctness witnesses and validation of BTOR2 circuits have earlier work including Btor2-Cert (TACAS 2024) and Cerbtora (IJCAR 2026). No Witnora speedup, new invariant-discovery algorithm, counterexample, or Cerbtora-accepted unbounded safety witness results from HV-015. Keep research PR draft.

Primary references: [Pono 2.0](https://doi.org/10.1007/978-3-032-26220-2_1), [Btor2-Cert](https://www.sosy-lab.org/research/pub/2024-TACAS.Btor2-Cert_A_Certifying_Hardware-Verification_Framework_Using_Software_Analyzers.pdf), [Cerbtora](https://doi.org/10.1007/978-3-032-32589-1_17).
