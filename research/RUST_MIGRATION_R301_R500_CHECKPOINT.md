# Witnora R-301–R-500 research frontier tracker

R-300 is already signed off on draft PR #122, with focused native CI
[#41958473142](https://github.com/joeyst8/witnora-core/actions/runs/41958473142).

R-301–R-500 are prospective **research and regression checkpoints**, not
200 newly migrated original Python files or a promise of a complexity-theory
breakthrough. Record a gate as verified only after its reproducible
experiment and native CI have passed.

| Batch | Focus | State |
| --- | --- | --- |
| R-301–R-320 | Exact bounded minimum inconsistent GF(2) subsystem, independent oracle, original-CNF proof | Focused CI #41959938645 green |
| R-321–R-340 | Hypergraph adversarial source metadata and proof controls | Local green; native CI pending |
| R-341–R-360 | Matched variable/constraint/source-clause/degree profiles with different GF(2) ranks and proof lengths | Local green; native CI pending |
| R-361–R-380 | Adversarial relabeling/ordering/provenance metamorphic tests | Planned |
| R-381–R-400 | Resource budgets and checker-failure controls | Planned |
| R-401–R-420 | Mixed nonlinear-CNF background challenge | Planned |
| R-421–R-440 | Held-out structural families | Planned |
| R-441–R-460 | Independent baseline and cost comparison | Planned |
| R-461–R-480 | Robustness/negative controls | Planned |
| R-481–R-500 | Final reproducibility and trust-boundary audit | Planned |

The Python reference remains the default; native Rust results and parity
proof exporters are opt-in, with independent original-CNF DRAT verification.
Do not merge the research PR to `main` based solely on this milestone ledger.
