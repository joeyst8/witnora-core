# PR #119: Precommitted non-parity source-diversity gate

**Protocol committed before downloading or measuring these four DIMACS
sources.** This is a falsification gate for a narrow, successful parity
specialization, not permission to tune on the evaluated instances.

## Frozen official sources

Source archive prefix:
`https://archive.dimacs.rutgers.edu/pub/challenge/satisfiability/benchmarks/cnf/`.
All downloads must remain original compressed `.Z` files, decompressed
in memory through `uncompress -c`, parsed by the strict original DIMACS
parser, and SHA-256 hashed before solver execution.

| Source name | Independent construction | Precommitted expected status |
|---|---|---|
| `hole8.cnf.Z` | Pigeonhole principle, 8 holes | UNSAT |
| `dubois20.cnf.Z` | Dubois generated unsatisfiable 3-CNF | UNSAT |
| `aim-50-1_6-yes1-1.cnf.Z` | AIM 50-variable generated formula | SAT |
| `aim-50-1_6-no-1.cnf.Z` | AIM 50-variable generated formula | UNSAT |

The exact decompressed SHA values will be recorded **after** fetching the
precommitted named sources and **before** solver trials. No source name may
be removed or swapped if it is difficult, slow, missing XORs, unsupported,
or disagrees with the expected truth value. A fetch/hash failure is reported
as a source error, not omitted from summary statistics.

**Sealed holdout `par32-2-c` is forbidden** and is not on the allowlist.

## Frozen operator and decision rule

The `par32-1-c` right-ROBDD/backward-pruned sparse-left algorithm and its
source-exact helper functions remain unchanged. On a new formula:

1. Detect only complete, safe, source-exact XOR-CNF encodings. Eliminate
   source XOR-only coordinates as before; inspect the exact residual-only
   XOR rows and the original residual CNF.
2. The existing operator is applicable only if all residual-only XOR rows
   split into local width-3 equations and **1–32** wider global rows, and
   if the same deterministic natural-order separator rule produces a small
   enough boundary. Otherwise report `UNSUPPORTED_SOURCE_STRUCTURE` or a
   more specific `UNSUPPORTED_*` status; **do not hallucinate global XORs**.
3. For an applicable formula, use the frozen exact BDD/sparse join with the
   original 500,000-node, 250,000-entry, 100,000-state, and 30-second
   ceilings. Verify any full SAT assignment against all original clauses.
4. When the operator is unsupported, the portfolio may fall back to plain
   original-CNF CryptoMiniSat. **Charge** the classifier cost and all
   CryptoMiniSat setup, solve, and verification to that portfolio worker.
   Do not count a fallback win as a novel Witnora algorithmic speedup.
5. Unsupported/incomplete outcomes cannot be promoted to UNSAT. An UNSAT
   conclusion is accepted only from the established complete SAT backend.

No manual separator, bound adjustment, per-instance variable ordering,
cache size, RHS repair, or hand-patched source assignment is allowed after
the experimental input has been inspected. A classifier that rejects all
four is a valid negative outcome and counts as **0/4 operator coverage**.

## Matched benchmark protocol

- Exactly **two sequential paired runs per source**, same original
  decompressed SHA-checked clauses; deterministic source order from the
  table above.
- Primary baseline: unmodified `pycryptosat==5.17.0`, one thread, raw
  original CNF. Per-worker timeout **12 seconds**, with full source
  verification (when SAT). Network and original DIMACS parse outside the
  worker for both methods.
- Primary Witnora result: frozen structural operator applicability,
  measured in an isolated worker. Also report an optional fallback
  portfolio worker running the same CryptoMiniSat after classification,
  with full combined time charged.
- Report original source metadata, source hash, exact-safe extracted XOR
  count, application/rejection reason, all timing data, verified truth,
  resource caps, and every `UNKNOWN`/error. Do not exclude failed trials.
- Additional independent solver checks may be included but cannot replace
  the completed matched primary baseline.

## Decision rule

The existing `par32` advantage is not general-purpose until at least one
genuinely unrelated source supports exact symbolic operation and the method
shows end-to-end speed and correctness on a precommitted selection. If the
source classifier finds no relevant global parity structure, conclude the
**coverage hypothesis failed** on these source families; do not perform
post-hoc structural modifications to rescue this evaluation.

Do not open the sealed holdout or publicize a novel-math/world-changing
claim. Preserve the protocol, the code, all raw results, and the final
negative/positive research gate in the existing unmerged PR #119.
