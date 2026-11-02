# PR #119: Source-bound 3-separator / 32-bit syndrome join

**Research draft, not a novel mathematics or speedup claim.** This operator
uses a genuine source-derived decomposition and reconstructs a model for the
full historical SATLIB PARITY source. It is nevertheless slower than a strong
existing XOR-aware solver. Meet-in-the-middle and two-phase strategies have
substantial SAT literature, including successful historical par32 solvers.

## Locked source and trust boundary

- Development source: original `par32-1-c.cnf.Z` from the [Rutgers DIMACS
  archive](https://archive.dimacs.rutgers.edu/pub/challenge/satisfiability/benchmarks/cnf/).
  Decompressed SHA-256 is
  `5e3253738e729c3fda8cde22e67b6d8bae0df6d53e9afabb6bd74d5ceb700312`.
- Original CNF: **1,315 variables; 5,254 raw clauses**. The source-exact
  XOR detector finds 1,158 independent rows. The 622 non-XOR clauses and
  their 186 width-3 source-derived XOR rows form a width-5 local system;
  32 wider residual-only XOR rows remain as global constraints.
- **Holdout `par32-2-c` was not touched by this operator**; the code accepts
  only the locked development source and rejects the holdout before network.
- No user-supplied separator, model bits, hidden truth assignment, planted
  seed, or manual XOR RHS values are used. The separator is chosen from a
  deterministic graph audit; the global parity rows follow by Gaussian row
  operations on complete original XOR encodings.
- Exact source-witness verification requires that the reconstructed assignment
  satisfy **all 5,254 original raw clauses**. A failed check raises an error.

## Mathematical construction

1. Construct the primal graph from the 622 residual clauses plus 186 local
   three-variable parity factors, not from a fabricated challenge family.
2. Examine natural-order cuts with at least 100 interior variables on each
   side. Pick the smallest left-side vertex separator, breaking ties by
   variable-count balance and cut coordinate. This is an ordinary graph
   algorithm, **not** a discovery of a previously unknown SAT theorem.
3. Select cut after variable 189: left interior **186**, right interior
   **186**, and boundary **{184, 186, 188}**. Every residual or local parity
   factor is entirely within left+boundary or right+boundary. The side
   counting widths are both **5**.
4. For each of the `2^3` boundary assignments, count left and right local
   models **exactly** via integer-valued bucket elimination. Verify the
   sum of eight count-products against the independent full local count.
5. Encode each side assignment's contribution to the **32-bit global parity
   syndrome** as a bitmask. Hash one side's valid signatures, stream the
   other's, and match their XOR to the required original RHS, accounting
   for the three assigned boundary variables. Equal signatures are safe to
   deduplicate; any one representative suffices for satisfiability.
6. Reconstruct 940 XOR-only original variables by GF(2) elimination on the
   original source equations with the 375 residual-variable values fixed.
   Independently verify the resulting 1,315-variable assignment on the raw
   DIMACS clauses.

## Exact conditional counting and feasibility

| Separator bitmask, variables (184,186,188) | Left local models | Right local models |
|---|---:|---:|
| 0 | 3,572,224 | 1 |
| 1 | 4,992 | 40,920 |
| 2 | 206,368 | 528 |
| 3 | 32 | 1,107,568 |
| 4 | 942,649 | 33 |
| 5 | 497 | 237,336 |
| 6 | 36,457 | 5,456 |
| 7 | 1 | 4,272,048 |

`sum_b (left_count[b] * right_count[b]) = 704494193` exactly, matching
the independent width-5 local count. However,
`sum_b (left_count[b] + right_count[b]) = 10427110`: the balanced variable
cut is **not balanced in local solution counts**. This invalidates a naive
claim of an approximately `sqrt(704494193)` enumeration cost.

The preregistered per-side cap is 50,000 models. Eligible boundary batches
are processed in decreasing order of their exact local count-product. The
first is bitmask 1, left 4,992 and right 40,920. All other boundary batches
are never declared UNSAT from a partial enumeration. The child process has
an isolated **30-second total worker cap**; source download is excluded for
comparison with the earlier native solver gate, while all source analysis,
counting, enumeration, reconstruction and verification are charged.

## Prototype results on the original source

The first implementation enumerated each side completely before looking
for a matching signature. It reached only 22,701/40,920 right-side models
within 30 seconds and returned **`UNKNOWN_INCOMPLETE`**, not UNSAT.
Streaming the join check during enumeration is exact and eliminates this
unnecessary delay.

Three sequential streamed runs with a complete source-model audit:

| Trial | Status | Full charged worker time | Left models | Right models before match |
|---|---|---:|---:|---:|
| 1 | `SAT_VERIFIED_ORIGINAL` | 13,461.57 ms | 4,992 | 10,217 |
| 2 | `SAT_VERIFIED_ORIGINAL` | 12,067.24 ms | 4,992 | 10,217 |
| 3 | `SAT_VERIFIED_ORIGINAL` | 11,471.84 ms | 4,992 | 10,217 |

An additional run emitted the archived full witness in 12,101.55 ms. All
completed runs selected boundary bitmask 1 and independently recovered the
same original-variable Boolean-vector SHA-256:

`515c7dabc059ff203d550e1f37b2b249dd556b4746b690cdfd56589015095bbf`.

The complete 1,315-bit model is persisted as sorted true-variable IDs in
`research/PR119_PAR32_1_MITM_VERIFIED_WITNESS.json` (603 positive variables),
alongside the exact official source digest. An **independent second verifier**
downloaded the original DIMACS file, recomputed the vector digest, and
evaluated all **5,254 clauses true**.

For trial 2 the measured phase times were:

| Stage | Time |
|---|---:|
| Source detection and separator extraction | 2,870.04 ms |
| Eight exact conditional model-count calculations | 255.23 ms |
| Left local model enumeration | 1,273.00 ms |
| Streaming right enumeration to signature match | 4,805.69 ms |
| Remaining auxiliary reconstruction/verification and overhead | about 2,864 ms |

**Performance gate fails:** the strongest measured plain original-CNF
CryptoMiniSat 5.17.0 baseline took approximately **3.78–4.05 s** on the same
source, with original-model verification. The new separator/MITM method is
about **3 times slower** overall on this one instance, despite solving it
correctly and through a distinct representation. Its result is not a claim
of beating current SAT methods or proving new complexity bounds.

## Reproduce and audit

```shell
PYTHONPATH=/tmp/witnora_cms_deps:/tmp/witnora_bench_deps:. \
  python -m unittest \
  tests.test_satlib_syndrome_mitm \
  tests.test_satlib_residual_geometry \
  tests.test_satlib_residual_fourier \
  tests.test_satlib_local_nonlinear_bridge \
  tests.test_satlib_cryptominisat_gate \
  tests.test_satlib_affine_quotient \
  tests.test_real_satlib_parity_gate \
  tests.test_verified_flip_orbits -v

PYTHONPATH=/tmp/witnora_cms_deps:/tmp/witnora_bench_deps:. \
  python scripts/experiment_satlib_syndrome_mitm.py

PYTHONPATH=/tmp/witnora_cms_deps:/tmp/witnora_bench_deps:. \
  python scripts/experiment_satlib_syndrome_mitm.py --run-solver --emit-witness
```

The exact witness source audit is also a standalone read-only check: load the
archived true-variable IDs, reconstruct a Boolean assignment for variables
1..1315, assert its SHA-256 matches the artifact, download the specified
original official DIMACS file, check its source SHA-256, and assert that each
source clause has a true literal. A Python offline regression verifies the
artifact schema, sorted/ranged true-variable list and Boolean-vector digest.

## Next gate and honest publication boundary

- **Keep** the source-verified method and its failure to beat CryptoMiniSat;
  do not tune the sealed holdout to rescue its score.
- Investigate whether partial-syndrome feasibility can be evaluated in a
  compact exact structure (rather than enumerating 10k–40k local models).
  A fast C++ rewrite alone would be an engineering gain, not a new theorem.
- Require cross-family generalization, a stronger-solver win including all
  processing time, and a clear literature novelty argument before considering
  publication. The separate Lean refinement obligations are still open.

Historical context matters: the DIMACS 32-bit parity challenge was already
solved in 1998 using equivalence-aware and two-phase preprocessing, so
correctly solving this old source alone is not new science. See the
[AAAI 2000 equivalency-reasoning paper](https://cdn.aaai.org/AAAI/2000/AAAI00-045.pdf),
the [1998 two-phase parity algorithm](https://www.sciencedirect.com/science/article/abs/pii/S0167637798000522),
and [SATLIB's original benchmark description](https://www.cs.ubc.ca/~hoos/SATLIB/Benchmarks/SAT/DIMACS/PARITY/descr.html).
