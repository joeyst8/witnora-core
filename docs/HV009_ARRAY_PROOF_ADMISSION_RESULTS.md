# HV-009 — Real-array BTOR2 certification admission results

Date: **2026-11-10**. Protocol precommitted at **7e0a21a7a640e22fc41bbd200d8d3282dda2a815**, before either selected circuit was run. Classification: known-tool development admission, **no Witnora breakthrough, speedup, or original proof technique**.

## Toolchain admission completed

The full Cerbtora 2.0.0 + Bitwuzla 0.6.1 checker is now **built and running**, so the build blocker recorded in HV-008 is resolved.

- Upstream Cerbtora commit: 983a21c440f8e4f25b1e8be8bd759332fee21e88
- Upstream BTOR2 parser commit: e6941e37e056084ab6e51c5c1eee6233089a330d
- Bitwuzla commit: 9bb73b69611d85fd04c20b3bd72f6dbe9bd9dc43; bundled CaDiCaL 1.7.4
- Isolated build tooling: CMake 3.31.6, Meson 1.8.2, Ninja 1.11.1.4, GCC 14.2.0.
- Configure options: TOOLS=ON, STATIC=OFF, Release, BITWUZLA_GIT_TAG pinned to exact SHA above.

**Positive control:** Source Cerbtora's published model plus its stronger published witness; official checker exit 0, all five obligations (reset, transition, property, base, step) UNSAT, prints "Certificate check passed" and "valid witness." Checker t_total about 0.0465s.

**Negative control:** Published model reused as its own witness; official checker exit 1, induction step SAT, prints "Certificate check failed." Checker t_total about 0.0651s.

Both controls are existing published results replicated using their independently executing public checker, not a Witnora discovery. Bitwuzla UNSAT reports were not separately checked by a formal SMT proof-log checker.

## The two predeclared real array tasks

Corpus: SoSy-Lab word-level HWMC benchmarks https://gitlab.com/sosy-lab/research/data/word-level-hwmc-benchmarks/, commit e19d110544fe7481763894f479b223aaa95fa582, array/btor2/hku-array subgroup. Both 400+ line HLS-derived circuits have array sorts and memory reads and writes; the supplied YAML metadata says expected_verdict=true.

| Predeclared task | SHA256 | Original-as-witness |
| --- | --- | --- |
| processed_hl_arr_access_32_arr.btor2 | 93fb87c152dc8b7fc3e709f1d56a6ab1178ac782340a1b84b86ee69f8fa40c49 | REJECTED (exit 1); step SAT (property 793) |
| processed_hl_arr_access_128_arr.btor2 | e1576463aa86a252d947d110f2daf6b54417c2cb3a7c4dfb871fe9ac5b33861b | REJECTED (exit 1); step SAT (property 779) |

Procedure fixed beforehand: one run per case, original model supplied as BOTH model and deliberately weak putative witness, TIME=20 seconds and SPACE=2048 MB per SAT obligation. The checker reports that reset, transition, property and base obligations pass, and the one-step induction step fails on both. Reported checker totals were ~0.0388s (32) and ~0.0417s (128); these are **fast rejection times**, not timings for actually proving safety. Process end-to-end wall estimates were ~0.115s and ~0.092s on an unisolated shared host.

## Correct interpretation

The original safety property being true on **reachable states** does not imply that the property is **1-inductive over arbitrary states**. For each file, the SAT induction-step counterexample may begin in an unreachable state. Thus the checker rejected **our inadequate witness**, not the circuit's expected-safe label. **No independently accepted complete safety certificate exists yet from our HV-009 experiment for either real-array circuit.**

These results make the practical certification gap concrete: a useful system must produce stronger **inductive invariants or witness circuits** for real memory-rich stateful designs, then have them accepted by an independent checker. This is already an established research field (Btor2-Cert TACAS 2024; Certifaiger/Cerbtora IJCAR 2026); the opportunity is to demonstrate a *specific new verified end-to-end advantage* on unseen cases, not invent certificates from scratch.

## Next admission gate

1. Locate/reproduce an established certificate-producing BTOR2 k-induction or PDR engine, and pin the tool and witnesses. No model rewriting or silently weaker constraints.
2. Obtain a true independently accepted witness for at least one unmodified real-array case. Keep solver UNKNOWN, witness rejection, and actual counterexample strictly distinct.
3. Predeclare a separate, disjoint memory-rich holdout cohort before algorithm tuning; measure end-to-end solve + emit + check and certificate size against public competitors.
4. Re-audit all proposed mathematical or algorithmic claims against 2026 original papers before calling them novel.
5. Preserve the prior three unrun combinational holdouts (tv80, spi, systemcaes).

**Status: full real checker running; actual array-model certificate generation remains unsolved in our experiment.** See the raw recorded outcomes in research/results/hv009_word_level_array_admission.json.
