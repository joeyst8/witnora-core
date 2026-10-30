# Compressed G5/G14 certificate trust review — 2026-10-30

This is an **internal, adversarial engineering review**, not an independent
third-party security certification or proof of Python implementation
correctness. The formal verification claim is always conditional on a *real*
Lean kernel accepting the generated proposition.

## Trusted base and claim

- Trusted: the Lean kernel and imported, compiled formal definitions, plus
  ordinary file/process integrity during verification. The Lean build prints the
  `#print axioms` output for the composition theorems; automated rejection
  of an unexpected axiom set remains future audit work.
- Untrusted: DIMACS input text; Python parsers and canonicalizers;
  component/root/offset/path discovery; G14 separator selection, branch
  enumeration, conditioning, component selection and G5 certificates;
  native checker claims, hashes, and SAT-oracle verdicts.
- Supported output: the **specific original signed CNF parsed from the
  source document is UNSAT**. It does not mean the solver solves arbitrary
  CNF or that its Python implementations have been universally refined.

## Boundary-by-boundary checks

| Boundary | What must pass in the composed Lean claim |
| --- | --- |
| ASCII DIMACS -> signed clauses | The exact parsed document equals the serialized raw signed clauses |
| Source clauses -> root paths | Every claimed source XOR path and root/offset relation is checked |
| Root substitution -> raw residual | Literal-wise rewritten clauses exactly equal the substituted Lean CNF |
| Raw residual -> canonical residual | Canonicalization equality is decided inside Lean |
| Separator branches | The finite enumeration of all Boolean assignments is exact |
| Conditioned component partitions | Every emitted branch partition passes `checkPartition` |
| Selected component | The purported UNSAT component belongs to its branch partition |
| G5 evidence | The selected component's concrete GF(2) rows and elimination DAG pass `checkG5Closed` |
| Final claim | `CompressedG14.residual_g14_implies_original_unsat` eliminates every original model |

For the direct compressed G5 route, the last three G14-specific checks
are replaced by `SourceG5.checkRawG5` on the exact rewritten residual.

## Adversarial falsification

`scripts/audit_compressed_g14_proof.py` generates a legitimate source-bound
compressed G14 UNSAT instance, then deliberately rewrites the final Lean
source at the trust boundary:

1. Erases **all source path evidence**, leaving no justification for
   the binary-XOR root substitution.
2. Replaces the **selected residual component** with an empty CNF, which
   cannot be the certified UNSAT component.

Each mutation is executed through the genuine Lean executable. The gate must
return `verified = False` and never set
`original_unsat_kernel_verified = True`. These tests supplement the
earlier native-certificate and fake-status rejection tests; they do not
exhaust the space of possible malformed artifacts.

## Performance measurements

`scripts/benchmark_compressed_g14_cost.py` measures a Glucose3 run on the
original CNF and separately the Python candidate/certificate cost and the
**full source-bound Lean gate** cost. The CI saves raw CSV, SHA-256 of
original DIMACS, counts and status. These tiny, single-run measurements
are **proof-overhead accounting, not a solver-speedup claim**.

## Remaining risk and future audit work

1. **Universal Python refinement:** per-instance Lean checks do not establish
   that every Python execution matches its Lean specification.
2. **Resource exhaustion:** native parsing, discovery and certificate
   generation can consume resources before the Lean subprocess timeout.
   Deployments need externally enforced memory, input-size, and wall-clock
   budgets and isolation.
3. **Toolchain and library trust:** this internal review does not independently
   audit the Lean kernel, imported standard library, dependencies, or runner.
4. **Adversarial coverage:** extend with mutated DIMACS headers, decimal
   lexemes, path offsets, missing G14 branches, forged partitions, altered
   G5 rows/DAGs, non-affine instances and SAT counterexamples.
5. **Scientific claims:** increase sample sizes, independent random seeds,
   hard crafted counterexamples, modern SAT baselines, repeated timings,
   memory and proof-size measurements before asserting novelty or advantage.
