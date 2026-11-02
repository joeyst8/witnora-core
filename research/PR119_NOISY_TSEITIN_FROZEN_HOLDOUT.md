# PR #119 — Frozen Noisy Tseitin Holdout (No Tuning)

Reproducible CI: https://github.com/joeyst8/witnora-core/actions/runs/41503302558
Frozen holdout code: `scripts/holdout_noisy_tseitin_source_subset.py`
Raw JSON: `research/PR119_NOISY_TSEITIN_FROZEN_HOLDOUT_RESULT.json`

## Frozen before measurement

- Sizes: 64, 96, 128 graph vertices.
- Fresh seeds: 47 and 73 (not the development seeds 11 and 29).
- Guarded non-affine noise: 1 or 4 clauses per vertex.
- 12 unsatisfiable instances, independently checked source-subset native G5 certificates.
- Additional SAT controls: even-charge parity and one deleted XOR-encoding clause, both correctly rejected by the native UNSAT claimant and solved SAT by MiniSat.
- Independent MiniSat22 and CaDiCaL195 workers each have **3 seconds** per instance; a timeout is `UNKNOWN_TIMEOUT`, not a claimed solver result.

## Results

| Size | Native G5-subset median | MiniSat UNSAT / total | CaDiCaL UNSAT / total |
| --- | ---: | ---: | ---: |
| 64 | 97.00 ms | 3/4 | 3/4 |
| 96 | 204.31 ms | 0/4 | 0/4 |
| 128 | 339.67 ms | 0/4 | 0/4 |

- Native G5 contradiction candidate with rechecked source-clause membership: **12/12**.
- MiniSat: **3 solved UNSAT / 9 timeouts**.
- CaDiCaL: **3 solved UNSAT / 9 timeouts**.
- On the 3 cases each solver completed, native extraction + native G5 certificate checking was faster: **3/3** against each.
- Across all 12, median native cost **204.31 ms**; medians over *only completed* solver cases were **1,902.29 ms** for MiniSat and **563.61 ms** for CaDiCaL. These medians are not directly comparable cohorts.

## Interpretation: promising, but prior art

The linear XOR contradiction is an established technique; Tseitin graph formulas are classical proof-complexity examples. An XOR-aware baseline, especially CryptoMiniSat, is required before any claim of novel speed or world-changing advantage.

The native times exclude per-instance Lean kernel compilation and full ASCII DIMACS source proof. The universal subset-to-source soundness theorem and one small source-subset G5 instance were kernel-checked separately. The large-holdout certificates have `lean_formal_status=NOT_LEAN_VERIFIED`, and must remain so until individually accepted.

No retuning against these 12 inputs is permitted if they are to remain a holdout. For a serious publication claim, freeze the method; run an independently generated graph distribution and a strong XOR-aware baseline, then compare **complete proof-producing workflows** including checking.
