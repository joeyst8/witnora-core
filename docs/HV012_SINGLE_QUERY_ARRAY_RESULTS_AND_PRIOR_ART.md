# HV-012 — Single-query BMC encoding does not remove array-safety cutoff

**Date:** 2026-11-10 America/Chicago. **Status:** frozen single-query experiment complete. **No algorithmic breakthrough; no unbounded proof.**

## Why this experiment exists

HV-011 obtained solver `unknown` at depths 32/64 when each frame's `bad` was submitted as a separate BTOR2 safety check under one Bitwuzla process with a 20-second time limit. The alternative here is standard bounded model checking: OR all frame-bad predicates into **one bad property**, which is satisfiable exactly if *any* frame violates safety. This removes per-property query iteration while retaining all original time-frame signals and reset/transition constraints.

The protocol was committed **before** testing as `docs/HV012_SINGLE_QUERY_ARRAY_BMC_PROTOCOL.md` (commit `934e3f316b5188c10a89e87189fa14ce5939fcf1`).

Input: untouched SoSy-Lab `processed_hl_arr_access_32_arr.btor2` from commit `e19d110544fe7481763894f479b223aaa95fa582`, SHA-256 `93fb87c152dc8b7fc3e709f1d56a6ab1178ac782340a1b84b86ee69f8fa40c49`. Recovered and rebuilt pinned Cerbtora 2.0.0, Bitwuzla 0.6.1 commit `9bb73b69611d85fd04c20b3bd72f6dbe9bd9dc43`, and Btor2tools parser commit `e6941e37e056084ab6e51c5c1eee6233089a330d`. Native tool rebuild in isolated scratch was necessary because temporary binaries from HV-011 expired; tools were restored from upstream source. No user's repo or corpus input was modified.

## Exact results

| Depth | Original frame bads | Aggregated bads | Bitwuzla result | Elapsed wall |
|---:|---:|---:|---|---:|
| 16 | 17 | 1 | **UNSAT** | 0.042 sec |
| 16 + SAT-positive input bad | 18 | 1 | **SAT** | 0.016 sec |
| 32 | 33 | 1 | **UNKNOWN** | 19.90 sec |
| 64 | 65 | 1 | **UNKNOWN** | 19.91 sec |

All Bitwuzla runs used `--lang btor2 --time-limit 20000 --memory-limit 2048`. The process returned exit 0 for every run; **`unknown` is not a successful proof**, and no per-frame results were extracted from it.

Depth-16 original multi-bad unrolling reproduced **exactly** HV-010's recorded SHA-256 `85fb4e83bb4dbf81776fcbc29fa1027c5f405d10e05799fc8227387f9c325689` before transformation. Depth-16 aggregated query correctly reported UNSAT. Adding a known satisfiable unconstrained `ap_start` bad produced SAT. At depths 32 and 64, this alternative still reached the same global cutoff.

Generated aggregated BTOR2 SHA-256s:
- Depth 16: `579ecf621651b8c3af4123519b76062c357bd8f8c9220e0d51bc366b40ed3d94`.
- Depth 16 + positive control: `50a635390298edf0c237dfd285a33de5bd59226fb59e444aaea57d5091e95bf8`.
- Depth 32: `6d54c3987d35bd14a1a2be64687910d3e0c9456bf2400adf9073f1ddf7b7b3d8`.
- Depth 64: `18e8d654ac1a7e7db1196d243cb3b8655bd944c4a166ec08424bd5e055ddc6e5`.

Generator: `research/hv012_aggregate_bads.py`, SHA-256 `9c78218fb777ba09ca6e6310dc283868659686d90fd1c5d259c72711240a3ffd`. Full machine-readable results: `research/results/hv012_single_query_array_bmc.json`.

## Reproduction

```bash
python research/hv010_btor2_bmc.py model.btor2 unrolled32.btor2 --depth 32
python research/hv012_aggregate_bads.py unrolled32.btor2 onebad32.btor2 --expected-bads 33
/path/to/bitwuzla --lang btor2 --time-limit 20000 --memory-limit 2048 onebad32.btor2
```

Use only the pinned original model whose SHA is above. Repeat `--depth 16 / --expected-bads 17` and `--depth 64 / --expected-bads 65`.

## Updated prior-art gate

**Not novel:** one-bad aggregation, bounded model checking, k-induction, PDR/IC3, and word-level array abstraction are long-established.

An important *current* incumbent is **Pono 2.0** ([official implementation](https://github.com/stanford-centaur/pono); [FM 2026 paper](https://doi.org/10.1007/978-3-032-26220-2_1)), which already supports array-capable IC3SA, word-level IC3 with syntax-guided abstraction. Its authors explicitly state that Pono 2.0 exposes invariants through its API but **does not yet export safety correctness proofs as witness circuits**. Separate upstream **Cerbtora** provides a word-level witness checker ([IJCAR 2026 primary paper](https://doi.org/10.1007/978-3-032-32589-1_17)). Hence the responsible *engineering* target is a reliable, checker-accepted array invariant witness; any novel research claim requires a substantial previously unstudied mechanism and controlled comparisons against Pono/AVR/Cerbtora.

## Decision

Do not spend further cycles on mere output-bad aggregation as the main solver innovation. Next priority is a **genuine sequential inductive baseline** (Pono 2.0 array-aware IC3SA or AVR, paired with an independent witness checker), on the exact development model, before untouched holdouts. Keep PR draft and distinguish checker-accepted proofs from unverified solver status.
