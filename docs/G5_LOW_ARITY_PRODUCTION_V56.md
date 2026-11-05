# G5 low-arity production repair (v56)

Draft PR #57. CI: https://github.com/joeyst8/witnora-core/actions/runs/41247347675

## The concrete completeness gap is repaired

The native exact affine extractor previously defaulted to `min_arity=2`, silently omitting every zero- or one-variable equation. In this research branch `extract_affine_residue_equations` defaults to `min_arity=0`; the existing width/positivity/encoding certificate validation remains in force.

The previously Lean-certified `[[1],[-1]]` contradiction now produces a **native-verified UNSAT certificate** automatically. An explicit `min_arity=2` call preserves the historical failure as an adversarial control. The empty clause `[[]]`, equivalent to the impossible zero-variable XOR row `0=1`, also obtains a native-verified UNSAT certificate.

Most importantly, `scripts/check_low_arity_g5_lean.py` feeds both *actual Python-produced* certificates through `verify_g5_certificate_with_lean` with `raw_clauses` supplied. Both receive `LEAN_VERIFIED` with source-normalization verification in CI. Thus this is not merely a Python UNSAT string or a manually authored Lean proof.

## Regression boundary

The same CI run executes native affine extraction/certificate tests plus the TC-063 structural-validator and direct-attack tests. All pass. This is a narrow fix at the *G5 production* stage; it does not establish full G14 production with an empty separator, Gaussian elimination completeness for all supported row systems, or a universal runtime bound.

The verified abstract `UnsatCoverComplete c (Family c r)` premise remains unproved. The next direct attack should check whether the full G14 producer can construct a complete cover from this zero-separator member and then seek the next smallest unsupported certified family member. Keep minimal counterexamples in regression tests rather than assuming the generalized result.
