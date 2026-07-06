# TC-063 Polynomial Bound Lemma

Status: `PROOF_OBLIGATION_REMAINS`

For fixed `c` and supported affine extraction bound `r`, recognition,
certificate construction, certificate size, and checker verification are
polynomial in `|F|`.

Proof obligations:

- Separator enumeration is `O(n^c)`.
- Assignment enumeration is `2^c`.
- Total residual component processing is polynomial for fixed `c`.
- Affine solving/checking is polynomial under G5 assumptions and supported `r`.
- Certificate size bound is stated explicitly.
- Exponential dependence on `c` is disclosed.

The lemma depends on G5 affine checker assumptions and remains a proof
obligation until externally formalized.
