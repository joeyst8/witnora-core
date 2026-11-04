# R-006: Native exact right-CNF Walsh coefficient engine

Status: **verified opt-in Rust kernel** on research branch
`research/w-crc-001-asymmetric-v1`, draft PR #122. Lean TC-063
proof work remains separate and untouched. Nothing was merged.

[Green R-006 native PyO3/Ganak workflow](https://github.com/joeyst8/witnora-core/actions/runs/41740113548)

## Mathematical operation moved into Rust

For the indicator `f` of the boundary CNF and Walsh mode `m`,
the normalized coefficient is

```text
hat_f(m) = 2^(-|boundary|) sum_x f(x) (-1)^<m,x>.
```

The Python reference `crc_boundary.py` computes it by
inclusion-exclusion on independent clause-variable components.
For a component on k variables and any subset T of its clauses,
let `Z_T` and `O_T` be the union of bits forced false and true
to violate the selected clauses. If these overlap, that
inclusion-exclusion term is impossible and contributes zero.
Otherwise, if the queried mode is not contained in the forced
variables, it also contributes zero. For compatible terms
the **integer numerator** on the common denominator `2^k` is

```text
(-1)^(|T| + popcount(m & O_T)) * 2^(k - popcount(Z_T | O_T)).
```

The formula is ordinary inclusion-exclusion and character
orthogonality, **not a newly discovered theorem**.
The Rust module `rust/witnora-ve/src/right_walsh.rs`
computes all requested modes in one bounded batch, factors by
disjoint clause-variable components, multiplies their numerators,
and returns arbitrary-precision signed integer numerators and
positive power-of-two denominators. No floating point is used.

Python's strict adapter `witnora_core/crc_rust_walsh.py` converts
these to exact `fractions.Fraction` values.
The source or direct boundary counter can explicitly opt in to
`coefficient_backend="rust_inclusion_exclusion"`.
The default `"python"` is unchanged.

## Resource and trust limits

- The original `max_inclusion_subsets` cap still bounds the sum
  of all `2^(clause count)` component expansions.
- An additional `max_rust_coefficient_operations` cap bounds
  subsets multiplied by queried Walsh modes (default 2,000,000).
- Too-large components or mode workloads **return incomplete**
  without guessed coefficients.
- This backend handles **inclusion-exclusion only**. When
  explicitly selected it does not silently switch to the
  Python Shannon, orbit, defect, or conflict coefficient backends
  if its resource budget refuses. This means the Rust option can
  legitimately be less complete on some sources.
- Signed clause validation, empty-clause contradictions,
  empty CNF, duplicate boundary IDs, invalid mode masks
  and 256-variable bit positions all have explicit controls.
- The implementation is not a Lean-certified rewrite or a
  proof of complexity-theoretic performance bounds.

## Independent differential verification

[Workflow #41740113548](https://github.com/joeyst8/witnora-core/actions/runs/41740113548)
passed:

1. **17 Rust tests** including exhaustive small-source coefficient
   comparisons against direct Walsh summation for random CNFs.
2. **Five new Python integration tests**, including 210 seeded
   small-CNF entire-Walsh-spectrum comparisons against the
   Python inclusion-exclusion component oracle **and direct
   truth-table Fourier calculation**, 120 seeded full affine
   left + boundary CNF right model-count comparisons to both
   Python and exhaustive `brute_count`, wide n=60 separated
   components and n=256 signed-mask tests. Budget and
   invalid-source negative controls passed.
   A further end-to-end test combined all three native opt-in
   stages in the same `count_signed_cnf_crc` source request:
   `rust_adaptive` preprocessing, `rust` k-XOR extraction,
   and `rust_inclusion_exclusion` coefficients. Across **9
   source variants** with n=12/24/60 and q=0/1/3 parity blocks,
   the combined native path matched the independently coded
   all-Python source path and the analytic count exactly.
   [Follow-up green CI #41740643432](https://github.com/joeyst8/witnora-core/actions/runs/41740643432)
   verifies the whole pipeline, not merely isolated operations.
3. **16/16 independent Ganak checks**, with separate exact
   analytical model counts, on source CNFs built from independent
   three-variable OR blocks plus 0 to 3 explicit four-clause
   three-XOR gadgets. The source submitted to Ganak included
   the actual XOR clauses, not hidden affine constraints.

## Timed comparative experiment

Each group is an all-positive OR clause on three otherwise disjoint
variables: it admits 7/8 local assignments. The first `q` groups
add an even three-variable parity equation, leaving three locally
allowed assignments per such group. Thus the exact count is

```text
3^q * 7^(groups-q).
```

Both timed arms perform the full left affine projection and Fourier
expansion, right CNF normalization, component discovery, batch
coefficient queries and model assembly. They **exclude** prior
source preprocessing and source XOR extraction. Three repetitions
per arm on the same GitHub-hosted runner; milliseconds are medians.

| n | XOR groups | Python coefficient path (ms) | Rust coefficient path (ms) | Rust/Python |
|---:|---:|---:|---:|---:|
| 12 | 0 | 0.0661 | 0.0543 | 0.821 |
| 12 | 1 | 0.1240 | 0.0497 | 0.401 |
| 12 | 2 | 0.1186 | 0.0689 | 0.581 |
| 12 | 3 | 0.1969 | 0.0998 | 0.507 |
| 24 | 0 | 0.0829 | 0.0435 | 0.525 |
| 24 | 1 | 0.1386 | 0.0559 | 0.403 |
| 24 | 2 | 0.1885 | 0.0835 | 0.443 |
| 24 | 3 | 0.3164 | 0.1474 | 0.466 |
| 48 | 0 | 0.1755 | 0.0808 | 0.460 |
| 48 | 1 | 0.3394 | 0.0874 | 0.258 |
| 48 | 2 | 0.3839 | 0.1228 | 0.320 |
| 48 | 3 | 0.5895 | 0.1749 | 0.297 |
| 60 | 0 | 0.2797 | 0.1004 | 0.359 |
| 60 | 1 | 0.3295 | 0.1005 | 0.305 |
| 60 | 2 | 0.4279 | 0.1253 | 0.293 |
| 60 | 3 | 0.7021 | 0.2218 | 0.316 |

The n=60, q=3 case's exact count was
**6,281,023,877,654,589** and all three validators agreed.
The whole affine-plus-coefficient run improved about **3.17×**
on this structured family. The n=60 q=0 case improved ~2.79×.
These very short per-case durations are noisy on shared runners;
larger held-out workloads and memory measurements are needed
before stable rankings or general solver comparisons.

## Migration state and next bottleneck

Four distinct computational areas have now been ported:

1. Exact bounded indexed variable elimination (R-001/R-002).
2. Exact source-preserving preprocessing and adaptive admission
   (R-003/R-004).
3. Exact k=1..3 XOR source extraction (R-005).
4. Right CNF Walsh coefficient batch inclusion-exclusion (R-006).

Python retains affine projection, left sparse Fourier expansion,
source/solver orchestration, alternate right coefficient oracles,
test harness, and independent reference. Lean remains the formal
certificate checking line of work. The next useful bounded task
is to port **GF(2) affine projection and left sparse Fourier**,
then benchmark a single fused native source-to-count call
against composition of multiple PyO3 crossings.

The finite reviewed research GitHub Actions queue does not
invent its own next task or send messages to a closed chat.
