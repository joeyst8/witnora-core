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


## Expanded state-budget probe: 30,000 states (2026-11-03)

Green CI run: https://github.com/joeyst8/witnora-core/actions/runs/41698947755

A second invocation used `--max-states 30000 --seconds 2.5 --repeats 1`
on the *same deterministic 18 instances*. This is a **one-timing-sample
resource-bound probe**, not a statistically independent experiment.

- Shannon CRC exactly completed **14/18** (up from 6/18 at 3,000 states).
  The four missing cases reached the state budget, not a wrong
  SAT/UNSAT conclusion.
- Structured ANF completed **12/18** (up from 3/18), with one
  TIMEOUT among its six incomplete cases.
- Ganak completed **18/18** again, and all **14 completed CRC counts
  agreed**. The independent PySAT SAT decisions also agreed.
- k=32: all three dense and all three mixed instances completed
  under 6,337–13,333 CRC states, despite all six failing the
  earlier 3,000-state limit.
- k=40: one of three random seeds completed in both the dense
  and mixed versions (29,616 CRC states); the other four exceeded
  30,000 states under the strict budget.

| Boundary k / family | CRC complete | Median CRC among completed | Median Ganak (all three) | Median per-instance Ganak/CRC among completed |
| --- | ---: | ---: | ---: | ---: |
| 24 / dense | 3/3 | 18.3302 ms | 68.2080 ms | 3.84x |
| 24 / mixed | 3/3 | 18.5461 ms | 383.2579 ms | 19.52x |
| 32 / dense | 3/3 | 113.5569 ms | 349.6224 ms | 3.08x |
| 32 / mixed | 3/3 | 105.4589 ms | 579.5104 ms | 5.49x |
| 40 / dense | 1/3 | 337.6868 ms | 514.0193 ms | 1.33x (one completed) |
| 40 / mixed | 1/3 | 299.1284 ms | 845.0338 ms | 2.82x (one completed) |

**Interpretation:** there is a real but parameter-sensitive
restricted-benchmark win over this Ganak configuration. The initial
k=32 failure was chiefly an artificially tight state cap. The
subsequent k=40 failures under 30,000 states remain and may be
removed by larger budgets *at additional computational cost*.

In the paired dense and mixed formulas, the nonlinear Shannon oracle
used exactly the same number of memoized states because both
requested Fourier coefficients share a single cofactor recursion.
This is the exact asymmetric-combination property we intended to
measure. The mixed source additionally pays for detecting and
projecting canonical XOR gadgets.

The result is not a new computational-complexity theorem.
Indeed the constant coefficient
`hat(g)(0) = #SAT(g) / 2^k`:
a polynomial-time exact coefficient oracle for *arbitrary* right CNF
would also give a polynomial-time exact #SAT counter. The search
cannot disappear universally by renaming a model count as a
coefficient. The next milestone should seek **precise structural
conditions** under which *requested* coefficients can be found
without this exponential recursion, and compare against a native
parity-aware dedicated counting baseline on the same formulas.
