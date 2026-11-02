# PR #119: SATLIB nonlinear local/global bridge and exact syndrome-cost gate

**Research-only; no new algorithm, theorem, or solver-speed claim.**
This is a source-exact structural reduction of the hard 1993 DIMACS PARITY
instance. The tools are familiar mathematics (GF(2) elimination, bounded-
treewidth dynamic programming, Fourier moments, binary-matroid cut ranks).
Our particular combination is a *prototype hypothesis*, not established
originality or general-world-impact research.

## Locked source, proof boundary, and prior work

- Source: [original Rutgers DIMACS SAT archive](https://archive.dimacs.rutgers.edu/pub/challenge/satisfiability/benchmarks/cnf/),
  `par32-1-c.cnf.Z`; decompressed SHA-256
  `5e3253738e729c3fda8cde22e67b6d8bae0df6d53e9afabb6bd74d5ceb700312`.
- Original: **1,315 variables / 5,254 source clauses**; exact complete XOR
  extraction finds **1,158 independent source rows** and 4,632 encoding
  clauses; there are **622 residual clauses** (372 binary, 250 ternary)
  involving **375 variables**.
- The existing affine dimension is **157**. The source is SAT, with witnesses
  previously verified against all original clauses in the CryptoMiniSat gate.
- `par32-2-c` is the **sealed holdout**: no source download, solve, profile,
  pivot tuning, or operator measurement in this experiment. All scripts reject
  it before requesting the network.
- Width certificates here are verified by Python's exact graph-order checker.
  These are **not** yet Lean kernel-checked proofs, which remain a distinct
  formal-verification obligation.

## Result 1: Local nonlinear structure is narrow

The original 375-variable residual CNF has 747 primal graph edges and a
deterministically produced, independently checked elimination order of width
**4**. This proves `treewidth <= 4`, **not** that the optimum equals 4.
After substituting affine free coordinates, a deterministic min-fill order
on the 157 projected variables reaches width **39** and 1,778 graph edges.
This second number is another **upper bound**, not a lower bound. It reveals
potential locality loss under that coordinate system, not an intrinsic
impossibility theorem.

The 372 binary residual clauses give **no nontrivial strongly connected
components** in their stand-alone 2-SAT implication graph, and therefore no
new source-bound XOR equalities by this SCC test. This closes one obvious
low-cost simplification route.

## Result 2: Exact nonlinear model count and the random-offset comparison

With exact integer-valued bucket elimination of scope at most 5, the number
of assignments satisfying **only** the 622 residual clauses is

```
121777498726418116773075109941942676845605421049
```

or approximately `2^156.41487` out of `2^375` assignments. This is a count
of the *residual alone*, **not** the complete mixed SAT instance.

Here is a rigorously defined first-moment comparison, *not* a statement
about the fixed actual instance. Let `L` be the 157-dimensional linear
direction subspace in GF(2)^1315, and let `S` be the residual satisfying set
on 375 variables (the other 940 are unrestricted). Draw a **uniform random
translation** `t` in GF(2)^1315. Then

```
E_t |(t+L) ∩ S| = 2^157 * |SAT(residual)| / 2^375
                   ≈ 2^(-61.58513).
```

By Markov's inequality, the random-translation chance of *any* intersection
is at most this expectation. The actual RHS/coset is **not** a uniform random
translation and is known SAT. Source construction can introduce exceptional
correlations; this number is neither a hardness proof nor evidence of a
physics-like impossibility.

## Result 3: Exact 186-local / 32-global separation

Eliminating the **940 XOR-only variables first** transforms the 1,158 source
equations into **218 independent residual-variable-only parity checks**.
There are **186 width-3 rows** and **32 wider rows** (width 13–23). Their
separation is based on this sharp source-derived width distribution, not a
manual solution hint or source-specific hand-picked separator.

The first exact Fourier-moment probe computes the compatible residual-model
count for each of 32 *shortest* source-derived parity rows using a sign-
weighted width-4 factor elimination. The fraction of residual models that
satisfy an individual row ranges **0.57191761–0.75647409**; none is nearly
forced or impossible in isolation. These are exactly evaluated integer
ratios, with decimals only for compact reporting. This is **not** joint
conditional probability or proof of a good branching heuristic.

Add **all 186 local width-3 XOR factors** to the residual CNF. The combined
primal graph still has a checked elimination order of width **5** and maximum
counting factor scope **6**. The exact integer model count becomes

```
704494193
```

or `2^29.39201`. All 186 local equations are already consequences of the
source XOR encodings; no externally assumed parity rows are allowed. The
remaining **32 global equations** have independent row rank 32.

For uniformly random 32-bit choices of the *remaining* RHS, the expected
number of exact local models satisfying them would be
`704494193 / 2^32 ≈ 2^(-2.60799) ≈ 0.164`. Again, the actual RHS is fixed
and source-SAT; this expectation over hypothetical alternative RHS is not a
claim about the existing source's probability of satisfiability.

**Meaningful operator target:** count or construct an assignment satisfying
the residual+local width-5 factors **and** the remaining 32-bit global parity
syndrome. This is an exact math problem with a checkable answer; it is not
yet a fast method for producing that answer.

## Result 4: Naive exact syndrome transfer fails the cost gate

The straight transfer method would retain a partial 32-bit parity syndrome
while eliminating residual variables. We measured how many global checks
remain active across each cut:

| Elimination order | Residual+local graph width | Max active wide checks | Mean active checks | Max binary-matroid cut rank |
|---|---:|---:|---:|---:|
| Min-fill | 5 | **32** | 25.126 | **32** |
| Natural ascending | 7 | **32** | 23.123 | **31** |
| Natural descending | 5 | **32** | 23.123 | **31** |

The cut-rank value is computed exactly as
`rank(M_prefix) + rank(M_suffix) - rank(M_full)` for the 32-row wide parity
matrix. It is **invariant to invertible XOR changes of row basis**. It does
not prove an optimal order or general algorithmic lower bound. But for these
orders, explicit state tracking may approach `2^31` or `2^32` syndrome
states. **Reject naive full syndrome-transfer enumeration as not practical
at our seven-second benchmark gate.** Do not claim a solver win here.

## Reproduction and safeguards

```shell
PYTHONPATH=/tmp/witnora_cms_deps:/tmp/witnora_bench_deps:. \
  python -m unittest \
  tests.test_satlib_residual_geometry \
  tests.test_satlib_residual_fourier \
  tests.test_satlib_local_nonlinear_bridge \
  tests.test_satlib_cryptominisat_gate \
  tests.test_satlib_affine_quotient \
  tests.test_real_satlib_parity_gate \
  tests.test_verified_flip_orbits -v

PYTHONPATH=/tmp/witnora_cms_deps:/tmp/witnora_bench_deps:. \
  python scripts/experiment_satlib_residual_geometry.py

PYTHONPATH=/tmp/witnora_cms_deps:/tmp/witnora_bench_deps:. \
  python scripts/experiment_satlib_residual_fourier.py --max-rows 32

PYTHONPATH=/tmp/witnora_cms_deps:/tmp/witnora_bench_deps:. \
  python scripts/experiment_satlib_local_nonlinear_bridge.py
```

**28 passing offline tests** in the listed scope: small truth-table model
counts and Fourier ratios, verified width-order acceptance, SCC parity
implication soundness, local row extraction, local/global bridge counting,
row-XOR-invariant cut rank, strict holdout locks, and prior original-source
verification tests. The full benchmark relies on an independently downloaded
historical source with its SHA checked each time.

## Next research gate and publication decision

To progress, invent a *compressed* representation of the wide-row parity
messages (possibly factoring in the local XOR relations), or find a source-
bound algebraic invariant making most wide syndromes unreachable **without**
enumerating `2^32` states. The operator must remain exact, recover and verify
the full original CNF model, and beat **CryptoMiniSat's 3.8–4.1 s baseline**
end-to-end on development data before any independent holdout result is
examined. Test multiple families; one case is not world-changing research.

Prior technical work establishes bounded-treewidth inference and parity
reasoning, so none of the components here is claimed new: [treewidth and
exact inference review](https://onlinelibrary.wiley.com/doi/10.1111/anzs.12257),
[CNF-XOR solving](https://pmc.ncbi.nlm.nih.gov/articles/PMC7363182/),
and [complete DPLL(XOR) parity reasoning](https://arxiv.org/abs/1207.0988).
