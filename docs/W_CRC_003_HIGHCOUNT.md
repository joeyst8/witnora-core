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
