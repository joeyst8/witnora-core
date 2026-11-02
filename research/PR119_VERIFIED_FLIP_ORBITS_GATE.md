# Verified CNF sign-flip orbits: real pruning, no solver breakthrough

## Prior-art and overlap checks

Before prototyping, we checked existing Witnora `operator_genesis.py`: its
`OrbitCapacityInstance` and checker are Hall-type resource/capacity deficits,
not literal-sign-flip automorphism verification. This experiment verifies a
different, narrower group action on original CNF clauses.

However **SAT symmetry breaking and orbit representatives are longstanding
research**, not a new mathematical discovery. Examples:

- Aloul et al., *Solving Difficult SAT Instances in the Presence of Symmetry*:
  https://web.eecs.umich.edu/~imarkov/pubs/conf/c023.pdf
- SAT 2024 proceedings, *Satsuma: Structure-Based Symmetry Breaking in SAT*:
  https://drops.dagstuhl.de/storage/00lipics/lipics-vol305-sat2024/LIPIcs.SAT.2024/LIPIcs.SAT.2024.pdf

## Soundness argument and test target

Let original CNF be `F`. For a bitmask `g`, define `T_g` by flipping the sign
of every literal whose variable bit is set in `g`. **Accept a generator only
if the transformed normalized clause set equals the original clause set.**
Then `F(a) == F(a xor g)` for every assignment `a`, since the transformation
permutes all clauses of `F`. Compositions of accepted flips are also valid:
`T_g ∘ T_h = T_(g xor h)`. If accepted generators have rank `r`, each orbit
contains exactly `2^r` assignments; one canonical representative per orbit
preserves SAT/UNSAT. The canonicalization uses a GF(2) echelon basis and
eliminates generator pivot bits from an assignment integer.

Exact source-CNF XOR detection supplies *candidates* from its homogeneous
nullspace; **it does not certify a symmetry**. Every candidate is separately
checked against all original clauses. When the candidate space is larger
than 4096 elements, discovery examines only a basis and explicitly becomes
incomplete. Rejected generators cannot affect correctness.

This full-source audit is the key distinction from earlier experiments that
assumed external affine equations without a CNF derivation.

## Benchmark

`scripts/experiment_verified_flip_orbits.py` compares exhaustive assignment
enumeration with canonical-orbit-only enumeration on the same 40 fixed
synthetic instances (10/14 variables, five seeds, four families). The timed
quotient result includes row detection, candidate construction, clause-set
automorphism audits, and orbit filtering. Native MiniSat22 is an external
correctness and timed practical benchmark (fresh solver per repeat).

Three repeats, per-case medians summed:

| Metric | Ordinary enumeration | Verified orbit quotient | MiniSat22 |
|---|---:|---:|---:|
| SAT/UNSAT answers correct | 40/40 | 40/40 | 40/40 |
| Assignments actually examined | 184,066 | **49,166** | Not comparable |
| Sum of median runtimes | 1,255.547 ms | **904.894 ms** | **2.488 ms** |

30/40 instances had a nonzero verified symmetry rank; 30/40 visited fewer
assignments, while only 22/40 ran faster end-to-end. The ten OOD random
3-SAT cases had no detected sign-flip generator; the search then did the
same work plus discovery overhead. Some UNSAT families contain deliberately
contradictory units, so exhaustive assignment enumeration is an extremely
weak baseline on those cases. **The native solver is orders of magnitude
faster and this should not be presented as a competitive SAT speedup.**

Independent tests verify source-CNF rejection of broken symmetries, full
truth preservation under every accepted generator for small formulas,
canonical representatives and orbit sizes, and 90 additional random CNFs
checked against MiniSat. Four new tests passed. These are experimental
checks, not universal Lean proofs of this Python implementation.

## Gate decision

**Preserve in draft only, not a world-changing publication.** The tested
quotient is mathematically sound and eliminates real assignment families,
but its speedup is against brute force, not existing SAT techniques. The
scientific next question is whether *source-certified* symmetry can reduce
conflicts in an already efficient CDCL implementation on genuine nontrivial
instances, with preprocessing included and better symmetry-breaking
algorithms as baselines. We should not repeat Hall capacity checks or call
standard orbit symmetry novel.

Reproduce:

```
python -c 'from scripts.experiment_verified_flip_orbits import benchmark; print(benchmark(seeds=5,repeats=3)["summary"])'
python -m unittest tests.test_verified_flip_orbits -q
```
