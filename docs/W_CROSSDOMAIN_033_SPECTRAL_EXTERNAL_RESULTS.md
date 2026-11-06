# W033 — Exact Walsh spectral proof on published VLSAT2 (negative external result)

## Provenance and scope

- Mathematically specified sound certificate: `docs/W_CROSSDOMAIN_033_SPECTRAL_CERTIFICATE_PROTOCOL.md`.
- GitHub Actions run: [42160801103](https://github.com/joeyst8/witnora-core/actions/runs/42160801103), **passed**.
- Source code committed before experiment: `2fa10bd12f9565555c0e73a04307f2654a940216`.
- Exact original publisher CNFs: eight frozen INRIA VLSAT2 inputs with independent parsing and both SHA256 hashes checked against W022/W032.
- Formula feature: zero-to-three-wide clauses only; skipping wider clauses is sound because a certified UNSAT **subformula** proves the entire original UNSAT.
- Evidence archive: `research/results/w033_walsh_external_raw.json.gz`; compressed SHA256 `9acfcb39adef7123f75a58c72dfb0be32eadfa24268bdbcb9ab9fe2d597e266d`; decompressed SHA256 `975df576c7657fb5eba653e76cb2ce3781d0bd10d2f92a621d43b7361c0cda90`.
- Algorithm wall time below covers the **Python spectral computation only**, not download, parsing, solver invocation, or end-to-end SAT solving; do not compare with W032 solver times as a speedup metric.

## Results

| Original published formula | Publisher label | Clauses retained of original | Exact L1 lower bound | Spectral Python time | UNSAT certificate |
| --- | --- | ---: | ---: | ---: | --- |
| `vlsat2_544_8738` | UNSAT | 8,707 / 8,738 | -34,804 / 8 | 17.6 ms | No |
| `vlsat2_600_11440` | UNSAT | 11,403 / 11,440 | -45,588 / 8 | 23.1 ms | No |
| `vlsat2_684_9417` | UNSAT | 9,363 / 9,417 | -37,428 / 8 | 19.0 ms | No |
| `vlsat2_684_13953` | UNSAT | 13,899 / 13,953 | -55,572 / 8 | 27.7 ms | No |
| `vlsat2_708_10259` | UNSAT | 10,203 / 10,259 | -40,788 / 8 | 23.8 ms | No |
| `vlsat2_736_11022` | UNSAT | 10,979 / 11,022 | -43,892 / 8 | 22.0 ms | No |
| `vlsat2_1000_22250` | SAT | 22,203 / 22,250 | -88,788 / 8 | 45.1 ms | No |
| `vlsat2_3456_192912` | SAT | 192,771 / 192,912 | -771,060 / 8 | 430.9 ms | No |

**Bottom line: 0 / 8 external formulas received a spectral UNSAT certificate.** The exact bound was negative by a wide margin for every formula. No false UNSAT certificate was observed.

## Controls and interpretation

- Eight local unit tests passed, including exhaustive brute-force verification over 1,000 deterministic random small formulas.
- The spectral rule can prove an UNSAT implication chain without XOR cubes, and a frozen 5-variable/35-clause random 3-CNF with no complete eight-pattern triple cube. These illustrate coverage beyond **W030's particular complete-triple XOR extractor**, not mathematical novelty or solver speed.
- Adding unrelated clauses can destroy the useful global L1 lower bound while the whole formula remains UNSAT. This was explicitly reproduced in a negative control.
- Thus the immediate obstruction is **global coefficient accumulation**: the full formula has many independent or weakly related violations, driving the L1 sum up. The exact global bound is too loose to help on this corpus, even though the proof rule is sound.

## Next research hypothesis (unverified)

Search for **small source-derived clause subsets** with stronger Fourier cancellation, or optimize nonnegative weights assigned to source clauses. If `E_w(s)=Σ_C w_C I_C(s)` has a strictly positive certified lower bound for nonnegative rational `w_C`, the original formula is still UNSAT. Finding those weights efficiently is a separate question, and any floating-point optimization output would require exact rational certificate verification before use.

This is a hypothesis for W034, not a W033 success. Before performance claims, compare against standard unit propagation, XOR extraction, and SAT preprocessing; account for all feature, optimization and proof verification costs. No inference about P versus NP is justified.
