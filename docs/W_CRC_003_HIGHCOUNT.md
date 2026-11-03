# W-CRC-003: high-model-count nonlinear boundary stress

Status: experimental stacked research on draft PR #122.

## Falsification question

W-CRC-002 improved internal ANF times, but Glucose3 could enumerate
the few models very cheaply. That is a weak test for an exact model
counter. W-CRC-003 removes that escape hatch:

- Select random overlapping 3-CNF with *lower clause density* (~2.4
  clauses per boundary variable) and therefore potentially many more
  satisfying assignments.
- Compare the original CRC inclusion-exclusion engine, exact CRC
  Shannon coefficient fallback, structured source-to-ANF counting,
  independent Glucose3 SAT decision, capped Glucose3 model enumeration,
  and a dedicated #SAT counter, **Ganak**.
- Repeat each family at 24, 32 and 40 boundary variables, three
  deterministic seeds per size, for 18 instances.
- Mixed XOR/nonlinear cases use a complete canonical XOR-CNF chain
  linked to the same densely overlapping nonlinear boundary clauses.
  These source formulas have 46, 62 and 78 total variables.
- Three internal variants include source conversion in measured time.
  Ganak counts include constructing and loading the original CNF
  inside the counter worker, with in-worker engine time separated from
  the extra subprocess startup/termination overhead.
- The default time limit is 2.5 seconds per internal attempt and
  Ganak process, the recursive memo-state cap is 3,000, and Glucose3
  enumeration stops after at most 1,000 models. Timeouts/budgets are
  recorded, never transformed into a zero count.
- All completed integer counts must agree, and all completed counts
  must match the independent SAT decision.

Code: `scripts/benchmark_crc_highcount.py`
and `tests/test_crc_highcount_benchmark.py`.

To reproduce:
`python -m pip install python-sat pyganak==2.8.0`
`python -m scripts.benchmark_crc_highcount`

Ganak's Python `pyganak.Counter` uses arbitrary-precision integer
model counts, not floating-point weights. **Important qualification:**
its default probabilistic component caching has an extremely small
documented collision-error probability; we cross-check completed
counts instead of treating the external result as a formal proof.
The Python binding does not expose the CLI `--prob 0` option.

Ganak source and API: https://github.com/meelgroup/ganak and
https://pypi.org/project/pyganak/ .

## Evaluation gate

A meaningful algorithmic success needs:
1. Exact agreement on completed counts with an independent counter.
2. A reproducible *end-to-end* advantage on overlapping nonlinear
   families; not merely fewer parity terms or lower memory use.
3. Comparable results under harder planted, Tseitin-like, and
   industrial instances, including more seeds and realistic time caps.
4. A proof in Lean 4 of any new exact coefficient operator and of
   its connection to source CNF; Python tests alone are not proof.
5. Distinguish SAT decision, model enumeration, and exact #SAT.

If Ganak is much faster, this is a useful **negative result**.
A compact two-mode left spectrum can coexist with an expensive
nonlinear coefficient-query problem. No P vs NP inference follows.


## First high-count results (2026-11-03)

Green GitHub Actions run: https://github.com/joeyst8/witnora-core/actions/runs/41698634046

- All **31 Python test methods passed**.
- All 18 Ganak integer model counts and SAT decisions completed.
  Ganak default probabilistic caching caveat applies.
- Glucose3 *enumeration* reached the 1,000-model cap on every
  instance; it cannot be used as a counting baseline here.
- With 3,000 internal states and 2.5s per attempt, Shannon CRC
  completed **6/18** cases (all at k=24); ANF completed **3/18**
  (the three dense-only k=24 controls).
- On each of the six completed CRC instances, integer results
  matched Ganak. No completed correctness discrepancies occurred.
- The original inclusion-exclusion CRC could not handle these
  overlapping nonlinear clause sets under its subset limit.

| Boundary size / family (3 seeds each) | CRC complete | ANF complete | Median CRC (completed) | Median Ganak engine |
| --- | ---: | ---: | ---: | ---: |
| k=24 dense nonlinear, 24 source vars | 3/3 | 3/3 | 15.0405 ms | 74.0356 ms |
| k=24 XOR + nonlinear, 46 source vars | 3/3 | 0/3 | 24.2935 ms | 420.2832 ms |
| k=32 dense nonlinear, 32 source vars | 0/3 | 0/3 | — | 378.7424 ms |
| k=32 XOR + nonlinear, 62 source vars | 0/3 | 0/3 | — | 640.3155 ms |
| k=40 dense nonlinear, 40 source vars | 0/3 | 0/3 | — | 563.5883 ms |
| k=40 XOR + nonlinear, 78 source vars | 0/3 | 0/3 | — | 930.8607 ms |

Median of the **per-instance** Ganak/CRC runtime ratios is about
4.92x on the three k=24 dense cases and 18.14x on the three k=24
mixed cases. The medians are from a single GitHub runner and only
two CRC repeat timings; not a stable population estimate. Ganak
engine times include its CNF setup and count in the worker, excluding
process startup, and may reflect parity-gadget preprocessing overhead.
This is a positive *restricted small-instance* result versus Ganak,
not evidence of universal SAT/#SAT superiority.

At k=32/40 the CRC status was INCOMPLETE_BUDGET, not UNSAT.
An expanded run with 30,000 states and a strict wall-clock limit
tests whether this boundary is a chosen budget artifact. Even if it
succeeds, serious claims require more seeds, larger instances,
native XOR-aware baselines, and a mathematical invariant that
predicts when exact coefficient queries can be generated cheaply.
