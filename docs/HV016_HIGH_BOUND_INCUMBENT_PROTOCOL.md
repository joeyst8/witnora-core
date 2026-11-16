# HV-016 — Predeclared high-bound published-solver runtime gate

**Date:** 2026-11-10 America/Chicago. **Frozen before either HV-016 solver invocation.**

## Why this follow-up is admissible

HV-015 built first-party Pono 2.0 successfully, but IC3SA returned UNKNOWN in under three seconds with the CLI's **default bound of 10**, and k-induction returned UNKNOWN under `--bound 16`. Inspection of Pono 2.0 `pono.cpp` confirms it uses `prover->check_until(pono_options.bound_ + has_monitor)`; the 20-second timeout was therefore not an effective full-runtime test.

## Fixed experiment

Use exactly the unchanged HKU `processed_hl_arr_access_32_arr.btor2` SHA-256 `93fb87c152dc8b7fc3e709f1d56a6ab1178ac782340a1b84b86ee69f8fa40c49`. Same locally built **Pono 2.0** tag `v2.0.0` commit `c81aa363f4c1b1d4f05669478d9a94c16a0d4b44`; smt-switch 1.1.3, Bitwuzla commit `122f27f9518269cd9c1ebf0efced37dfd7f845e6`, cvc5 1.3.3.

Run sequentially, once per engine, with the same `timeout --signal=TERM --kill-after=2s 20s` and `ulimit -v 2097152` **2 GiB virtual-memory** cap:

1. `./build/pono --engine ic3sa --bound 1000000 --smt-solver bzla <pinned BTOR2 path>`.
2. `./build/pono --engine ind --bound 1000000 --smt-solver bzla <pinned BTOR2 path>`.

Record literal stdout/stderr, process exit, elapsed cutoff status, and any resource failure. Bound one million is a practical nonbinding ceiling within 20s, not an unbounded proof guarantee. Do not modify flags after looking at the output. Do not run alternate engines or edit the model. A native `unsat` output is an **uncertified solver claim** until Cerbtora independently checks an accepted correctness witness; `sat` requires an independently checked trace. A timeout is UNKNOWN, never UNSAFE or SAFE.

## Novelty gate

This is measurement of a *published incumbent*, not novel Witnora science. IC3SA, k-induction, BTOR2 invariant generation, and witness validation are known. The experiment resolves a benchmark-design confound before attempting Witnora algorithm development.
