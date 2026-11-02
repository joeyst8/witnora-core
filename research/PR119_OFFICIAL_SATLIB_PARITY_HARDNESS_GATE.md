# Official historical PARITY restored: hard-case baseline and obstruction map

## Why this gate matters

Earlier draft experiments used synthetic 16/32-variable parity substitutes
because the exact SATLIB artifacts could not be obtained. **That gap is now
closed.** We fetched original 1993 compressed `.cnf.Z` files directly from
the official DIMACS archive (Rutgers), decompressed in memory, recorded
SHA-256 of both original download and exact decompressed bytes, and parsed
the original clause lists without dropping repeated clauses. No artificial
SATLIB replacement was used.

Primary source:

- SATLIB PARITY description, including noisy parity-learning provenance:
  https://www.cs.ubc.ca/~hoos/SATLIB/Benchmarks/SAT/DIMACS/PARITY/descr.html
- Original DIMACS directory:
  https://archive.dimacs.rutgers.edu/pub/challenge/satisfiability/benchmarks/cnf/
- `scripts/benchmark_real_satlib_parity_gate.py` records each individual
  source URL, archive SHA-256, decompressed SHA-256, source counts, structural
  fingerprint, and bounded solver status.

Example fixed exact hashes:

| Source file | Compressed SHA-256 | Decompressed SHA-256 |
|---|---|---|
| `par16-1-c.cnf.Z` | `60a6ff6ac7e9df14318cfd84c9cf292062ea69ba40dd22514505ab37f3291e00` | `33691e8d6a59db323b77240ae6319353f3adc0738c36e7a3e1e9f3efaa182d8a` |
| `par32-1-c.cnf.Z` | `5ca64d346db4edef4202565c8cbed8c4266e6906075798c411a655187ca9b5c0` | `5e3253738e729c3fda8cde22e67b6d8bae0df6d53e9afabb6bd74d5ceb700312` |
| `par32-2-c.cnf.Z` | `ab0cb33120c293b078f2632ac518724a1b9d6eb500bd9b05639c67dc3e26448c` | `bc94a298db22f71a8b03d9804267e4361c78b028073b6c60e3625d4d25cf17ef` |

## Bounded native screening

Three independently implemented native solver families were tried:
MiniSat22, Glucose3, and CaDiCaL 1.9.5 (through PySAT). One run per
solver/instance in a separate process, **3-second wall-time cap**. An
expired cap is `UNKNOWN_TIMEOUT`, not SAT/UNSAT. SAT results include an
independent check of the returned model against **source clauses**.

| Official instance | Variables | Clauses | MiniSat22 | Glucose3 | CaDiCaL195 |
|---|---:|---:|---|---|---|
| `par8-1-c` | 64 | 254 | SAT | SAT | SAT |
| `par16-1-c` | 317 | 1,264 | SAT | SAT | SAT |
| `par16-2-c` | 349 | 1,392 | SAT | SAT | SAT |
| **`par32-1-c`** | **1,315** | **5,254** | **UNKNOWN (3s)** | **UNKNOWN (3s)** | **UNKNOWN (3s)** |
| **`par32-2-c`** | **1,303** | **5,206** | **UNKNOWN (3s)** | **UNKNOWN (3s)** | **UNKNOWN (3s)** |
| `hole8` negative control | 72 | 297 | UNSAT | UNSAT | UNSAT |

The original SATLIB description classifies all PARITY items as satisfiable;
we have **not yet generated their models** within the three-second gate.
UNSAT for `hole8` was independently agreed by all three solvers, not
accompanied by a proof trace. This measures a **local bounded hardness
gap**, not a universal statement that modern solvers cannot solve them.
Follow-up time caps/repeats and more modern competition benchmarks remain
necessary before publishing performance claims.

## Recovered source-bound mathematical obstruction

The exact complete XOR encodings can be extracted from the *original*
source CNF. GF(2) elimination on those rows is consistent, leaving a high
dimensional solution space. The non-XOR clauses are then the coupled
residual conditions that distinguish noisy parity learning from XOR-SAT.

| Statistic | `par16-1-c` | `par32-1-c` | `par32-2-c` |
|---|---:|---:|---:|
| Verified exact XOR equations | 270 | **1,158** | 1,146 |
| Independent GF(2) rank | 270 | **1,158** | 1,146 |
| Remaining affine dimensions | 47 | **157** | 157 |
| Clauses in recognized XOR encodings | 1,080 | **4,632** | 4,584 |
| Residual non-XOR clauses | 184 | **622** | 622 |
| Residual variables | 124 | **375** | 375 |
| Residual variables also in XOR system | 124 | **375** | 375 |
| Mean union of affine coordinates touched per residual clause | 5.81 | **7.14** | 7.15 |
| Maximum such support | 15 | **31** | 31 |
| Residual clauses touching over 16 affine coordinates | 0 | **108** | 108 |

The projected support metric is computed by taking a basis for the
homogeneous kernel of the exact source-derived XOR equations, expressing
each original variable as an affine function of free coordinates, and
counting the union of coordinates touched by literals in each residual
clause. It is a structural diagnostic, **not** a certificate of final
SAT/UNSAT, projected clause width, treewidth, or a complexity lower bound.

The **candidate obstruction to target** is the interaction of the 622
non-XOR clauses with the 157-dimensional affine solution space. Merely
solving the linear part leaves exponentially many choices; imposing the
residual conditions cheaply is the open design question. Prior SAT
literature already studies noisy parity learning, so neither the family
nor this decomposition is claimed novel.

## Scientific next gate

Treat `par32-1-c` as development and `par32-2-c` as a **pre-registered
operator holdout** for the next experiment: its source structure and baseline
timing have been seen, but no operator is to be tuned on it. Develop a projected residual
representation and measure whether it reduces nonlinear search without
expanding constraints or relying on hidden original target bits. Benchmark
against MiniSat, Glucose and CaDiCaL under identical bounded wall times.
Reject if the full extraction + operator + verification cost does not win.

Reproduce with network access, Unix `uncompress`, and PySAT:

```
python -m scripts.benchmark_real_satlib_parity_gate --timeout 3
python -m unittest tests.test_real_satlib_parity_gate -q
```

This is preserved in the draft as **hardness target identification**, not
as a published breakthrough or Lean-certified result.
