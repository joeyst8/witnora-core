# Operator Frontier

## v2.16 Composed Orchestration Frontier Update

`COMPOSED_OBSTRUCTION` has been promoted into
`G9_COMPOSED_OPERATOR_ORCHESTRATION_PROTOTYPE`.

The frontier rule is certificate chaining: composition is trusted only when
every step certificate verifies, every output formula hash matches the next
input formula hash, every preservation type is declared, and the witness/proof
lift trace checks. Diagnostic-only steps cannot certify SAT or UNSAT.

G9 evidence is finite empirical edge-delta evidence. It is not a strictness
theorem, not a lower-bound proof against G0-G8, not DRAT, and not composition
completeness.

## v2.15 Graph Separator Frontier Update

`GRAPH_SEPARATOR_OBSTRUCTION` has been promoted into
`G8_GRAPH_SEPARATOR_LIFT_PROTOTYPE`.

The frontier rule is now explicit: separator evidence becomes trusted only
when the checker reconstructs the primal decomposition, rejects invalid
cross-component clauses, verifies SAT witness lift under a shared separator
assignment, or verifies UNSAT cover over every separator assignment.

Grid/structured duplicate controls are marked `GRAPH_SEPARATOR_NO_NEW_DELTA`
when a prior grammar already accounts for the row.

## v2.14 Obstruction Dual Frontier Update

The frontier now has a failure-certificate layer. When G0-G6 do not produce a
certified collapse for selected controlled rows, `G7_OBSTRUCTION_DUAL_CERTIFICATE_PROTOTYPE`
records a bounded attempt trace, source feature evidence, obstruction
fingerprints, and a missing-operator recommendation.

This is not a SAT/UNSAT result and not a lower-bound claim. It is a checkable
planning artifact: the failure is made structured enough to guide the next
operator, while the claim boundary stays explicit.

## v2.8 Theoremization Update

The frontier now feeds a theoremization layer. v2.8 does not add a new
operator; it records the full G0-G6 hierarchy, bounded collapse class
definitions, empirical strictness evidence, proof obligations, and gap
analysis. Frontier rows are still planning and evidence objects, not theorem
claims or hierarchy completeness claims.

The operator frontier is a planning diagnostic. It records formulas that remain
`NO_COLLAPSE_FOUND` under a selected grammar and suggests candidate operators
that may be worth formalizing later.

It does not solve those formulas. It does not prove that a suggested operator
is necessary. It does not rerun an external SAT solver.

## Candidate Signals

- Pigeonhole rows suggest cardinality or matching-style structure.
- Pigeonhole and graph-coloring rows may also expose large deterministic
  syntactic candidate orbits. In v2.1 this is only orbit evidence; it is not a
  certified quotient transformation.
- v2.2 adds exact automorphism certificates for supported small symmetry rows.
  That still does not imply a general quotient rule or pigeonhole collapse.
- v2.3 adds a native cardinality/counting route for recognized standard
  pigeonhole encodings. It changes the pigeonhole battlefield from pure
  obstruction evidence into native certificate evidence for those exact
  encodings.
- High Horn-clause ratios suggest a Horn terminal class may be useful.
- Clause groups above the exact-XOR `max_k` cap can suggest future larger
  exact-XOR experiments, but an over-cap group is not itself a detection claim.
- Remaining no-collapse rows may motivate a bounded backdoor diagnostic, but
  only with strict caps and certificate replay.

## v2.1 Discovery Rankings

`python -m witnora_core.collapse_theory discover-operators` runs the selected
base grammar, collects bounded non-collapse rows, records obstruction
signatures, and ranks candidate next operators. The ranking is a research
planning heuristic. It is not a theorem and it does not certify that the
recommended operator will collapse the family.

The default candidate vocabulary is:

- `SYMMETRY_ORBIT`
- `HIGHER_ARITY_XOR`
- `CARDINALITY_PB`
- `HORN_RENAMABLE`
- `BACKDOOR_TO_TRACTABLE`
- `GRAPH_DECOMPOSITION`

## Boundary

The frontier report is research triage. It is useful for deciding which
operator to build next, not for making benchmark or complexity claims.

## v2.2 Frontier Update

The next frontier split is now explicit:

- graph-coloring toy rows can carry native symmetry certificates and direct SAT
  witness reconstruction;
- pigeonhole rows carry exact orbit and cardinality/PB diagnostics only;
- a future operator must combine symmetry preservation with cardinality/PB
  reasoning before any pigeonhole collapse claim is allowed.

## v2.3 Frontier Update

`G3_SYMMETRY_CARDINALITY_CERTIFIED` implements that next step for standard
`php_n_m`: exact ALO/AMO detection over assignment variables plus a native
counting certificate. The frontier remains open for nonstandard encodings,
larger certificate compression, and DRAT export.

## v2.4 Operator Genesis Update

The frontier now feeds `witnora_core.operator_genesis`. The genesis engine
does more than map fingerprints to a fixed list: it emits operator schemas with
trigger signatures, preservation obligations, certificate sketches, safety
risks, promotion criteria, and theorem-candidate queue entries.

This is still a planning layer. A generated schema is not an implemented
operator, not a proof, and not a benchmark result. The next operator becomes
trusted only after implementation, independent checking, targeted tests,
red-team review, and a frozen artifact.

## v2.5 First Generated Operator Prototype

v2.5 promotes `ORBIT_COUNTING_COLLAPSE` into
`G4_ORBIT_CAPACITY_COUNTING_PROTOTYPE`. The frontier claim is narrow: local
Hall/capacity deficits over exact assignment/resource CNFs can emit native
certificates when the checker expands the evidence against the original CNF.

This is not counted as a novel G4 delta for complete matching rows that are just
the G3 pigeonhole pattern in another notation. It is not a full matching solver
or a DRAT proof route.

## v2.6 Affine-Residue Frontier Update

The next promoted candidate is `MODULAR_RESIDUE_COLLAPSE`, implemented as
`G5_HIGH_ARITY_AFFINE_RESIDUE_PROTOTYPE`. It addresses parity-over-cap rows by
raising the exact full-CNF affine arity bound under a native checker.

This is not broad modular arithmetic solving. It is exact GF(2) affine
certificate evidence only, with no heuristic mining, no CryptoMiniSat-style
claim, and no DRAT claim.

## v2.7 Proof-Motif Frontier Update

The next promoted candidate is `PROOF_MOTIF_COMPRESSION`, implemented as
`G6_PROOF_MOTIF_COMPRESSION_PROTOTYPE`. Unlike G1-G5, it is not primarily a
semantic detector. It targets repeated proof structure: verify one motif proof,
check every instantiation, and account for compressed macro-proof size.

Tseitin/XOR-like rows are treated as duplicate controls when prior XOR
grammars may already handle them. G6 evidence is counted only when the native
proof-motif checker verifies template and reuse obligations.
