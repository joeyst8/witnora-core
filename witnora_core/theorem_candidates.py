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
    lemma_count: int | None = None
    proof_obligation_count: int | None = None
    dependency_on_g5_affine_soundness: bool | None = None
    fixed_c_polynomiality: bool | None = None
    native_certificate_only: bool | None = None
    external_proof_bridge_absent: bool | None = None
    finite_tests_are_support_only: bool | None = None

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
        TheoremCandidate(
            id="TC-015",
            name="High-Arity Affine Native Certification Candidate",
            statement=(
                "For exact full CNF encodings of GF(2) affine equations up to bounded arity K, "
                "G5 can extract equations and emit a native Gaussian-elimination certificate checkable "
                "against the original CNF."
            ),
            status="FORMAL_PROOF_SKETCH",
            supporting_witnesses=["parity_arity_7_unsat", "parity_arity_8_unsat", "parity_arity_9_unsat", "parity_arity_10_unsat"],
            required_proof_obligations=[
                "Verify every forbidden-assignment clause for each extracted equation exists in the original CNF.",
                "Replay deterministic GF(2) Gaussian elimination using only row swaps and row-xor operations.",
                "For UNSAT, verify a 0 = 1 contradiction row.",
                "For SAT, verify the assignment against the original CNF.",
            ],
            forbidden_interpretations=[
                "Does not claim broad modular arithmetic solving.",
                "Does not claim CryptoMiniSat-style XOR mining.",
                "Does not claim DRAT verification.",
                "Does not claim P vs NP progress.",
            ],
            next_experiments=["Try arity 11-12 under explicit proof-size caps.", "Investigate a DRAT bridge only after native checks are stable."],
        ),
        TheoremCandidate(
            id="TC-016",
            name="G5 Affine Residue Strictness Candidate",
            statement=(
                "There exists a bounded profile B where exact parity-over-cap formulas are certified by "
                "G5_HIGH_ARITY_AFFINE_RESIDUE_PROTOTYPE but not by G1_XOR under its lower extraction cap."
            ),
            status="EMPIRICAL_EVIDENCE_NOT_THEOREM",
            supporting_witnesses=["parity_arity_7_unsat", "parity_arity_8_unsat"],
            required_proof_obligations=[
                "State the G1 extraction cap and G5 arity cap explicitly.",
                "Replay native G5 certificates.",
                "Provide formal bounded non-collapse evidence before promoting to theorem status.",
            ],
            forbidden_interpretations=[
                "Does not claim G5 strictness as a theorem.",
                "Does not prove lower bounds against G1.",
                "Does not claim full parity family solving beyond configured exact encodings.",
            ],
            next_experiments=["Scale exact parity-over-cap rows under fixed arity caps."],
        ),
        TheoremCandidate(
            id="TC-017",
            name="Operator Genesis Success Candidate 2",
            statement=(
                "The v2.4-generated MODULAR_RESIDUE_COLLAPSE candidate was promoted to a v2.6 "
                "implemented prototype with native GF(2) certificates and bounded operator-delta evidence."
            ),
            status="EMPIRICAL_EVIDENCE",
            supporting_witnesses=["mixed_affine_arity_8_unsat", "mixed_affine_arity_8_sat"],
            required_proof_obligations=[
                "Record the generated candidate origin.",
                "Replay the native affine-residue checker.",
                "Keep generated-operator success separate from theorem status.",
            ],
            forbidden_interpretations=[
                "Does not mean generated operator discovery proves a theorem.",
                "Does not imply broad modular arithmetic solving.",
                "Does not claim P vs NP progress.",
            ],
            next_experiments=["Use the promotion pipeline to select a third generated operator prototype."],
        ),
        TheoremCandidate(
            id="TC-018",
            name="Proof Motif Native Certification Candidate",
            statement=(
                "For formulas containing repeated isomorphic local proof motifs, G6 can emit a native "
                "macro-proof certificate whose checker verifies one motif template and all instantiations."
            ),
            status="FORMAL_PROOF_SKETCH",
            supporting_witnesses=["motif_ladder_4", "motif_ladder_8", "renamed_conflict_motif_8"],
            required_proof_obligations=[
                "Verify each motif template as a native resolution or unit-propagation proof.",
                "Verify each reuse substitution against original source clauses.",
                "Verify each instantiated proof hash and derived lemma.",
                "Verify the final macro contradiction uses only verified instantiated lemmas.",
            ],
            forbidden_interpretations=[
                "Does not claim DRAT verification.",
                "Does not claim proof motif compression is complete for structured formulas.",
                "Does not claim repeated patterns are proofs without checker verification.",
                "Does not claim P vs NP progress.",
            ],
            next_experiments=["Try repeated proof motifs in non-synthetic scheduling and graph gadget families."],
        ),
        TheoremCandidate(
            id="TC-019",
            name="G6 Proof Motif Compression Strictness Candidate",
            statement=(
                "There exists a bounded profile B where repeated-motif formulas are certified by G6 "
                "within proof-size bounds while G0-G5 fail or exceed configured proof-size bounds."
            ),
            status="EMPIRICAL_EVIDENCE_NOT_THEOREM",
            supporting_witnesses=["motif_ladder_16", "motif_chain_with_selectors_8"],
            required_proof_obligations=[
                "State the configured proof-size bound.",
                "Replay native G6 macro-proof certificates.",
                "Provide formal bounded non-collapse or proof-size evidence before promoting to theorem status.",
            ],
            forbidden_interpretations=[
                "Does not claim G6 strictness as a theorem.",
                "Does not prove lower bounds against G0-G5.",
                "Does not count Tseitin/XOR duplicates as novel G6 deltas.",
            ],
            next_experiments=["Measure compression ratios on larger repeated motif ladders under fixed bounds."],
        ),
        TheoremCandidate(
            id="TC-020",
            name="Operator Genesis Success Candidate 3",
            statement=(
                "The v2.4-generated PROOF_MOTIF_COMPRESSION candidate was promoted to a v2.7 "
                "implemented prototype with native macro-proof certificates and bounded operator-delta evidence."
            ),
            status="EMPIRICAL_EVIDENCE",
            supporting_witnesses=["motif_ladder_8", "motif_chain_with_selectors_8"],
            required_proof_obligations=[
                "Record the generated candidate origin.",
                "Replay the native proof-motif checker.",
                "Keep generated-operator success separate from theorem status.",
            ],
            forbidden_interpretations=[
                "Does not mean generated operator discovery proves a theorem.",
                "Does not imply a complete proof-compression system.",
                "Does not claim P vs NP progress.",
            ],
            next_experiments=["Use the promotion pipeline to select a fourth generated operator prototype."],
        ),
        TheoremCandidate(
            id="TC-021",
            name="Bounded XOR Strictness Candidate",
            statement=(
                "Under an explicit bound profile B, G1_XOR has empirical certificate-backed rows "
                "on Tseitin and XOR-chain families not certified by G0_BASE in the recorded bounded run."
            ),
            status="EMPIRICAL_EVIDENCE_NOT_THEOREM",
            supporting_witnesses=["tseitin", "xor-chain"],
            required_proof_obligations=[
                "Specify the bound profile B.",
                "Replay G1 certificates/proofs.",
                "Replace bounded G0 no-collapse records with formal non-collapse proof before theorem status.",
            ],
            forbidden_interpretations=[
                "Does not claim a strictness theorem.",
                "Does not claim a lower bound against all algorithms.",
                "Does not claim P vs NP progress.",
            ],
            next_experiments=["Formalize the G0 non-collapse side for selected bounded Tseitin rows."],
        ),
        TheoremCandidate(
            id="TC-022",
            name="Bounded Symmetry Strictness Candidate",
            statement=(
                "Under an explicit bound profile B, G2_SYMMETRY_CERTIFIED has empirical witness "
                "reconstruction rows not certified by G1_XOR in the recorded bounded run."
            ),
            status="EMPIRICAL_EVIDENCE_NOT_THEOREM",
            supporting_witnesses=["cycle_4_3color", "cycle_6_3color"],
            required_proof_obligations=[
                "Replay certified automorphism and witness-reconstruction checks.",
                "Prove G1 non-collapse under the same bound before theorem status.",
                "Keep native symmetry certification separate from DRAT.",
            ],
            forbidden_interpretations=[
                "Does not claim graph coloring is solved generally.",
                "Does not claim W(G1) is strictly contained in W(G2) as a theorem.",
            ],
            next_experiments=["Scale graph-coloring symmetry examples with fixed bound profiles."],
        ),
        TheoremCandidate(
            id="TC-023",
            name="Bounded Pigeonhole/Cardinality Strictness Candidate",
            statement=(
                "Under an explicit bound profile B, G3_SYMMETRY_CARDINALITY_CERTIFIED has native "
                "pigeonhole counting certificates not certified by G2_SYMMETRY_CERTIFIED alone."
            ),
            status="EMPIRICAL_EVIDENCE_NOT_THEOREM",
            supporting_witnesses=["php_3_2", "php_4_3", "php_5_4", "php_6_5"],
            required_proof_obligations=[
                "Replay native PHP counting certificates.",
                "Prove symmetry-only G2 cannot certify the counting contradiction under the bound.",
                "Keep standard assignment-grid scope explicit.",
            ],
            forbidden_interpretations=[
                "Does not claim a complete PB solver.",
                "Does not claim G3 strictness as a theorem.",
                "Does not claim P vs NP progress.",
            ],
            next_experiments=["Mechanize a proof sketch for the standard PHP native checker."],
        ),
        TheoremCandidate(
            id="TC-024",
            name="Bounded Orbit-Capacity Strictness Candidate",
            statement=(
                "Under an explicit bound profile B, G4_ORBIT_CAPACITY_COUNTING_PROTOTYPE has "
                "native local Hall/capacity certificates not counted as duplicate G3 pigeonhole rows."
            ),
            status="EMPIRICAL_EVIDENCE_NOT_THEOREM",
            supporting_witnesses=["hall_local_3_2", "hall_local_4_3", "hall_local_5_4"],
            required_proof_obligations=[
                "Replay orbit-capacity checker output.",
                "Prove G3's standard PHP recognizer does not cover local Hall deficits under the bound.",
                "Keep complete matching duplicates out of novel delta counts.",
            ],
            forbidden_interpretations=[
                "Does not claim a complete matching or allocation solver.",
                "Does not claim G4 strictness as a theorem.",
            ],
            next_experiments=["Add more local deficit families with exact checker evidence."],
        ),
        TheoremCandidate(
            id="TC-025",
            name="Bounded High-Arity Affine Strictness Candidate",
            statement=(
                "Under an explicit bound profile B, G5_HIGH_ARITY_AFFINE_RESIDUE_PROTOTYPE has "
                "native GF(2) certificates for exact parity-over-cap rows not handled by the lower G1 cap."
            ),
            status="EMPIRICAL_EVIDENCE_NOT_THEOREM",
            supporting_witnesses=["parity_arity_7_unsat", "parity_arity_8_unsat", "parity_arity_9_unsat", "parity_arity_10_unsat"],
            required_proof_obligations=[
                "Replay exact full-CNF affine extraction and GF(2) trace checks.",
                "State the lower G1 cap and G5 cap.",
                "Prove lower-cap non-coverage before theorem status.",
            ],
            forbidden_interpretations=[
                "Does not claim broad modular arithmetic solving.",
                "Does not claim heuristic XOR mining.",
                "Does not claim G5 strictness as a theorem.",
            ],
            next_experiments=["Write a proof sketch for exact high-arity affine checker soundness."],
        ),
        TheoremCandidate(
            id="TC-026",
            name="Bounded Proof-Motif Strictness Candidate",
            statement=(
                "Under an explicit bound profile B, G6_PROOF_MOTIF_COMPRESSION_PROTOTYPE has native "
                "macro-proof certificates for repeated-motif rows not certified by G5 within the proof-size profile."
            ),
            status="EMPIRICAL_EVIDENCE_NOT_THEOREM",
            supporting_witnesses=["motif_ladder_8", "renamed_conflict_motif_8", "motif_chain_with_selectors_8"],
            required_proof_obligations=[
                "Replay template, reuse, substitution, and final contradiction checks.",
                "State the proof-size bound.",
                "Prove G5 non-certification under the same bound before theorem status.",
            ],
            forbidden_interpretations=[
                "Does not claim proof motif compression is complete.",
                "Does not count Tseitin/XOR duplicates as novel G6 deltas.",
                "Does not claim P vs NP progress.",
            ],
            next_experiments=["Search for non-synthetic repeated proof motifs with checked reuse sites."],
        ),
        TheoremCandidate(
            id="TC-027",
            name="Collapse Hierarchy Strictness Program",
            statement=(
                "The G0-G6 ladder is a program for turning empirical operator deltas into bounded "
                "strictness theorems by discharging explicit proof obligations."
            ),
            status="FORMAL_PROOF_OBLIGATION",
            supporting_witnesses=["G0-G6 hierarchy"],
            required_proof_obligations=[
                "Prove non-collapse side for each edge.",
                "Mechanize native checker soundness arguments.",
                "Define scaling witness families.",
            ],
            forbidden_interpretations=[
                "Does not mark the hierarchy as proven strict.",
                "Does not claim hierarchy completeness.",
                "Does not claim P vs NP progress.",
            ],
            next_experiments=["Prioritize the smallest edge with a plausible formal non-collapse argument."],
        ),
        TheoremCandidate(
            id="TC-028",
            name="Collapse Hierarchy Completeness Speculation",
            statement=(
                "Future operator hierarchies may cover broader verifier-to-witness classes, but v2.8 "
                "records this only as speculative program material."
            ),
            status="SPECULATIVE_PROGRAM",
            supporting_witnesses=["gap analysis"],
            required_proof_obligations=[
                "Define the target formula universe.",
                "Prove coverage only for restricted classes.",
                "Avoid completeness language without proof.",
            ],
            forbidden_interpretations=[
                "No hierarchy completeness claim.",
                "No complete SAT algorithm claim.",
            ],
            next_experiments=["Use gap analysis to select a narrow v2.9 target."],
        ),
        TheoremCandidate(
            id="TC-029",
            name="Operator Genesis Progress Candidate",
            statement=(
                "Operator genesis has promoted ORBIT_COUNTING_COLLAPSE, MODULAR_RESIDUE_COLLAPSE, "
                "and PROOF_MOTIF_COMPRESSION into bounded prototypes with native checkers."
            ),
            status="EMPIRICAL_EVIDENCE_NOT_THEOREM",
            supporting_witnesses=["v2.5", "v2.6", "v2.7"],
            required_proof_obligations=[
                "Separate implemented prototypes from theorem status.",
                "Track safety and duplicate controls.",
                "Show each checker is sound.",
            ],
            forbidden_interpretations=[
                "Generated operators are not automatically trusted.",
                "No autonomous theorem discovery claim.",
            ],
            next_experiments=["Choose v2.9 from gap-ranked proof obligations."],
        ),
        TheoremCandidate(
            id="TC-030",
            name="Obstruction-to-Operator Program Candidate",
            statement=(
                "Persistent obstruction fingerprints can guide candidate operator generation and "
                "proof-obligation queues."
            ),
            status="CONJECTURE",
            supporting_witnesses=["operator genesis fingerprints", "gap analysis"],
            required_proof_obligations=[
                "Show fingerprint stability.",
                "Show candidate generation improves next-operator selection.",
                "Prove promoted operators preserve satisfiability or certificates.",
            ],
            forbidden_interpretations=[
                "Not a proof of obstruction completeness.",
                "No lower-bound claim.",
            ],
            next_experiments=["Audit v2.9 candidate selection against v2.8 gap analysis."],
        ),
        TheoremCandidate(
            id="TC-031",
            name="Restricted G0 Width vs G1 XOR Strictness Candidate",
            statement=(
                "For a fixed cap c, finite exact-XOR witnesses can be rejected by the restricted "
                "G0_WIDTH_C route due to verified width obstruction and accepted by "
                "G1_XOR_FOR_STRICTNESS due to checked exact XOR extraction and native GF(2) elimination."
            ),
            status="FORMAL_PROOF_SKETCH",
            supporting_witnesses=["tseitin_10", "xor_chain_unsat_n5"],
            required_proof_obligations=[
                "Keep the prior grammar restricted to G0_WIDTH_C.",
                "Verify exact bounded-width obstruction for each finite witness.",
                "Verify exact XOR extraction and GF(2) certificate for G1_XOR_FOR_STRICTNESS.",
                "Do not promote to full G0_BASE strictness without proving every G0 route cannot collapse the family.",
            ],
            forbidden_interpretations=[
                "Does not prove full G0_BASE strictness.",
                "Does not prove hierarchy completeness.",
                "Does not prove P vs NP progress.",
                "Does not prove a scalable Tseitin family theorem.",
            ],
            next_experiments=[
                "Mechanize a scalable treewidth lower-bound proof for bounded-degree Tseitin graph families.",
                "Audit safe preprocessors before considering G0_WIDTH_C_WITH_SAFE_PREPROCESS.",
            ],
        ),
        TheoremCandidate(
            id="TC-032",
            name="Scalable Tseitin Width Obstruction Obligation",
            statement=(
                "Tseitin formulas over suitable graph families are expected to provide scalable "
                "width/treewidth obstruction evidence, but v2.9 treats this as a proof obligation "
                "unless an explicit graph-theoretic proof is supplied."
            ),
            status="FORMAL_PROOF_OBLIGATION",
            supporting_witnesses=["scalable Tseitin family"],
            required_proof_obligations=[
                "Specify the graph family.",
                "Prove the required treewidth or induced-width lower bound.",
                "Show any allowed preprocessing does not lower the formula below cap c.",
                "Connect the lower bound to the restricted G0_WIDTH_C route only unless full G0 obligations are discharged.",
            ],
            forbidden_interpretations=[
                "No expander family theorem is marked proven.",
                "No lower bound against all G0 operators is claimed.",
                "No P vs NP progress claim.",
            ],
            next_experiments=["Write a formal graph-family proof note and corresponding checker assumptions."],
        ),
        TheoremCandidate(
            id="TC-033",
            name="Finite Restricted G0-vs-G1 Strictness Certificate",
            statement=(
                "For the finite checked instance set I, each F in I is rejected by G0_WIDTH_C "
                "under cap c via verified width obstruction and accepted by G1_XOR_FOR_STRICTNESS "
                "via verified XOR certificate."
            ),
            status="FINITE_STRICTNESS_CERTIFIED",
            supporting_witnesses=[
                "tseitin_10",
                "xor_chain_unsat_n5",
                "tseitin_12",
                "xor_chain_unsat_n7",
                "tseitin_14",
                "xor_chain_unsat_n9",
            ],
            required_proof_obligations=[
                "Replay every finite width obstruction certificate.",
                "Replay every G1 XOR upper-bound certificate.",
                "Keep the claim scope finite and restricted to G0_WIDTH_C.",
                "Leave scalable Tseitin/expander strictness as a proof obligation.",
            ],
            forbidden_interpretations=[
                "Does not prove full G0_BASE strictness.",
                "Does not prove a scalable family theorem.",
                "Does not prove hierarchy strictness.",
                "Does not prove P vs NP progress.",
            ],
            next_experiments=[
                "Reuse the finite certificate format for other hierarchy edges.",
                "Attempt a scalable graph-family proof separately from finite certification.",
            ],
        ),
        TheoremCandidate(
            id="TC-034",
            name="Finite G1-to-G2 Empirical Edge Delta Certificate",
            statement=(
                "For the finite checked instance set I, each F in I is not accepted by G1_XOR "
                "under the configured bound profile during replay, while G2_SYMMETRY_CERTIFIED "
                "verifies a SAT witness reconstruction."
            ),
            status="FINITE_EMPIRICAL_EDGE_DELTA_CERTIFIED",
            supporting_witnesses=[
                "cycle_4_3color",
                "cycle_6_3color",
                "cycle_8_3color",
                "cycle_10_3color",
            ],
            required_proof_obligations=[
                "Replay lower G1_XOR bounded non-acceptance.",
                "Do not call replay non-acceptance a lower-bound proof.",
                "Replay G2 symmetry witness reconstruction and verify the final assignment against the original CNF.",
                "Keep claim scope finite and empirical.",
            ],
            forbidden_interpretations=[
                "Not lower-bound strictness.",
                "Not full G1-vs-G2 theorem.",
                "Not a family theorem.",
                "Not P vs NP progress.",
            ],
            next_experiments=[
                "Develop an actual lower-obstruction certificate for G1 if a strictness theorem is desired.",
                "Reuse finite edge-delta evidence grading for later hierarchy edges.",
            ],
        ),
        TheoremCandidate(
            id="TC-035",
            name="G1-to-G2 Symmetry Strictness Candidate",
            statement=(
                "The graph-coloring symmetry edge may admit a bounded strictness theorem only if a lower-bound "
                "or obstruction certificate for G1_XOR is supplied in addition to the existing G2 witness evidence."
            ),
            status="FORMAL_PROOF_OBLIGATION",
            supporting_witnesses=["cycle graph coloring symmetry family"],
            required_proof_obligations=[
                "Prove G1_XOR cannot accept the selected family under the same bound profile.",
                "Keep finite replay evidence separate from lower-bound evidence.",
                "Verify G2 native symmetry certificate soundness.",
            ],
            forbidden_interpretations=[
                "No G1 lower bound is supplied by v2.11.",
                "No G1-vs-G2 family theorem is claimed.",
                "No hierarchy completeness claim.",
                "No P vs NP progress claim.",
            ],
            next_experiments=["Search for a real G1 obstruction certificate for color-symmetry families."],
        ),
        TheoremCandidate(
            id="TC-036",
            name="Obstruction Dual Certificate Candidate",
            statement=(
                "When G0-G6 do not produce a certified collapse under a bounded diagnostic profile, "
                "G7 can emit a checkable obstruction-dual certificate that records failure evidence, "
                "obstruction fingerprints, proof obligations, and a missing-operator recommendation."
            ),
            status="EMPIRICAL_EVIDENCE_NOT_THEOREM",
            supporting_witnesses=[
                "near_affine_not_exact_xor",
                "near_cardinality_incomplete_amo",
                "graph_separator_bridge_toy",
                "proof_motif_near_miss",
            ],
            required_proof_obligations=[
                "Verify the G0-G6 non-certification trace without calling it a lower bound.",
                "Verify obstruction fingerprints against source formula features.",
                "Require a checker design before any recommended operator is promoted.",
                "Keep obstruction-dual evidence separate from SAT/UNSAT result reporting.",
            ],
            forbidden_interpretations=[
                "Does not claim SAT or UNSAT.",
                "Does not claim hardness or lower bounds.",
                "Does not claim P vs NP progress.",
                "Does not claim the obstruction vocabulary is complete.",
            ],
            next_experiments=[
                "Use G7 queues to choose the next operator prototype.",
                "Audit whether repeated obstruction fingerprints stabilize across broader benchmarks.",
            ],
        ),
        TheoremCandidate(
            id="TC-037",
            name="Graph Separator Lift Soundness Candidate",
            statement=(
                "If a CNF decomposes over separator S and all component witnesses agree on the "
                "same separator assignment, then the combined assignment satisfies the original "
                "CNF when the checker verifies that assignment directly."
            ),
            status="FORMAL_PROOF_SKETCH",
            supporting_witnesses=["separator_sat_pair", "repeated_separator_chain_sat"],
            required_proof_obligations=[
                "Reconstruct the primal decomposition from the original CNF.",
                "Reject clauses whose non-separator variables span multiple components.",
                "Verify each component witness under the chosen separator assignment.",
                "Verify the combined assignment against the original CNF.",
            ],
            forbidden_interpretations=[
                "Does not claim DRAT.",
                "Does not claim separator completeness.",
                "Does not claim a graph-coloring family theorem.",
                "Does not claim P vs NP progress.",
            ],
            next_experiments=["Extend the proof sketch to recursive separator trees."],
        ),
        TheoremCandidate(
            id="TC-038",
            name="Graph Separator UNSAT Cover Candidate",
            statement=(
                "If every separator assignment is covered by at least one verified component "
                "contradiction after conditioning, then the original CNF is UNSAT under the "
                "native separator-cover checker."
            ),
            status="FORMAL_PROOF_SKETCH",
            supporting_witnesses=["separator_unsat_cover", "separator_toy_unsat"],
            required_proof_obligations=[
                "Enumerate every separator assignment within the configured bound.",
                "Verify the conditioned component contradiction for each covered assignment.",
                "Reject incomplete separator covers.",
                "Keep the native covering argument separate from DRAT claims.",
            ],
            forbidden_interpretations=[
                "Does not claim DRAT.",
                "Does not claim a general UNSAT solver.",
                "Does not claim a lower bound against prior grammars.",
                "Does not claim P vs NP progress.",
            ],
            next_experiments=["Replace bounded component search with reusable native component certificates."],
        ),
        TheoremCandidate(
            id="TC-039",
            name="G8 Empirical Edge Delta Candidate",
            statement=(
                "There exist finite separator-structured rows certified by G8_GRAPH_SEPARATOR_LIFT_PROTOTYPE "
                "while prior G0-G7 replay does not produce a certified collapse under the configured profile."
            ),
            status="FINITE_EMPIRICAL_EDGE_DELTA_CERTIFIED",
            supporting_witnesses=["separator_sat_pair", "separator_unsat_cover"],
            required_proof_obligations=[
                "Keep prior-grammar replay separate from lower-bound proof.",
                "Verify G8 SAT lift or UNSAT cover certificates.",
                "Mark duplicate prior-grammar rows as GRAPH_SEPARATOR_NO_NEW_DELTA.",
            ],
            forbidden_interpretations=[
                "No G8 strictness theorem is claimed.",
                "No lower bound against G0-G7 is claimed.",
                "No hierarchy completeness claim.",
                "No P vs NP progress claim.",
            ],
            next_experiments=["Find a certified lower obstruction for the prior grammar side."],
        ),
        TheoremCandidate(
            id="TC-040",
            name="Obstruction-To-Operator Success Candidate",
            statement=(
                "The v2.14 GRAPH_SEPARATOR_LIFT recommendation was promoted into a v2.15 "
                "implemented prototype with native certificate evidence."
            ),
            status="EMPIRICAL_EVIDENCE",
            supporting_witnesses=["graph_separator_bridge_toy", "separator_sat_pair", "separator_unsat_cover"],
            required_proof_obligations=[
                "Record the recommendation source from v2.14.",
                "Verify the G8 checker on SAT, UNSAT, and negative-control rows.",
                "Avoid claiming that all obstruction recommendations are automatically implementable.",
            ],
            forbidden_interpretations=[
                "Does not claim autonomous operator discovery is complete.",
                "Does not claim graph separator lift is a theorem.",
                "Does not claim P vs NP progress.",
            ],
            next_experiments=["Use G7 queues to select the next promoted obstruction recommendation."],
        ),
        TheoremCandidate(
            id="TC-041",
            name="Composed Orchestration Soundness Candidate",
            statement=(
                "If every step in a composed orchestration certificate verifies, every formula-state "
                "handoff hash matches, every preservation declaration is checked, and the witness/proof "
                "lift trace verifies, then the final native result is sound for the original CNF."
            ),
            status="FORMAL_PROOF_SKETCH",
            supporting_witnesses=["composed_sat_lift", "composed_unsat_cover"],
            required_proof_obligations=[
                "Verify every operator step certificate independently.",
                "Require step output formula hashes to match the next step input formula hashes.",
                "Reject diagnostic-only steps used as SAT or UNSAT certificates.",
                "Verify SAT witnesses against the original CNF.",
                "Require UNSAT preservation or a native UNSAT lift rule at every step.",
            ],
            forbidden_interpretations=[
                "Does not claim DRAT.",
                "Does not claim composition completeness.",
                "Does not claim a theorem is proven.",
                "Does not claim P vs NP progress.",
            ],
            next_experiments=["Formalize a proof-assistant version of the certificate-chain soundness sketch."],
        ),
        TheoremCandidate(
            id="TC-042",
            name="G9 Empirical Edge Delta Candidate",
            statement=(
                "There exist finite composed-obstruction rows certified by "
                "G9_COMPOSED_OPERATOR_ORCHESTRATION_PROTOTYPE while no single G0-G8 operator "
                "is counted as certifying the same row under the configured replay."
            ),
            status="FINITE_EMPIRICAL_EDGE_DELTA_CERTIFIED",
            supporting_witnesses=["affine_separator", "cardinality_separator", "proof_motif_separator"],
            required_proof_obligations=[
                "Keep prior-grammar replay separate from lower-bound proof.",
                "Use at least two nontrivial checked operator steps before counting a novel G9 delta.",
                "Mark single-operator duplicate rows as not novel G9 deltas.",
            ],
            forbidden_interpretations=[
                "No G9 strictness theorem is claimed.",
                "No lower bound against G0-G8 is claimed.",
                "No orchestration-completeness claim.",
                "No P vs NP progress claim.",
            ],
            next_experiments=["Build finite edge-delta certificates for more mixed operator pairs."],
        ),
        TheoremCandidate(
            id="TC-043",
            name="Obstruction-To-Orchestration Success Candidate",
            statement=(
                "The v2.14 COMPOSED_OPERATOR_ORCHESTRATION recommendation was promoted into "
                "a v2.16 implemented prototype with native certificate-chain evidence."
            ),
            status="EMPIRICAL_EVIDENCE",
            supporting_witnesses=["mixed", "affine_separator", "composed_unsat_cover"],
            required_proof_obligations=[
                "Record the recommendation source from v2.14.",
                "Verify SAT and UNSAT composed certificates.",
                "Reject broken handoffs, diagnostic proof steps, fake DRAT, and bad witness lifts.",
                "Avoid claiming autonomous orchestration is complete.",
            ],
            forbidden_interpretations=[
                "Does not claim a theorem.",
                "Does not claim universal operator chaining.",
                "Does not claim DRAT.",
                "Does not claim P vs NP progress.",
            ],
            next_experiments=["Promote the next obstruction-dual recommendation only after a checker design exists."],
        ),
        TheoremCandidate(
            id="TC-044",
            name="Circuit Projection SAT Lift Soundness Candidate",
            statement=(
                "If every projected auxiliary variable has a verified exact definitional gate and "
                "the lifted assignment evaluates all gates consistently, then direct verification "
                "against the original CNF certifies the SAT witness."
            ),
            status="FORMAL_PROOF_SKETCH",
            supporting_witnesses=["half_adder_sat", "mux2_sat", "mux4_sat"],
            required_proof_obligations=[
                "Verify every gate definition against original CNF clauses.",
                "Reject unsafe auxiliary occurrences that remain after projection.",
                "Evaluate projected gates from the core assignment.",
                "Verify the lifted full assignment against the original CNF.",
            ],
            forbidden_interpretations=[
                "Does not claim a complete circuit-SAT method.",
                "Does not claim arbitrary auxiliary projection.",
                "Does not claim DRAT.",
                "Does not claim P vs NP progress.",
            ],
            next_experiments=["Add more gate families only when exact definition checkers exist."],
        ),
        TheoremCandidate(
            id="TC-045",
            name="Circuit Projection UNSAT Preservation Candidate",
            statement=(
                "For supported exact definitional rows, if every projection step is "
                "equisatisfiability-preserving and the projected core is natively certified UNSAT, "
                "then the original CNF is UNSAT under the native checker."
            ),
            status="FORMAL_PROOF_SKETCH",
            supporting_witnesses=["circuit_unsat_control"],
            required_proof_obligations=[
                "Verify each projected gate definition.",
                "Verify each projection step removes only definitional clauses.",
                "Verify no projected variable remains unsafely in the core.",
                "Verify native core UNSAT evidence.",
            ],
            forbidden_interpretations=[
                "Does not claim DRAT.",
                "Does not claim broad projection completeness.",
                "Does not claim a family theorem.",
                "Does not claim P vs NP progress.",
            ],
            next_experiments=["Replace bounded core UNSAT checks with reusable native core certificates where possible."],
        ),
        TheoremCandidate(
            id="TC-046",
            name="G10 Empirical Edge Delta Candidate",
            statement=(
                "There exist finite circuit/projection rows certified by "
                "G10_CIRCUIT_PROJECTION_LIFT_PROTOTYPE while prior G0-G9 replay does not "
                "produce a certified collapse under the configured profile."
            ),
            status="FINITE_EMPIRICAL_EDGE_DELTA_CERTIFIED",
            supporting_witnesses=["half_adder_sat", "mux2_sat", "projected_affine_core", "projected_capacity_core"],
            required_proof_obligations=[
                "Keep prior-grammar replay separate from lower-bound proof.",
                "Verify exact definitional projection certificates.",
                "Exclude trivial single-gate validation rows from novel G10 delta counts.",
                "Verify orchestration handoffs for projected-core rows.",
            ],
            forbidden_interpretations=[
                "No G10 strictness theorem is claimed.",
                "No lower bound against G0-G9 is claimed.",
                "No complete circuit-SAT method is claimed.",
                "No P vs NP progress claim.",
            ],
            next_experiments=["Build a finite edge certificate for a projected-core-to-G9 orchestration chain."],
        ),
        TheoremCandidate(
            id="TC-047",
            name="Obstruction-To-Circuit-Projection Success Candidate",
            statement=(
                "The v2.14 CIRCUIT_PROJECTION_LIFT recommendation was promoted into a "
                "v2.17 implemented prototype with native circuit-projection certificate evidence."
            ),
            status="EMPIRICAL_EVIDENCE",
            supporting_witnesses=["circuit-sat-toy", "projected_affine_core", "projected_capacity_core"],
            required_proof_obligations=[
                "Record the recommendation source from v2.14.",
                "Verify AND, OR, and NOT exact gate definitions.",
                "Reject incomplete, polluted, unsafe, and bad-lift controls.",
                "Avoid claiming broad circuit solving.",
            ],
            forbidden_interpretations=[
                "Does not claim a theorem.",
                "Does not claim arbitrary projection.",
                "Does not claim DRAT.",
                "Does not claim P vs NP progress.",
            ],
            next_experiments=["Promote projection into larger composed orchestration rows only after handoff certificates verify."],
        ),
        TheoremCandidate(
            id="TC-048",
            name="Proof Motif Generalization Soundness Candidate",
            statement=(
                "If a generalized proof motif template verifies and every reuse instantiation "
                "expands into checked concrete proof steps over original CNF clauses, then the "
                "native generalized macro-proof certificate is sound."
            ),
            status="FORMAL_PROOF_SKETCH",
            supporting_witnesses=["ladder_near_4", "ladder_near_8", "gadget_variants"],
            required_proof_obligations=[
                "Verify every base motif proof expansion.",
                "Verify generalized template parameter constraints.",
                "Verify every concrete reuse instantiation against original clauses.",
                "Reject diagnostic-only similarity as certification.",
            ],
            forbidden_interpretations=[
                "Does not claim DRAT.",
                "Does not claim arbitrary proof-pattern learning.",
                "Does not claim proof motif generalization completeness.",
                "Does not claim P vs NP progress.",
            ],
            next_experiments=["Move the proof sketch into a proof-assistant audit once the template language stabilizes."],
        ),
        TheoremCandidate(
            id="TC-049",
            name="G11 Empirical Edge Delta Candidate",
            statement=(
                "There exist finite near-motif rows certified by "
                "G11_PROOF_MOTIF_GENERALIZATION_CHECKER_PROTOTYPE while G6 exact motif "
                "compression and prior G0-G10 replay do not certify the same rows under the "
                "configured profile."
            ),
            status="FINITE_EMPIRICAL_EDGE_DELTA_CERTIFIED",
            supporting_witnesses=["ladder_near_4", "chain_near_6", "proof_motif_near_miss"],
            required_proof_obligations=[
                "Keep prior-grammar replay separate from lower-bound proof.",
                "Require at least one generalized template covering non-identical motif variants.",
                "Exclude exact G6 motif duplicate rows from novel G11 delta counts.",
                "Reject loose similarity without proof expansion.",
            ],
            forbidden_interpretations=[
                "No G11 strictness theorem is claimed.",
                "No lower bound against G0-G10 is claimed.",
                "No proof motif completeness claim.",
                "No P vs NP progress claim.",
            ],
            next_experiments=["Search for non-synthetic near-motif rows with checked generalized instantiations."],
        ),
        TheoremCandidate(
            id="TC-050",
            name="Obstruction-To-Proof-Motif-Generalization Success Candidate",
            statement=(
                "The v2.14 PROOF_MOTIF_NEAR_MISS recommendation was promoted into a v2.18 "
                "implemented prototype with native generalized macro-proof certificate evidence."
            ),
            status="EMPIRICAL_EVIDENCE",
            supporting_witnesses=["proof_motif_near_miss", "ladder_near_8"],
            required_proof_obligations=[
                "Record the recommendation source from v2.14.",
                "Verify generalized templates and every reuse instantiation.",
                "Reject bad generalizations, loose similarity, fake DRAT, and tampering.",
                "Avoid claiming arbitrary proof-pattern learning.",
            ],
            forbidden_interpretations=[
                "Does not claim a theorem.",
                "Does not claim DRAT.",
                "Does not claim proof motif completeness.",
                "Does not claim P vs NP progress.",
            ],
            next_experiments=["Use obstruction-dual queues to find stronger near-motif generalization targets."],
        ),
        TheoremCandidate(
            id="TC-051",
            name="Collapse Plan Certificate Soundness Candidate",
            statement=(
                "If a collapse plan certificate verifies, then the proposed plan is structurally "
                "valid, claim-boundary safe, and executable only through future certified operator runs."
            ),
            status="FORMAL_PROOF_SKETCH",
            supporting_witnesses=["composed_obstruction_plan", "circuit_projection_plan", "graph_separator_plan"],
            required_proof_obligations=[
                "Verify the source obstruction fingerprint.",
                "Verify every planned operator is in the known portfolio.",
                "Verify certificate types, handoff requirements, and lift obligations.",
                "Reject fake execution, SAT/UNSAT, DRAT, theorem, and completeness claims.",
            ],
            forbidden_interpretations=[
                "Does not claim the plan executed.",
                "Does not claim SAT or UNSAT.",
                "Does not claim DRAT.",
                "Does not claim P vs NP progress.",
            ],
            next_experiments=["Connect verified plans to later executed certificate chains without weakening the claim boundary."],
        ),
        TheoremCandidate(
            id="TC-052",
            name="Obstruction-To-Plan Mapping Candidate",
            statement=(
                "For supported obstruction fingerprints, deterministic planning rules produce compatible "
                "operator sequences or missing-operator hypotheses with declared certificate obligations."
            ),
            status="EMPIRICAL_EVIDENCE",
            supporting_witnesses=["proof_motif_near_plan", "near_affine_missing_operator_plan", "no_confident_fingerprint_plan"],
            required_proof_obligations=[
                "Keep planning separate from execution.",
                "Record missing operator soundness obligations and negative controls.",
                "Verify review/theoremization plans are diagnostic only.",
            ],
            forbidden_interpretations=[
                "Does not claim all fingerprints are covered.",
                "Does not claim a universal planner.",
                "Does not claim lower bounds against G0-G11.",
                "Does not claim P vs NP progress.",
            ],
            next_experiments=["Expand planning rules only when new obstruction certificates justify them."],
        ),
        TheoremCandidate(
            id="TC-053",
            name="Self-Expanding Collapse Hierarchy Candidate",
            statement=(
                "A hierarchy with obstruction fingerprints and verified planner certificates can propose "
                "future collapse paths and missing operators while preserving claim boundaries."
            ),
            status="SPECULATIVE",
            supporting_witnesses=["G7 obstruction-dual queue", "G12 planner certificates"],
            required_proof_obligations=[
                "Define a formal semantics for plan certificates.",
                "Prove that planner verification never implies formula satisfiability or unsatisfiability.",
                "Connect future execution certificates through separately verified operator runs.",
            ],
            forbidden_interpretations=[
                "Does not claim autonomous discovery is complete.",
                "Does not claim a theorem is proven.",
                "Does not claim hierarchy completeness.",
                "Does not claim P vs NP progress.",
            ],
            next_experiments=["Use G12 plans to select the next operator without counting plans as collapses."],
        ),
        TheoremCandidate(
            id="TC-054",
            name="Planner-Guided Execution Soundness Candidate",
            statement=(
                "If a verified plan certificate is paired with a separately verified execution chain whose "
                "operator certificates, formula handoffs, and result obligations verify, then the execution "
                "result is sound for that finite instance."
            ),
            status="FORMAL_PROOF_SKETCH",
            supporting_witnesses=["projected_affine_plan_execution", "proof_motif_plan_execution"],
            required_proof_obligations=[
                "Verify the referenced G12 plan certificate.",
                "Verify every actual operator step certificate with the matching checker.",
                "Verify every formula-state handoff hash.",
                "Verify SAT witnesses against the original CNF and UNSAT preservation chains where claimed.",
                "Reject fake execution, fake SAT/UNSAT, fake DRAT, and diagnostic steps used as results.",
            ],
            forbidden_interpretations=[
                "Does not claim all plans succeed.",
                "Does not claim planner completeness.",
                "Does not claim a theorem is proven.",
                "Does not claim P vs NP progress.",
            ],
            next_experiments=["Broaden planner-guided execution to more independently checked operator chains."],
        ),
        TheoremCandidate(
            id="TC-055",
            name="Plan-Execution Match Candidate",
            statement=(
                "For supported finite fixtures, G12 can propose plans whose expected certificate chain matches "
                "actual certified G13 execution."
            ),
            status="FINITE_PLANNER_EXECUTION_VERIFIED",
            supporting_witnesses=["projected_affine_plan_execution", "proof_motif_plan_execution"],
            required_proof_obligations=[
                "Compute planned-vs-actual comparison from records rather than trusting metadata.",
                "Separate MATCH, PARTIAL_MATCH, MISMATCH, and EXECUTION_FAILED outcomes.",
                "Ensure mismatches do not certify planner success.",
            ],
            forbidden_interpretations=[
                "Does not claim matching examples prove all plans succeed.",
                "Does not claim strictness or lower bounds.",
                "Does not claim hierarchy completeness.",
            ],
            next_experiments=["Add more finite plan-execution fixtures with independently checked handoffs."],
        ),
        TheoremCandidate(
            id="TC-056",
            name="Self-Expanding Loop Candidate",
            statement=(
                "The loop obstruction fingerprint to plan to execution to verified result is demonstrated on "
                "finite controlled instances."
            ),
            status="EMPIRICAL_EVIDENCE",
            supporting_witnesses=["composed_plan_execution", "graph_separator_plan_execution", "mismatch_control"],
            required_proof_obligations=[
                "Keep obstruction, plan, and execution artifacts separate.",
                "Record failed and mismatched executions honestly.",
                "Do not upgrade finite execution evidence into a family theorem.",
            ],
            forbidden_interpretations=[
                "Does not claim universal collapse planning.",
                "Does not claim a polynomial-time SAT algorithm.",
                "Does not claim P vs NP progress.",
            ],
            next_experiments=["Use mismatch records to improve G12 without treating planner improvement as proof."],
        ),
        TheoremCandidate(
            id="TC-057",
            name="G9 Composition Soundness Candidate",
            statement=(
                "If every step in a composed orchestration certificate is verified by its corresponding "
                "operator checker, every formula handoff hash matches, diagnostic-only steps are excluded "
                "from result certification, and the final SAT witness or UNSAT preservation chain verifies "
                "against the original formula, then the composed result is sound for that finite instance."
            ),
            status="FORMAL_PROOF_SKETCH",
            supporting_witnesses=["affine_separator", "composed_sat_lift", "composed_unsat_cover"],
            required_proof_obligations=[
                "Formalize soundness assumptions for every step checker.",
                "Formalize exact formula-state serialization and hash handoff equality.",
                "Prove diagnostic-only steps cannot contribute to SAT/UNSAT certification.",
                "Mechanize SAT witness lift and UNSAT preservation composition.",
            ],
            forbidden_interpretations=[
                "Does not claim a theorem is proven.",
                "Does not claim composition completeness.",
                "Does not claim DRAT.",
                "Does not claim P vs NP progress.",
            ],
            next_experiments=["Move the G9 proof sketch into an external formalization audit."],
        ),
        TheoremCandidate(
            id="TC-058",
            name="G10 Circuit Projection Soundness Candidate",
            statement=(
                "If each projected auxiliary variable has an exact verified definitional gate encoding, "
                "projection steps are equisatisfiability-preserving, unsafe auxiliary uses are rejected, "
                "and the lifted assignment satisfies the original CNF directly, then SAT witness lift is "
                "sound; UNSAT preservation is sound only for supported exact definitional families whose "
                "projection chain verifies."
            ),
            status="FORMAL_PROOF_SKETCH",
            supporting_witnesses=["half_adder_sat", "projected_affine_core", "projected_capacity_core"],
            required_proof_obligations=[
                "Formalize exact AND/OR/NOT definitional encodings.",
                "Formalize safe-use constraints for projected auxiliary variables.",
                "Mechanize equisatisfiability preservation for supported UNSAT projection rows.",
                "Keep arbitrary circuit-SAT solving outside the claim boundary.",
            ],
            forbidden_interpretations=[
                "Does not claim broad circuit-SAT solving.",
                "Does not claim arbitrary auxiliary projection.",
                "Does not claim a theorem is proven.",
                "Does not claim P vs NP progress.",
            ],
            next_experiments=["Audit projection preservation in a proof assistant or external checker."],
        ),
        TheoremCandidate(
            id="TC-059",
            name="G11 Proof Motif Generalization Soundness Candidate",
            statement=(
                "If every generalized proof motif reuse is checked through concrete proof expansion or a "
                "verified parametric instantiation, all substitutions are valid, and the final contradiction "
                "verifies from original clauses, then the generalized macro-proof certificate is sound for "
                "that finite instance."
            ),
            status="FORMAL_PROOF_SKETCH",
            supporting_witnesses=["ladder_near_4", "ladder_near_8", "proof_motif_near_miss"],
            required_proof_obligations=[
                "Formalize the generalized template language.",
                "Formalize substitution safety and parameter constraints.",
                "Mechanize every concrete reuse expansion or parametric instantiation.",
                "Keep near-motif similarity separate from proof.",
            ],
            forbidden_interpretations=[
                "Does not claim arbitrary proof-pattern learning.",
                "Does not claim proof-motif completeness.",
                "Does not claim a theorem is proven.",
                "Does not claim P vs NP progress.",
            ],
            next_experiments=["Externalize generalized macro-proof checking to a proof-format bridge."],
        ),
        TheoremCandidate(
            id="TC-060",
            name="G12 Plan-Only Soundness Candidate",
            statement=(
                "If a collapse plan certificate verifies, then the plan is structurally valid, "
                "operator-compatible, claim-boundary safe, and execution-required; it does not certify SAT, "
                "UNSAT, DRAT, theorem status, or completeness."
            ),
            status="FORMAL_PROOF_SKETCH",
            supporting_witnesses=["composed_obstruction_plan", "circuit_projection_plan", "no_confident_fingerprint_plan"],
            required_proof_obligations=[
                "Formalize plan-only semantics.",
                "Prove verified plans cannot imply SAT or UNSAT.",
                "Keep missing-operator hypotheses separate from executed certificates.",
                "Reject unknown operators and missing handoff obligations.",
            ],
            forbidden_interpretations=[
                "Does not claim execution happened.",
                "Does not claim SAT or UNSAT.",
                "Does not claim a theorem is proven.",
                "Does not claim P vs NP progress.",
            ],
            next_experiments=["Connect plans to separately verified executions without relaxing plan-only semantics."],
        ),
        TheoremCandidate(
            id="TC-061",
            name="G13 Planner-Guided Execution Soundness Candidate",
            statement=(
                "If a verified G12 plan is paired with a separately verified G13 execution certificate, "
                "every actual operator certificate verifies, every formula handoff verifies, planned-vs-actual "
                "comparison is recomputed, and the final SAT witness or UNSAT preservation trace verifies, "
                "then the finite execution result is sound for that instance."
            ),
            status="FORMAL_PROOF_SKETCH",
            supporting_witnesses=["projected_affine_plan_execution", "proof_motif_plan_execution"],
            required_proof_obligations=[
                "Formalize separation between plan and execution certificates.",
                "Formalize planned-vs-actual comparison.",
                "Mechanize every allowed actual step checker.",
                "Reject mismatch as planner success and reject copied-plan execution records.",
            ],
            forbidden_interpretations=[
                "Does not claim all plans succeed.",
                "Does not claim planner completeness.",
                "Does not claim a theorem is proven.",
                "Does not claim P vs NP progress.",
            ],
            next_experiments=["Broaden finite plan-execution fixtures after checker assumptions are formalized."],
        ),
        TheoremCandidate(
            id="TC-062",
            name="Closed-Loop Finite Soundness Candidate",
            statement=(
                "For finite controlled instances where obstruction fingerprinting, planning, execution, "
                "certificate verification, and result verification all pass, Witnora demonstrates a sound "
                "finite closed-loop collapse experiment."
            ),
            status="EMPIRICAL_EVIDENCE",
            supporting_witnesses=["G7 obstruction records", "G12 plans", "G13 executions"],
            required_proof_obligations=[
                "Formalize obstruction-record semantics.",
                "Formalize plan-to-execution linkage.",
                "Prove the finite-vs-family claim boundary.",
                "Keep native certificates separate from external proof formats.",
            ],
            forbidden_interpretations=[
                "Does not claim a family theorem.",
                "Does not claim hierarchy completeness.",
                "Does not claim a theorem is proven.",
                "Does not claim P vs NP progress.",
            ],
            next_experiments=["Attack the first infinite-family theorem gate after external review of the finite backbone."],
        ),
        TheoremCandidate(
            id="TC-063",
            name="Bounded Separator-Affine Collapse Theorem",
            statement=(
                "For the restricted family SAF(c,r), where c and r are fixed constants, a CNF with a "
                "separator S of size at most c whose separator-conditioned residual components are exact "
                "GF(2) affine CNFs accepted by G5 can be recognized, collapsed, and checked by enumerating "
                "all separator assignments and solving each residual affine component. SAT requires one "
                "separator assignment where every component is SAT; UNSAT requires every separator "
                "assignment to be covered by at least one affine-UNSAT component."
            ),
            status="RESTRICTED_THEOREM_WITH_PROOF_OBLIGATIONS",
            supporting_witnesses=[
                "saf_sat_chain_n",
                "saf_unsat_cover_n",
                "saf_mixed_components_n",
            ],
            required_proof_obligations=[
                "State SAF(c,r) exactly and keep the theorem restricted to that family.",
                "Prove separator enumeration is polynomial only for fixed c.",
                "Verify every residual component is exact affine under G5, not affine plus leftovers.",
                "For SAT, verify the combined separator/component assignment against the original CNF.",
                "For UNSAT, verify a complete separator-assignment cover with affine UNSAT certificates.",
                "Keep native separator-affine certificates separate from external DRAT proof claims.",
            ],
            forbidden_interpretations=[
                "Does not claim P vs NP progress.",
                "Does not claim all SAT or arbitrary separator formulas.",
                "Does not claim hierarchy completeness.",
                "Does not claim DRAT unless an external proof is checked.",
                "Does not claim polynomial-time SAT for arbitrary formulas.",
            ],
            next_experiments=[
                "Mechanize the SAF(c,r) proof in an external proof assistant.",
                "Investigate the next restricted infinite-family theorem beyond exact affine residuals.",
            ],
            lemma_count=8,
            proof_obligation_count=32,
            dependency_on_g5_affine_soundness=True,
            fixed_c_polynomiality=True,
            native_certificate_only=True,
            external_proof_bridge_absent=True,
            finite_tests_are_support_only=True,
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
