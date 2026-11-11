# HV-008 — BTOR2 word-level witness-admission smoke control

**Date:** 2026-11-10. **Classification:** existing-tool benchmark admission and semantic-audit control; **not a new solver, certificate format, or scientific breakthrough**.

## Research purpose

HV-007 eliminated generic overlap, output grouping, incremental SAT, bit-level certificates, liveness certificates, certified retiming and broad word-level certification from Witnora novelty claims. HV-008 opens the next, more chip-relevant investigation: independently certified word-level *sequential* safety, eventually on memory/array-rich designs with genuinely strong public baselines. Start with a small correctness control to expose semantic mistakes before scaling to harder data.

Official fixture source: `Froleyks/cerbtora`, Git commit `983a21c440f8e4f25b1e8be8bd759332fee21e88`, `examples/model.btor2` (Git blob `a8f625b2381c7031ccf554ef84c912f492c6b496`) and `examples/witness.btor2` (Git blob `2bfb7d7de64857824172c24cb99234311896d0fb`). Original project's MIT license applies. Upstream checker: https://github.com/Froleyks/cerbtora .

The tool is a 2026 author-maintained independently validating BTOR2 witness checker. Btor2-Cert (TACAS 2024, DOI `10.1007/978-3-031-57256-2_7`) is earlier related word-level certifying work with a different workflow. Neither is a Witnora invention.

## Direct check completed

- Cloned the upstream source at the pinned commit; the host has `g++` and `make` but **no CMake or Bitwuzla** available. The upstream full Cerbtora checker was **NOT BUILT OR RUN**, so **there is no independently Cerbtora-accepted proof result**.
- Implemented a strict, stand-alone, dependency-free Python **subset** interpreter for only the fixture's BTOR2 operators (`state`, `init`, `next`, `neg`, `not`, `ite`, `const`, `zero`, `eq`, `or`, `bad`, `sort`). Unsupported syntax fails closed; this is **not** a general BTOR2 parser, SMT solver, or certificate checker.
- Enumerated all (2^{1+2}=8) states, calculated all transitions, reachability from the initialized state, original property's one-step inductiveness, witness's one-step inductiveness, and the fact that the witness has the *same initial state and transition relation* and a stronger safe-state predicate.
- **Positive control**: `python3 research/hv008_btor2_fixture_enumerator.py <upstream>/examples/model.btor2 <upstream>/examples/witness.btor2` exited **0**, confirming by finite enumeration that the witness's good states form an inductive strengthening of the original safety property (for this tiny fixture).
- **Negative control**: supplying the original `model.btor2` in place of `witness.btor2` exited **1**; the original property is safe on the reachable trace but **not** inductive from arbitrary states. Its specific induction counterexample is `(transition=0,data=01) -> (transition=0,data=10)`.

| Quantity | Result |
| --- | --- |
| Original and witness state space | 8 states each |
| Reachable from reset | Exactly 2: `(0,00)`, `(0,11)` |
| Original bad states reachable | 0 |
| Original bare property inductive? | **No** |
| Strengthened published witness inductive? | **Yes** |
| Model and witness initial/next equations identical? | **Yes** |
| Strengthened witness bad predicate contains original bad predicate? | **Yes** |
| Full Cerbtora validation obtained? | **No** — build environment incomplete |

## Fixture comment discrepancy worth recording

The original fixture says its one-bit `transition` state 'flips at every step'. But the actual line is `7 neg 1 5`: BTOR2 `neg` means *arithmetic two's-complement negation*, not bitwise `not` (see CAV 2018 original BTOR2 paper, https://cs.stanford.edu/~preiner/publications/2018/NiemetzPreinerWolfBiere-CAV18.pdf and official tools reference https://github.com/hwmcc/btor2tools). For a one-bit vector `x`, `-x mod 2 = x`. Therefore state `transition` stays at its reset `0`, and the 2-bit `data` flips `00 <-> 11` at each step; there are **two reachable states**, not the four implied by the comment's intended behavior.

This is a **documentation/fixture semantics discrepancy only**. It does **not** falsify its safety claim or the published witness. The original property is safe, and the witness is inductive under the source's actual semantics. Do not elevate a comment typo into an algorithmic or mathematical discovery.

## Reproduction, scope, and next gate

- Committed reproducible script `research/hv008_btor2_fixture_enumerator.py` on the draft PR. It accepts paths to **unmodified upstream** `.btor2` fixture files. Exact blob digests above.
- Archived the positive/negative control results in `research/results/hv008_btor2_smoke.json`.
- Actual Cerbtora checker acceptance remains **PENDING**. Verify via its published CLI when CMake, Bitwuzla, and pinned dependencies are available; compare the same original model without changing constraints.
- **Do not train on tiny examples** and do not call this a performance result. Further work needs public nontrivial BTOR2 instances with arrays, a fixed development/validation/final-holdout protocol, competitor baselines including Cerbtora/Btor2-Cert, end-to-end solve+emit+check cost, and independently accepted proof evidence.
- Three frozen earlier combinational holdouts `tv80`, `spi`, `systemcaes` remain untouched.
