# ASCII DIMACS source-to-XOR semantic bridge (v41)

Draft PR #42. CI: https://github.com/joeyst8/witnora-core/actions/runs/41239703459

## Proof

`DimacsXorDocument.checkXorDocument source raw normalized rhs submitted` combines:

1. `DIMACSDocument.parseDocument source`: executable restricted ASCII whole-document parsing, including header and clause count;
2. `DIMACSTokens.checkStream parsedTokens submitted`: exact zero-delimited reconstruction of submitted signed-integer clauses and rejection of zero inside literals;
3. `FiniteXor.checkPythonEncodingOutput raw normalized rhs submitted`: validated positive IDs, normalizer equivalence, and exact canonical signed output.

From a `true` result:

- `checked_xor_document_tokens` proves `parseDocument source = some (serialize submitted)`.
- `checked_xor_document_iff_original` proves for every `a : Nat → Bool`:
  `SignedSerialization.signedCNFHolds submitted a ↔ Extraction.parityVars raw a = rhs`.

The positive-unit `p cnf 1 1\n1 0\n` byte example is kernel checked, along with modified-literal, extra-clause and non-ASCII rejection examples.

Axiom audit for these theorems: `[propext, Classical.choice, Quot.sound]`. No `sorry`, user-defined axiom, unsafe declaration or native evaluation.

## Boundary and next steps

The input is an explicit raw `List Nat` of byte values, not an independently verified operating-system file read or a universal Python byte-transport theorem. The restricted DIMACS grammar is an executable parser; this composition proves soundness relative to its accepted parse result, not an external text standard's entire semantics. This is exact satisfiability equivalence for accepted XOR encoding, not G5/G14 or TC-063 UNSAT.

Next run authentic Python-generated XOR DIMACS sources as explicit byte lists through this composition, including adversarially modified documents, and continue the G14 residual-model proof.
