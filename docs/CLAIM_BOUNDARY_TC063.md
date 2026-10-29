# TC-063 Claim Boundary

Allowed wording:

- `TC-063` is hardened to `RESTRICTED_THEOREM_WITH_PROOF_OBLIGATIONS`.
- TC-063 is restricted to `SAF(c,r)`.
- Polynomiality is only for fixed separator bound `c`.
- G5 affine checker soundness is an explicit dependency.
- Native separator-affine certificates are Witnora-native, not external proofs.
- Scaling tests support implementation only.

Forbidden wording:

- `THEOREM_PROVEN_UNQUALIFIED`.
- P vs NP progress.
- Polynomial-time SAT for arbitrary formulas.
- All SAT or hierarchy completeness.
- DRAT/LRAT/FRAT proof unless externally exported and checked.
- HARD or UNKNOWN accepted statuses.

Reason:

TC-063 still has proof obligations and checker-soundness dependencies. v2.23
hardens the theorem shape and review surface without overstating the result.

v2.24 preserves this boundary in the external review package. It does not claim
P vs NP progress, all-SAT coverage, hierarchy completeness, an unqualified
theorem-proven status, or DRAT/LRAT/FRAT proof status. It asks reviewers to
attack the restricted `SAF(c,r)` theorem, its G5 dependency, and its native
certificate assumptions directly.

v2.25 keeps the same TC-063 boundary in the public preprint: TC-063 is a
restricted theorem with proof obligations over `SAF(c,r)`, not a fully proven
unqualified theorem, not all-SAT coverage, and not P-vs-NP progress.

v2.26 keeps the boundary unchanged while finalizing the public submission
packet. Bibliography hardening and release checklists do not upgrade TC-063:
the status remains `RESTRICTED_THEOREM_WITH_PROOF_OBLIGATIONS`, polynomiality
remains only for fixed `c`, and native certificates remain native-only unless
externally exported and checked.

## Optional runtime G5 Lean gate (research branch)

For a G5 affine residue UNSAT certificate and its original DIMACS CNF:

```bash
python -m witnora_core.operator_genesis check-affine-residue-cert \
  --cnf original.cnf --certificate certificate.json --lean
```

This mode requires a working `lake`/Lean toolchain and the built `formal/`
project. It reports distinct `native_check` and `lean_check` objects and
returns a nonzero process status unless the Lean checker accepts a concrete
`SparseBridge.checkG5Closed = true` proof obligation. A missing toolchain,
timeout, tampered certificate or rejected obligation is **not Lean verified**.
The optional `--lean-timeout` and `--max-arity` parameters control the check.

Without `--lean`, the existing command performs the historical native
certificate check only. The certificate JSON's `lean_formal_status` remains
`NOT_LEAN_VERIFIED`; the runtime result is a separate, invocation-bound
attestation and is not a permanently authenticated certificate signature.

This closes a concrete per-certificate runtime verification path for supported
G5 UNSAT claims. It does **not** prove the universal correctness of arbitrary
Python execution, provide a formal Python-to-Lean compiler refinement, establish
TC-063 composition, or prove any P-versus-NP claim.

## G5/G14 formal composition milestone

`Witnora.G5G14Composition.original_unsat_of_checked_g5_branch_cover`
combines the G14 abstract separator coverage principle with the closed G5
certificate checker. The conclusion is original-CNF UNSAT **conditional on**
these still-unproved implementation contracts:

1. Original-CNF model lifting into the separator/component decomposition.
2. Selected component-model interpretation into the residual CNF.
3. Existence of an accepted G5 certificate for a selected component on
   **every** separator branch.

The theorem requires no exponential original-CNF UNSAT enumeration and
does not trust a Python UNSAT verdict. The three premises are substantial:
this composition theorem alone is not an end-to-end proof of Python G14
branch production, TC-063, or its stated runtime bounds.

## Lean CNF-conditioning theorem

`Witnora.Conditioning.conditionCNF_correct` proves, for any CNF,
partial separator assignment and total assignment extending it, that the
executable Lean conditioning function preserves CNF satisfaction exactly.
Satisfied clauses are removed; false assigned literals are removed; empty
residual clauses are retained. The proof is universal in the CNF size and
uses no exhaustive UNSAT enumeration.

This discharges the **Lean-specification conditioning semantics** part of
the G14 decomposition bridge. It does not by itself prove that Python's
`_reduce_clause` and `_condition_by_separator` are extensionally equal to
the Lean functions, that the Python component partition is complete for
every input, or that every G14 branch carries a valid Lean-checked G5
certificate. TC-063 remains conditional on those implementation refinements.

## Lean residual-component partition theorem

`Witnora.ComponentPartition.checkPartition_sound` proves that a checked
permutation (multiset equality) of the conditioned CNF's clauses into
residual components preserves satisfaction. The executable check rejects
missing, extra, and duplicated clauses, while allowing component order to
differ. `conditioned_partition_correct` composes this with the Lean CNF
conditioning theorem for any assignment extending the separator.

This proves a universal specification-level partition bridge. The exact
refinement from Python's component discovery, clause simplification,
serialized signed-literal encoding, and assignment iteration into this Lean
checker is **not yet proved**. Nor does this theorem ensure that Python
generates accepted G5 certificates on every required separator branch.

## Concrete Python G14-to-Lean partition integration

The G14 fixture emitter now serializes Python's actual separator assignments
and residual component CNFs into closed Lean propositions checking
`ComponentPartition.checkPartition (Conditioning.conditionCNF ...)`.
CI kernel-checks these generated positive checks and missing-partition
negative controls, alongside the prior finite-oracle branch checks.
The generator is deterministic and does not import arbitrary certificate text
as Lean commands.

This establishes checked correspondence for emitted fixtures only. A
universal proof that Python's reduction, component graph discovery, and
serialization implement Lean's specification remains open; per-branch G5
proof acceptance still needs integration into one G14 trusted gate.

## Runtime G14 UNSAT-cover gate

Run the optional `--lean` mode of the G14 certificate checker:

```bash
python -m witnora_core.separator_affine_family_theorem check \
  --cnf original.cnf --certificate g14_certificate.json --lean
```

This mode reruns the native G14 checker, independently reconstructs every
separator assignment and conditioned component, checks the exact residual
clause partition, and requires a successful runtime G5 Lean check for the
selected UNSAT component of **every** branch. The CLI fails closed if one
branch is missing, invalid, or not accepted by Lean. A concrete two-branch
G14 UNSAT-cover certificate is checked end to end in CI.

The response uses `LEAN_G5_COVER_VERIFIED`, **not** an unrestricted
`TC063_PROVED` claim. Python's component discovery and conditioning have
not been universally refined into Lean, and there is not yet one
kernel-checked theorem applying the combined Python gate to arbitrary G14
certificate input. Neither TC-063 completeness nor arbitrary-SAT
polynomiality follows from this runtime gate.

## Strengthened runtime G14 partition gate

The G14 Lean runtime gate now emits a closed, numeric Lean proposition
for the **actual original CNF and every recomputed separator branch**.
Lean independently runs `Conditioning.conditionCNF` and verifies
`ComponentPartition.checkPartition` against the supplied component CNFs.
Only after all partition obligations pass does the gate run the existing
G5 Lean UNSAT verifier on each selected covering component. Any missing
toolchain, failed partition, malformed data, or failed G5 certificate
returns `NOT_LEAN_VERIFIED`. The success code is
`LEAN_G5_COVER_AND_PARTITIONS_VERIFIED`.

This is a stronger per-certificate trusted-checking path, not a universal
formal semantics of CPython or a proof that Python always emits accepted
certificates. The finite separator enumeration and the signed-literal
serialization implementation still require a universal refinement
argument to close complete TC-063 correctness.

## Complete separator-branch enumeration gate

`Witnora.SeparatorAssignments.enumerate_complete` proves that Lean's
deterministic Boolean-pattern generator includes every assignment of an
arbitrary supplied separator-variable list. The list order matches
Python's use of the Cartesian product of `[False, True]` over sorted
separator IDs. Generated G14 CI claims compare Python's complete output
sequence against this executable Lean generator.

The runtime G14 Lean source now also checks equality between the complete
Python branch list and `SeparatorAssignments.enumerate` before checking
conditioned partitions and every G5 contradiction. These are concrete
per-certificate proof obligations: a Python generator that omits or
reorders a branch cannot pass this Lean equality. Universal CPython
execution correctness and signed-literal serialization refinement remain
separate unproved obligations.

## Signed-literal representation theorem and runtime checks

`Witnora.SignedSerialization.encode_decode` proves that every nonzero
signed integer decodes to a Lean pair (positive variable ID, polarity)
and encodes back to the same integer. `decode_encode` proves the reverse
for all positive variable IDs and both polarities.
`signedCNFHolds_iff` establishes CNF satisfaction equivalence for the
paired representation; zero is explicitly an invalid signed literal.

Both the G5 and G14 runtime gates now emit closed Lean claims comparing
the **actual signed integer CNF data** with the paired clauses supplied
to the proof checker. G14 fixture CI also checks signed original and
component CNFs. This closes a universal mathematical representation
lemma and concrete per-certificate serialization equality checks; it
is not a universal proof of Python execution or parsing correctness.

## DIMACS parser trust-boundary hardening

The Python CNF literal constructor now rejects Boolean pseudo-integers
(`True` and `False`) as invalid signed literals. A deterministic
adversarial regression suite checks 160 randomized raw formulas over
all their small Boolean assignments, comparing direct raw-clause
satisfaction with Python's canonicalization and DIMACS export/reparse.
It also checks malformed headers, missing terminators, variable bounds,
and preservation of contradictory empty clauses.

These are tests and input-validation hardening, **not** a Lean proof of
Python DIMACS parsing or canonicalization for every input. Formalizing
tautology elimination, duplicate removal, and raw-text parsing remains
a separate source-to-Lean refinement obligation.

## CNF canonicalization specification and concrete Python checks

`Witnora.CNFCanonical.normalize_correct` proves in Lean that removing
repeated literals, removing clauses with complementary literal pairs, and
removing repeated clauses preserves CNF satisfaction for every assignment.
This is a universal theorem over Lean's abstract paired-literal CNFs; the
canonical ordering used in Python is not part of the theorem.

`scripts/emit_lean_cnf_canonical.py` emits closed Lean examples from actual
`CNFFormula.from_raw_clauses` output on adversarial and seeded randomized
valid signed-integer input. The CI checker compares each Python output to
Lean's executable normalization, allowing clause and literal reordering but
requiring matching literal and clause sets. These finite examples guard the
boundary, but they are **not** a universal CPython source-refinement proof.

The Python constructor now validates every literal even if an earlier pair
makes the clause tautological, and regression tests reject invalid trailing
values. Remaining work includes a universal ordering/serialization refinement
for Python, an independently justified parser semantics, and the complete
G5/G14-to-TC-063 composition theorem.

## Deterministic CNF order: executable Lean refinement target

`Witnora.CNFSorted.canonicalize` now models Python's signed-integer
ascending literal sort, lexicographic clause sort, tautology removal,
and duplicate elimination using an executable insertion-sort model.
The universal `canonicalize_correct` Lean theorem establishes that this
ordered normalization preserves satisfaction for every Lean CNF and total
assignment. Its helper theorem establishes that sorting preserves list
membership independently of the comparator.

The Python-produced fixtures additionally check **exact equality of ordered
clauses**, not merely equal literal/clause sets, against this Lean
canonicalizer on 43 deterministic adversarial and randomized formulas.
Those closed concrete checks do not prove that every CPython call to
`sorted`, `set`, or the constructor refines the Lean model. In particular,
the arbitrary-input Python interpreter semantics and a universal ordering
correspondence are still open; neither the P=NP question nor complete TC-063
has been resolved.

## Sorting multiset preservation

The universal Lean theorems `Witnora.CNFSorted.insertBy_perm` and
`sortBy_perm` prove the executable insertion sorting algorithm returns a
permutation of its input for **every** element type, Boolean comparator,
and list. Their specialized corollaries `sortLiterals_perm` and
`sortClauses_perm` preserve the full multiplicity of each list element.
These are stronger than earlier membership-only results and cannot conceal
sorting-related duplication or loss of clauses or literals.

These theorems do **not** yet establish that each output list is monotonically
ordered according to a total comparator, or that arbitrary CPython execution
refines the Lean implementation. The Python output equality claims are still
finite tests; universal source-level refinement remains open.

## Universal insertion-sort orderedness

`Witnora.CNFSorted.sortBy_sorted` proves that the executable insertion
sort returns a list whose head is no greater than every later element,
recursively, provided the comparator is total and transitive.
`literalLE_total` and `literalLE_trans` discharge those conditions for
signed-integer literal ordering, so `sortLiterals_sorted` proves the
literal-order property for arbitrary Lean input clauses.

Together with the earlier permutation theorem, Lean proves both order and
multiplicity preservation for sorted literals. The corresponding universal
lexicographic *clause*-order theorem, Python runtime/source refinement,
and end-to-end TC-063 theorem are still open. None of these results imply
P=NP.

## Universal lexicographic clause-order proof

The Lean theorems `Witnora.CNFSorted.lexLE_total` and
`Witnora.CNFSorted.lexLE_trans` establish totality and transitivity of
our executable lexicographic comparator on arbitrary signed-integer lists.
The `clauseLE_total` and `clauseLE_trans` theorems lift those results to
paired signed-literal clauses, and `sortClauses_sorted` proves that
`sortClauses` produces globally ordered CNF clauses.

Together with `sortClauses_perm`, this proves both global clause order and
exact multiplicity preservation in Lean. The full `canonicalize` theorem
therefore has verified literal and clause sorting stages. The remaining
refinement problem is a general semantics bridge from actual Python
`sorted` / sets / constructor / DIMACS operations to Lean, beyond the
current 43 exact-output examples. End-to-end TC-063 remains conditional.

## Combined canonical-output ordering invariants

The Lean theorems `canonicalize_clause_ordered` and
`canonicalize_literals_ordered` now close the composition of the earlier
sorting lemmas: for **every** input paired-literal CNF, the exact executable
`canonicalize` result is globally lexicographically clause-ordered, and
each surviving clause is internally signed-integer ordered. Together with
`canonicalize_correct`, this gives a universally sound and ordered Lean
normalization target for the Python refinement proof.

It is still **not** a source-level proof that arbitrary CPython executions
return that exact output. The 43 generated examples check concrete source
outputs only. Universal implementation refinement, parser semantics, and
complete G5/G14 TC-063 composition remain unproved.

## Universal duplicate-freedom of final canonicalization

The Lean theorem `Witnora.CNFCanonical.dedup_nodup` proves that the
executable duplicate-removal function produces a duplicate-free list
for arbitrary inputs. `Witnora.CNFSorted.sortBy_nodup` transfers this
property through any permutation sort. The final results
`canonicalize_clause_nodup` and `canonicalize_literals_nodup` prove
that **every** canonicalized formula has no duplicate clauses and each
remaining clause has no duplicate literals.

These close the duplicate-freedom obligation for the Lean executable
specification. Combined with the earlier satisfaction-preservation and
ordering theorems, they provide a precise canonical-output target.
The universal CPython source-execution correspondence and complete
TC-063 certificate-theorem remain open; finite Python/Lean examples
must not be presented as a source-level proof.

## Fail-closed per-invocation Python CNF normalization gate

`witnora_core.lean_cnf_gate.verify_cnf_normalization_with_lean`
now accepts strictly validated raw signed-integer clause lists, calls the
actual Python CNF constructor (or checks a caller-supplied candidate),
and emits a fixed, closed Lean proposition asserting **exact equality**
with `Witnora.CNFSorted.canonicalize`. It returns a positive verification
status only if Lean successfully checks that proposition and binds the
attestation to hashes of both original and normalized CNF data.

All malformed literal values, unsupported shapes, oversized inputs,
missing Lean toolchains, timeouts, and Lean rejections fail closed.
The CI workflow runs unit tests including deliberately altered output,
plus a real unmocked Lean invocation for Python-normalized CNF.

This is a per-invocation checker: accepted output is sound relative to
Lean's executable model. It does **not** prove that all Python executions
are accepted, nor does it establish a universal CPython interpreter
refinement. The gate is not yet a mandatory step of the existing G5/G14
certificate production workflow; that integration remains open.

## Mandatory CNF normalization attestation in G5/G14 Lean gates

The production-facing `verify_g5_certificate_with_lean` now calls the
fail-closed Lean CNF normalization gate on the canonical signed clauses
supplied to G5 before issuing `LEAN_VERIFIED`. The successful output
includes its concrete normalization attestation; rejection blocks G5.

The G14 UNSAT-cover path likewise requires a normalization attestation for
the original CNF before checking any partition, then requires **each**
selected G5 covering component to return both G5 verification and its own
successful normalization attestation. Missing or negative attestations
block the strongest G14 status. CI includes explicit fail-closed tests.

**Scope:** These gates receive already-created `CNFFormula` objects. They
check their signed-clause canonical representation but cannot reconstruct
or prove the original raw DIMACS normalization or CPython constructor
behavior upstream. Universal Python source-refinement and unrestricted
TC-063 correctness remain unproved.

### Raw DIMACS provenance checkpoint (G5/G14 CLI)

The `--lean` certificate-checking CLI now reads the DIMACS source once through
`load_dimacs_with_raw`, retaining parsed clauses **before** duplicate deletion,
tautology elimination and sorting. Both G5 and G14 pass that raw clause list
and the independently constructed canonical formula to the fail-closed Lean
normalization gate. A disagreement blocks formal acceptance, and successful
results carry `source_normalization_verified: true`. Programmatic gate calls
without `raw_clauses` retain canonicality checking, but carry
`source_normalization_verified: false` and **do not prove source provenance**.
This is a concrete runtime correspondence check, not a universal CPython
parser/execution proof; the parser, its input file reading, and the certificate
binding to the caller-selected file remain in the trusted integration boundary.

### Source/certificate substitution resistance

G5 and G14 runtime Lean attestations now hash the exact supplied raw clause
list together with the canonical CNF and certificate payload (when the source
list is available); the successful response also exposes the canonical
`source_formula_hash`. G14 rejects an injected `lean_formal_status` in the
untrusted certificate and requires every selected G5 branch to report the
exact `LEAN_VERIFIED` status plus a verified normalization check. Existing
formula-hash and independently reconstructed branch checks remain mandatory.
The hashes are binding identifiers, **not** signed attestations or a proof of
correctness of arbitrary Python execution; a trusted caller still must pair
an attestation with the same input bytes and verified invocation.
