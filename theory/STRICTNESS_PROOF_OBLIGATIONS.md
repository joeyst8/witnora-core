# Strictness Proof Obligations

The v2.8 theoremization layer separates operator wins from theorem claims.

For each hierarchy edge, empirical strictness evidence has two sides:

- the extended grammar emits a checked witness, proof, or native certificate;
- the prior grammar does not collapse the selected family under the stated
  bound profile.

The first side is often satisfied by tests and checkers. The second side is
usually still an open proof obligation. A bounded no-collapse record is not a
lower-bound theorem.

Proof obligations tracked by v2.8 include:

- `PRIOR_GRAMMAR_NON_COLLAPSE`
- `NEW_GRAMMAR_CERTIFICATION`
- `CHECKER_SOUNDNESS`
- `BOUND_PROFILE_WELL_DEFINED`
- `COST_MODEL_COMPLETE`
- `WITNESS_FAMILY_SCALING`
- `LOWER_BOUND_REQUIRED`
- `DRAT_BRIDGE_OPTIONAL`
- `NATIVE_CERTIFICATE_SOUNDNESS`

No candidate is marked proven unless an explicit proof artifact exists and the
tests verify the proof file. v2.8 marks no strictness candidate as proven.

