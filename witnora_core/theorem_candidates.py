"""Theorem-candidate registry for the collapse-theory program.

These records are research objects. They are not theorem claims unless their
status and proof obligations say so.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class TheoremCandidate:
    id: str
    name: str
    statement: str
    status: str
    supporting_witnesses: list[str] = field(default_factory=list)
    required_proof_obligations: list[str] = field(default_factory=list)
    known_counterexamples: list[str] = field(default_factory=list)
    forbidden_interpretations: list[str] = field(default_factory=list)
    next_experiments: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def initial_theorem_candidates() -> list[TheoremCandidate]:
    return [
        TheoremCandidate(
            id="TC-001",
            name="Bounded XOR Strictness",
            statement=(
                "There exists a bounded profile B such that W_B(G0_BASE) is a proper observed "
                "subset of W_B(G1_XOR), witnessed by Tseitin and XOR-chain instances with "
                "externally verified DRAT proofs where available."
            ),
            status="EMPIRICAL_EVIDENCE",
            supporting_witnesses=["tseitin_10", "xor_chain_unsat_n5"],
            required_proof_obligations=[
                "State the bound profile B explicitly.",
                "Replay G0_BASE no-collapse under B.",
                "Replay G1_XOR collapse and certificate/proof verification under B.",
            ],
            forbidden_interpretations=[
                "Does not prove P vs NP progress.",
                "Does not prove an absolute lower bound against all algorithms.",
                "Does not claim broad XOR extraction.",
            ],
            next_experiments=["Scale the witness family under fixed bounds.", "Formalize the G0 obstruction condition."],
        ),
        TheoremCandidate(
            id="TC-002",
            name="Formal XOR Strictness on Tseitin",
            statement=(
                "For suitable graph families and a fixed bounded-width route, Tseitin formulas "
                "resist G0-style bounded-width collapse under the stated cap but collapse under exact "
                "XOR extraction and affine elimination."
            ),
            status="CONJECTURE",
            supporting_witnesses=["tseitin_10"],
            required_proof_obligations=[
                "Specify the graph family.",
                "Prove the G0 bounded-width obstruction for the chosen cap.",
                "Prove exact XOR encodings are detected and externally certifiable.",
            ],
            forbidden_interpretations=[
                "Does not claim all Tseitin formulas are solved.",
                "Does not claim general SAT solving.",
            ],
            next_experiments=["Collect larger certified Tseitin rows.", "Write a formal proof sketch for the bounded G0 obstruction."],
        ),
        TheoremCandidate(
            id="TC-003",
            name="Symmetry Collapse Conjecture",
            statement=(
                "There exists a grammar G2_SYM extending G1_XOR with deterministic orbit/symmetry "
                "collapse such that selected pigeonhole or graph-coloring families move from "
                "NO_COLLAPSE_FOUND to certified collapse under bounded profiles."
            ),
            status="CONJECTURE",
            supporting_witnesses=[],
            required_proof_obligations=[
                "Define a sound orbit quotient or symmetry-breaking transformation.",
                "Define witness reconstruction or proof preservation.",
                "Externally verify any UNSAT claim.",
            ],
            forbidden_interpretations=[
                "Current syntactic orbit diagnostics are not a certified collapse.",
                "Does not claim pigeonhole has been collapsed by symmetry.",
            ],
            next_experiments=["Design certified quotient rules for a toy orbit family.", "Attack pigeonhole with certificate-preserving symmetry operators."],
        ),
        TheoremCandidate(
            id="TC-004",
            name="Collapse Obstruction Conjecture",
            statement=(
                "For each grammar G_i, non-collapse under a bound profile can be explained by a finite "
                "family of structural obstruction signatures useful for choosing the next operator."
            ),
            status="CONJECTURE",
            supporting_witnesses=[],
            required_proof_obligations=[
                "Define obstruction signatures formally.",
                "Show signatures are complete for a restricted grammar/family pair.",
                "Show an operator removes one obstruction without unsound claims.",
            ],
            forbidden_interpretations=[
                "Does not classify all resistant instances.",
                "Does not prove lower bounds against arbitrary algorithms.",
            ],
            next_experiments=["Collect obstruction records across pigeonhole, parity, and graph-coloring families."],
        ),
        TheoremCandidate(
            id="TC-005",
            name="Bounded Symmetry Strictness Candidate",
            statement=(
                "There exists a bounded profile B such that W_B(G1_XOR) is strictly contained in "
                "W_B(G2_SYMMETRY_CERTIFIED), witnessed by a family where certified symmetry "
                "reasoning produces a valid collapse path not available to G1_XOR."
            ),
            status="CONJECTURE",
            supporting_witnesses=[],
            required_proof_obligations=[
                "Find a family where G1_XOR records bounded no-collapse.",
                "Validate exact automorphism generators against the original CNF.",
                "Discharge SBP preservation or witness reconstruction obligations.",
                "Separate native symmetry certification from DRAT certification.",
            ],
            forbidden_interpretations=[
                "Does not claim W(G1) is strictly contained in W(G2) as an absolute theorem.",
                "Does not claim symmetry collapses pigeonhole.",
                "Does not claim P vs NP progress.",
            ],
            next_experiments=["Scale certified graph-coloring witness reconstruction.", "Develop a preservation checker for pigeonhole SBPs."],
        ),
        TheoremCandidate(
            id="TC-006",
            name="Graph-Coloring Symmetry Collapse Candidate",
            statement=(
                "Small graph-coloring encodings with color-permutation automorphisms admit certified "
                "symmetry evidence and direct witness reconstruction for selected SAT rows."
            ),
            status="EMPIRICAL_EVIDENCE",
            supporting_witnesses=["cycle_4_3color", "cycle_6_3color"],
            required_proof_obligations=[
                "Validate color permutation automorphisms exactly.",
                "Check reconstructed assignments against the original CNF.",
                "Show that any SBP used is justified by orbit-representative preservation, not implication.",
            ],
            forbidden_interpretations=[
                "Does not claim graph coloring is solved generally.",
                "Does not claim an UNSAT proof unless one is checked against the original CNF.",
            ],
            next_experiments=["Add more certified SAT graph-coloring examples.", "Investigate certificate-preserving quotient maps."],
        ),
        TheoremCandidate(
            id="TC-007",
            name="Pigeonhole Symmetry/Cardinality Collapse Candidate",
            statement=(
                "Pigeonhole likely requires combined symmetry/orbit and cardinality/PB reasoning to "
                "produce a certified collapse path."
            ),
            status="CONJECTURE",
            supporting_witnesses=[],
            required_proof_obligations=[
                "Validate row/hole automorphisms exactly.",
                "Detect cardinality/PB structure exactly.",
                "Define a sound preservation or proof-export route before claiming collapse.",
            ],
            forbidden_interpretations=[
                "Does not claim symmetry alone collapses pigeonhole.",
                "Does not claim general pigeonhole encodings beyond recognized standard php_n_m forms.",
                "Does not treat symmetry-breaking predicates as implied clauses.",
            ],
            next_experiments=["Build a certified cardinality operator.", "Design pigeonhole SBP preservation checks."],
        ),
        TheoremCandidate(
            id="TC-008",
            name="SBP Preservation Lemma",
            statement=(
                "If G is a verified automorphism group of F and SBP selects at least one representative "
                "from every G-orbit of satisfying assignments, then F is satisfiable iff F with SBP is satisfiable."
            ),
            status="FORMAL_PROOF_SKETCH",
            supporting_witnesses=["symmetric_exactly_one_4", "cycle_4_3color"],
            required_proof_obligations=[
                "Prove each generator preserves F.",
                "Prove each satisfying-assignment orbit has an SBP-satisfying representative.",
                "Verify any reconstructed witness against the original formula.",
            ],
            forbidden_interpretations=[
                "Does not say SBP clauses are logical consequences of F.",
                "Does not provide DRAT certification unless a proof against original CNF is checked.",
            ],
            next_experiments=["Mechanize the orbit-representative proof for larger SBP templates."],
        ),
        TheoremCandidate(
            id="TC-009",
            name="Pigeonhole Native Certification Theorem",
            statement=(
                "For standard php_n_m encodings with n > m, the G3 cardinality detector can emit "
                "a polynomial-size native pigeonhole counting certificate checkable directly against "
                "the original CNF assignment variables x[pigeon,hole]."
            ),
            status="FORMAL_PROOF_SKETCH",
            supporting_witnesses=["php_3_2", "php_4_3", "php_5_4", "php_6_5"],
            required_proof_obligations=[
                "Verify each ALO clause over x[pigeon,hole] variables exists in the original CNF.",
                "Verify each required AMO pair clause exists in the original CNF.",
                "Check n > m and the counting contradiction.",
                "Keep the certificate native unless a DRAT proof against the original CNF is checked.",
            ],
            forbidden_interpretations=[
                "Does not claim a complete PB solver.",
                "Does not claim general pigeonhole encodings beyond recognized standard php_n_m forms.",
                "Does not claim P vs NP progress.",
            ],
            next_experiments=["Add DRAT export for native PHP certificates.", "Broaden recognition only with exact schema checks."],
        ),
        TheoremCandidate(
            id="TC-010",
            name="G3 Cardinality Strictness Candidate",
            statement=(
                "There exists a bounded profile B where selected php_n_m instances are in "
                "W_B(G3_SYMMETRY_CARDINALITY_CERTIFIED) but are not found by G1_XOR or "
                "G2_SYMMETRY_CERTIFIED under the same bounded experiment."
            ),
            status="EMPIRICAL_EVIDENCE",
            supporting_witnesses=["php_4_3", "php_5_4"],
            required_proof_obligations=[
                "Record G1 and G2 outcomes under the same bound profile.",
                "Replay native G3 PHP certificates.",
                "Provide a lower-bound proof before promoting this to theorem status.",
            ],
            forbidden_interpretations=[
                "Does not claim G3 strictness as a theorem.",
                "Does not prove lower bounds against all algorithms.",
            ],
            next_experiments=["Formalize the bounded non-collapse side for G1/G2.", "Scale standard php_n_m native certificates."],
        ),
        TheoremCandidate(
            id="TC-011",
            name="Symmetry + Cardinality Pigeonhole Collapse Candidate",
            statement=(
                "Symmetry helps identify and canonicalize pigeonhole assignment-grid structure, while "
                "cardinality/counting produces the native UNSAT certificate."
            ),
            status="EMPIRICAL_EVIDENCE",
            supporting_witnesses=["php_3_2", "php_4_3", "php_5_4", "php_6_5"],
            required_proof_obligations=[
                "Keep symmetry evidence separate from the counting contradiction.",
                "Verify assignment-grid ALO/AMO clauses against the original CNF.",
                "Do not claim symmetry alone solves pigeonhole.",
            ],
            forbidden_interpretations=[
                "Does not claim symmetry alone solves pigeonhole.",
                "Does not claim a DRAT proof.",
            ],
            next_experiments=["Use symmetry to compress larger PHP certificates without changing the native counting proof."],
        ),
        TheoremCandidate(
            id="TC-012",
            name="Hall/Capacity Native Certification Candidate",
            statement=(
                "For exact assignment CNFs with ALO demand constraints and exact capacity constraints, "
                "if a provided subset S satisfies |S| > capacity(N(S)), then a native capacity-deficit "
                "certificate proves UNSAT and is checkable directly against the original CNF."
            ),
            status="FORMAL_PROOF_SKETCH",
            supporting_witnesses=["hall_local_4_3", "hall_local_5_4", "capacity_deficit_5_over_4"],
            required_proof_obligations=[
                "Verify every item in S has a source ALO clause over its allowed neighborhood.",
                "Verify every resource in N(S) has exact source capacity clauses.",
                "Verify |S| > capacity(N(S)).",
                "Keep the result native unless an external proof against the original CNF is checked.",
            ],
            forbidden_interpretations=[
                "Does not claim a full matching solver.",
                "Does not claim a full allocation solver.",
                "Does not claim DRAT verification.",
                "Does not claim P vs NP progress.",
            ],
            next_experiments=["Broaden exact capacity encodings only when checkable.", "Explore DRAT bridges for native Hall certificates."],
        ),
        TheoremCandidate(
            id="TC-013",
            name="G4 Orbit-Capacity Strictness Candidate",
            statement=(
                "There exists a bounded profile B where local Hall-deficit formulas are native-certified "
                "by G4_ORBIT_CAPACITY_COUNTING_PROTOTYPE but are not counted as G3 standard pigeonhole "
                "recognition results."
            ),
            status="EMPIRICAL_EVIDENCE_NOT_THEOREM",
            supporting_witnesses=["hall_local_4_3", "hall_local_5_4"],
            required_proof_obligations=[
                "Separate local Hall-deficit rows from complete matching duplicates of G3 pigeonhole.",
                "Replay G4 native certificates with the independent checker.",
                "Provide formal bounded non-collapse evidence before promoting to theorem status.",
            ],
            forbidden_interpretations=[
                "Does not claim G4 strictness as a theorem.",
                "Does not prove a lower bound against G3.",
                "Does not claim all matching or allocation formulas are solved.",
            ],
            next_experiments=["Find a family-level bounded proof obligation for G3 non-recognition.", "Scale local Hall-deficit fixtures."],
        ),
        TheoremCandidate(
            id="TC-014",
            name="Operator Genesis Success Candidate",
            statement=(
                "The v2.4-generated ORBIT_COUNTING_COLLAPSE candidate was promoted to a v2.5 "
                "implemented prototype with a native checker and bounded local Hall-deficit delta evidence."
            ),
            status="EMPIRICAL_EVIDENCE",
            supporting_witnesses=["hall_local_4_3", "hall_local_5_4"],
            required_proof_obligations=[
                "Record the generated candidate origin.",
                "Replay the native orbit-capacity checker.",
                "Keep generated-operator success separate from theorem status.",
            ],
            forbidden_interpretations=[
                "Does not mean the generated operator is a theorem.",
                "Does not imply automatic operator generation has solved SAT.",
                "Does not claim P vs NP progress.",
            ],
            next_experiments=["Use the promotion pipeline to select a second generated operator prototype."],
        ),
    ]


def theorem_candidates_markdown(candidates: list[TheoremCandidate]) -> str:
    lines = [
        "# Theorem Candidates",
        "",
        "These are conjectural or evidence-backed research targets. They are not promoted to theorem status unless the listed proof obligations are discharged.",
        "",
    ]
    for candidate in candidates:
        lines.extend(
            [
                f"## {candidate.id}: {candidate.name}",
                "",
                f"Status: `{candidate.status}`",
                "",
                candidate.statement,
                "",
                "Proof obligations:",
            ]
        )
        for obligation in candidate.required_proof_obligations:
            lines.append(f"- {obligation}")
        lines.append("")
        lines.append("Forbidden interpretations:")
        for item in candidate.forbidden_interpretations:
            lines.append(f"- {item}")
        lines.append("")
        lines.append("Next experiments:")
        for item in candidate.next_experiments:
            lines.append(f"- {item}")
        lines.append("")
    return "\n".join(lines)
