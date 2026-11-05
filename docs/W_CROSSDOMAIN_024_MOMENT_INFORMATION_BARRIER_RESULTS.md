# W-CROSSDOMAIN-024: exact second-order barrier, recovered by indexed triples

## Scope and preregistration

Protocol: [`W_CROSSDOMAIN_024_MOMENT_INFORMATION_BARRIER_PROTOCOL.md`](W_CROSSDOMAIN_024_MOMENT_INFORMATION_BARRIER_PROTOCOL.md), independently committed as `7ec7cf48145b2424b9401aff85079041f0994ac1` **before** the Rust experiment.

This is **one deliberately constructed SAT/UNSAT pair**, replicated through 64 matched variable and clause relabelings; it is **not** 64 independent benchmark instances and is not evidence of a general solver speedup or a P/NP complexity separation.

## Exact construction

The five source triples are `(1,2,3)`, `(1,4,5)`, `(2,4,6)`, `(3,5,6)`, `(7,8,9)`. Each right-hand side is a GF(2) equation represented by four forbidden-assignment three-literal CNF clauses.

| Exact invariant or outcome | SAT partner | UNSAT partner |
| --- | ---: | ---: |
| Variables | 9 | 9 |
| Width-three CNF clauses | 20 | 20 |
| Literal occurrences | 60 | 60 |
| Negative-literal-count histogram by clause, counts for `0,1,2,3` | `[1,12,3,4]` | `[1,12,3,4]` |
| Positive and negative degree of every variable | Identical | Identical |
| Unsigned variable-triple multiset | Identical | Identical |
| Every signed pairwise Gram entry | Identical | Identical |
| Normalized signed-incidence `B^T B` | `I/3` | `I/3` |
| Satisfying assignments (exact over `2^9` assignments) | **32** | **0** |
| Indexed triple products reveal source RHS | Yes | Yes |
| Reconstructed GF(2) contradiction | No | **Yes** |

The UNSAT source has RHS `(0,0,0,1,0)`; the SAT source has `(0,0,0,0,1)`. The first four left-hand sides XOR to zero, since each of variables 1 through 6 appears in exactly two of them; hence an odd RHS on their cycle is inconsistent. The independent equation `(7,8,9)` may have either parity without breaking satisfiability.

## Why second-order geometry is provably blind

For each encoded width-three XOR equation, the four forbidden sign vectors have a constant product. Their first sign moments and every distinct-pair sign product sum to zero, while each diagonal signed Gram entry contributes four. Summing over clauses gives `G_uv = 0` for `u != v` and `G_uu = degree(u)`.

The normalized signed clause–variable incidence matrix has rows weighted by `1/sqrt(3 * degree(variable))`; therefore `B^T B = I/3` *exactly* for both formulas, after any variable permutation. Aggregate sign histograms also match because each partner contains four even-parity and one odd-parity source blocks.

This proves a **restricted representation impossibility**: no classifier whose input consists only of the specified first- and second-order statistics and aggregate sign histograms can distinguish these two inputs. It does *not* say that all geometric methods, all local SAT algorithms, or all polynomial-time algorithms fail.

## What the extra order adds

For a particular source triple `{i,j,k}`, compute `T_ijk = sum_clause(sign(i) * sign(j) * sign(k))` over its four clauses. This returns `-4` for an even source equation and `+4` for an odd one. The **unindexed multiset** of third moments is still identical between partners (`[-4,-4,-4,-4,+4]`); crucial information is the **association between moment and variable triple**, and the GF(2) dependency among those triples.

Simple source-clause grouping reconstructs five parity equations, and Gaussian elimination certifies the contradiction with a four-row XOR cycle on the UNSAT side. XOR recognition, Fourier parity features, and Gaussian elimination are established techniques. The result is a controlled test of Witnora's representation and should not be claimed as an original algorithmic theorem.

## Verification and reproducibility

- Rust implementation: `rust/witnora-ve/src/bin/witnora_moment_barrier.rs`.
- Independent full-scope Python source reconstruction: `tests/test_moment_barrier_rust.py` (all 64 cases), with the complete Rust-generated clauses exposed for cases `0,1,31,63`.
- Dedicated GitHub workflow: `.github/workflows/w024-moment-barrier.yml`.
- Frozen xorshift seeds and shared Fisher–Yates variable and clause relabelings are given in the protocol and encoded in both languages.
- **GitHub W024 CI: PASS** — workflow run [`42128185204`](https://github.com/joeyst8/witnora-core/actions/runs/42128185204), at commit `38e1167df08b5c61661c0f1d17bd36a7a88cdfc2`; both Rust unit tests and the independent all-64-pair Python audit passed, and the raw JSON was generated and uploaded.
- **Raw evidence:** GitHub workflow artifact [`w024-exact-moment-barrier`](https://github.com/joeyst8/witnora-core/actions/runs/42128185204/artifacts/13461947320), SHA-256 of artifact ZIP `9e8305fc65e8512801798011978d5a62652645e17573a40a80f8842b485c1627`; also checked in under `research/results/w024_moment_barrier.json` for durability.
- The archive contains 64 case summaries and four complete paired clause controls. Case 0 has an independently checked four-equation UNSAT certificate over relabeled triples `(1,2,3)`, `(1,8,9)`, `(2,7,8)`, `(3,7,9)`; their combined XOR mask is zero and combined RHS is one.

## Connection to earlier research

W022 showed a fixed Rayleigh direction in the normalized geometry; W023 found gauge-deflated signals that closely followed a simple polarity-conflict statistic. W024 now supplies a *constructive exact blind spot* for second-order geometry. A meaningful next study should test **cost-aware incremental extraction** of localized indexed parity structure in mixed CNF, compared against modern CDCL/XOR baselines with matched overhead and heldout formulas; do not assume that third-order extraction automatically improves runtime.

Established context: Laitinen, Junttila, and Niemelä, *Extending Clause Learning SAT Solvers with Complete Parity Reasoning* (2012), https://arxiv.org/abs/1207.0988; Gwynne and Kullmann, *On SAT representations of XOR constraints* (2013), https://arxiv.org/abs/1309.3060.
