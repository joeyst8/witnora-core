# TC-063 Assignment Exhaustiveness Lemma

Status: `FORMALIZED_PROOF_SKETCH`

Every total satisfying assignment of `F` restricts to exactly one
`alpha in {0,1}^S`, and every `alpha` is considered by the algorithm.

Proof obligations:

- Enumerate all `2^|S|` assignments.
- Omit no assignment.
- Duplicate no assignment.
- Use deterministic assignment encoding.

The exponential dependence on `|S|` is explicit and polynomiality is only for
fixed `c`.
