# Kernel-reducible ASCII numeric certificate parser (v34)

Draft PR #35; built on prior experimental numeric and String adapters.

## Result

`KernelAsciiNumericCertificate.lean` parses explicit `List Nat` byte values, with separators `|` (124), `,` (44), and `;` (59), and digit values 48 through 57. It rejects noncanonical decimal forms, malformed structure, and bad byte values. The parsed certificate passes through the existing numeric range and optimality checker.

Unlike the earlier Lean `String` implementation, all concrete examples are proved using ordinary `decide` on structurally recursive list operations. CI passed and the axiom reports showed:

- `checked_ascii_certificate_sound`: `[propext, Classical.choice, Quot.sound]`
- `triangle_bytes_pass`: `[propext]`
- `triangle_bytes_optimal`: `[propext, Classical.choice, Quot.sound]`

There is **no `Lean.ofReduceBool` dependence** in these named theorems. Eight cases were checked: one valid triangle and seven invalid byte/structure/semantic variants. The tests are finite examples, not a proof of completeness of rejection for all malformed data.

## Trust boundary

This establishes soundness of certificates represented by an explicit byte-value list. It does **not** prove that a Python-produced file's raw bytes were faithfully transported into that Lean list. The Python serializer, file handling, and external byte-to-Lean literal conversion still need a deterministic cross-check or verified correspondence. Existing G5/G14/TC-063 obligations remain open.

Next: implement a canonical Python emitter that produces the byte list for a concrete certificate, compare its bytes against a frozen reference, and kernel-check the produced Lean input without importing the previous String parser's native-evaluation assumptions.
