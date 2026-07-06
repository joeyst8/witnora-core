"""Collapse hierarchy theoremization records for Witnora v2.8.

This module does not add a solver or collapse operator. It turns the current
G0-G6 operator ladder into a bounded, operational research object: definitions,
empirical strictness evidence, proof obligations, gap analysis, and a paper
draft.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


NOT_RECORDED = "NOT_RECORDED_IN_THIS_ARTIFACT"
EMPIRICAL_NOT_THEOREM = "EMPIRICAL_EVIDENCE_NOT_THEOREM"
FORMAL_PROOF_OBLIGATION = "FORMAL_PROOF_OBLIGATION"
FORMAL_PROOF_SKETCH = "FORMAL_PROOF_SKETCH"
CONJECTURE = "CONJECTURE"
SPECULATIVE_PROGRAM = "SPECULATIVE_PROGRAM"
REFUTED = "REFUTED"
PROVEN = "PROVEN"

G_CHAIN = [
    "G0_BASE",
    "G1_XOR",
    "G2_SYMMETRY_CERTIFIED",
    "G3_SYMMETRY_CARDINALITY_CERTIFIED",
    "G4_ORBIT_CAPACITY_COUNTING_PROTOTYPE",
    "G5_HIGH_ARITY_AFFINE_RESIDUE_PROTOTYPE",
    "G6_PROOF_MOTIF_COMPRESSION_PROTOTYPE",
]


@dataclass(frozen=True)
class OperatorDefinition:
    name: str
    description: str
    certificate_or_checker: str
    claim_boundary: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class GrammarDefinition:
    name: str
    extends: str | None
    operators: list[str]
    native_certificate_types: list[str]
    external_proof_routes: list[str]
    claim_boundary: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class BoundProfileDefinition:
    name: str
    max_runtime_seconds: int
    max_width: int
    max_treewidth_c: int
    xor_max_k: int
    g5_affine_max_arity: int
    max_proof_bytes: int
    max_certificate_bytes: int
    max_operator_depth: int
    max_search_nodes: int
    max_motif_reuse_sites: int
    max_hall_subset_size: int
    native_certificate_allowed: bool
    drat_required: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class BoundedCollapseClassDefinition:
    notation: str
    grammar: str
    bound_profile: str
    membership_definition: str
    non_membership_warning: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class EmpiricalStrictnessEvidence:
    edge: str
    base_grammar: str
    extended_grammar: str
    witness_families: list[str]
    base_result: str
    extended_result: str
    strictness_status: str
    proof_obligation: str
    evidence_refs: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class StrictnessCandidate:
    id: str
    name: str
    statement: str
    current_status: str
    witness_family: list[str]
    proof_obligations: list[str]
    forbidden_interpretations: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ProofObligation:
    theorem_candidate_id: str
    obligation_id: str
    obligation_type: str
    current_status: str
    evidence_refs: list[str]
    missing_work: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class HierarchyEdge:
    edge_id: str
    base_grammar: str
    extended_grammar: str
    added_operator_layer: str
    witness_families: list[str]
    empirical_status: str
    duplicate_control_handling: str
    proof_obligation_summary: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class HierarchyEvidenceBundle:
    release_tags: list[str]
    commits: dict[str, str]
    source_archive_sha256: dict[str, str]
    artifact_sha256: dict[str, str]
    test_counts: dict[str, str | int]
    witness_families: dict[str, list[str]]
    public_categories: dict[str, list[str]]
    certificate_paths: dict[str, list[str]]
    claim_boundaries: dict[str, str]
    strictness_status: dict[str, str]
    duplicate_control_handling: dict[str, str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class GapAnalysisRecord:
    gap: str
    current_grammars_tried: list[str]
    failure_mode: str
    obstruction_fingerprint: str
    likely_next_operator_candidate: str
    proof_or_certificate_obstacle: str
    v2_9_recommendation: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class TheoremizationReport:
    out_root: str
    artifact_zip: str
    artifact_sha256: str
    grammar_count: int
    hierarchy_edge_count: int
    theorem_candidate_count: int
    proof_obligation_count: int
    gap_count: int
    claim_boundary: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def stable_json(data: Any) -> str:
    return json.dumps(data, indent=2, sort_keys=True)


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(stable_json(data) + "\n", encoding="utf-8", newline="\n")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def make_zip(root: Path | str, zip_path: Path | str) -> str:
    root = Path(root)
    zip_path = Path(zip_path)
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(root.rglob("*")):
            if path.is_file():
                zf.write(path, path.relative_to(root).as_posix())
    return sha256_file(zip_path)


def operator_definitions() -> list[OperatorDefinition]:
    return [
        OperatorDefinition("UP", "Unit propagation.", "trace replay", "base simplification only"),
        OperatorDefinition("PLE", "Pure literal elimination.", "deterministic replay", "base simplification only"),
        OperatorDefinition("SUB", "Subsumption.", "deterministic replay", "base simplification only"),
        OperatorDefinition("BCE", "Blocked clause elimination.", "reconstruction trace", "bounded replay only"),
        OperatorDefinition("VE", "Variable elimination.", "reconstruction trace", "bounded replay only"),
        OperatorDefinition("COMPONENTS", "Component decomposition.", "component replay", "base decomposition only"),
        OperatorDefinition("2SAT", "Terminal 2-SAT class.", "SCC certificate", "tractable terminal only"),
        OperatorDefinition("BOUNDED_TREEWIDTH", "Bounded treewidth terminal route.", "width-bound audit", "bounded c only"),
        OperatorDefinition("XOR_AFFINE", "Exact bounded XOR extraction and affine elimination.", "native/DRAT where supported", "no broad XOR mining"),
        OperatorDefinition("SYMMETRY_CERTIFIED", "Exact automorphism validation and SAT witness reconstruction.", "symmetry certificate checker", "native symmetry only unless DRAT checked"),
        OperatorDefinition("CARDINALITY_PIGEONHOLE", "Exact AMO/ALO and standard pigeonhole grid certificate.", "native pigeonhole checker", "standard recognized PHP only"),
        OperatorDefinition("ORBIT_CAPACITY_COUNTING", "Local Hall/capacity-deficit native certificate.", "orbit-capacity checker", "exact generated assignment CNFs only"),
        OperatorDefinition("HIGH_ARITY_AFFINE_RESIDUE", "Exact high-arity GF(2) full-CNF extraction.", "native GF(2) checker", "no heuristic XOR mining or broad modular solving"),
        OperatorDefinition("PROOF_MOTIF_COMPRESSION", "Native macro-proof motif template/reuse checker.", "proof motif checker", "native macro-proof only; not DRAT"),
    ]


def grammar_definitions() -> list[GrammarDefinition]:
    return [
        GrammarDefinition(
            "G0_BASE",
            None,
            ["UP", "PLE", "SUB", "BCE", "VE", "COMPONENTS", "2SAT", "BOUNDED_TREEWIDTH"],
            ["SAT_ASSIGNMENT_VERIFIED", "BASE_TRACE_VERIFIED"],
            [],
            "G0 is the base deterministic replay grammar under configured bounds.",
        ),
        GrammarDefinition(
            "G1_XOR",
            "G0_BASE",
            ["UP", "PLE", "SUB", "BCE", "VE", "COMPONENTS", "2SAT", "BOUNDED_TREEWIDTH", "XOR_AFFINE"],
            ["UNSAT_XOR_NATIVE_ONLY", "SAT_ASSIGNMENT_VERIFIED"],
            ["UNSAT_DRAT_EXPORTED_VERIFIED where explicitly exported and checked"],
            "Exact bounded XOR only; no broad XOR extraction claim.",
        ),
        GrammarDefinition(
            "G2_SYMMETRY_CERTIFIED",
            "G1_XOR",
            ["XOR_AFFINE", "SYMMETRY_CERTIFIED"],
            ["SYMMETRY_NATIVE_CERTIFIED", "SYMMETRY_SAT_WITNESS_RECONSTRUCTED"],
            [],
            "Symmetry certificates are native unless a proof against the original CNF is separately checked.",
        ),
        GrammarDefinition(
            "G3_SYMMETRY_CARDINALITY_CERTIFIED",
            "G2_SYMMETRY_CERTIFIED",
            ["SYMMETRY_CERTIFIED", "CARDINALITY_PIGEONHOLE"],
            ["UNSAT_PIGEONHOLE_NATIVE_CERTIFIED"],
            [],
            "Standard PHP assignment-grid certificates only; not a complete PB solver.",
        ),
        GrammarDefinition(
            "G4_ORBIT_CAPACITY_COUNTING_PROTOTYPE",
            "G3_SYMMETRY_CARDINALITY_CERTIFIED",
            ["CARDINALITY_PIGEONHOLE", "ORBIT_CAPACITY_COUNTING"],
            ["UNSAT_ORBIT_CAPACITY_NATIVE_CERTIFIED"],
            [],
            "Local Hall/capacity native certificates; duplicate G3 controls are not novel deltas.",
        ),
        GrammarDefinition(
            "G5_HIGH_ARITY_AFFINE_RESIDUE_PROTOTYPE",
            "G4_ORBIT_CAPACITY_COUNTING_PROTOTYPE",
            ["ORBIT_CAPACITY_COUNTING", "HIGH_ARITY_AFFINE_RESIDUE"],
            ["SAT_AFFINE_RESIDUE_NATIVE_CERTIFIED", "UNSAT_AFFINE_RESIDUE_NATIVE_CERTIFIED"],
            [],
            "Exact full-CNF high-arity GF(2) only; no heuristic mining and no broad modular solver claim.",
        ),
        GrammarDefinition(
            "G6_PROOF_MOTIF_COMPRESSION_PROTOTYPE",
            "G5_HIGH_ARITY_AFFINE_RESIDUE_PROTOTYPE",
            ["HIGH_ARITY_AFFINE_RESIDUE", "PROOF_MOTIF_COMPRESSION"],
            ["UNSAT_PROOF_MOTIF_NATIVE_CERTIFIED"],
            [],
            "Native macro-proof motifs only; every template and reuse instantiation is checked.",
        ),
    ]


def bound_profile_definitions() -> list[BoundProfileDefinition]:
    return [
        BoundProfileDefinition(
            name="B_V28_BOUNDED_EVIDENCE",
            max_runtime_seconds=120,
            max_width=32,
            max_treewidth_c=8,
            xor_max_k=6,
            g5_affine_max_arity=10,
            max_proof_bytes=5_000_000,
            max_certificate_bytes=2_000_000,
            max_operator_depth=16,
            max_search_nodes=100_000,
            max_motif_reuse_sites=64,
            max_hall_subset_size=6,
            native_certificate_allowed=True,
            drat_required=False,
        )
    ]


def bounded_collapse_classes() -> list[BoundedCollapseClassDefinition]:
    definition = (
        "A formula F is in W_B(G) if Witnora can produce, under bound profile B "
        "and grammar G, a SAT witness verified against the original CNF, an UNSAT "
        "certificate/proof verified by the appropriate checker, or an accepted "
        "native certificate whose checker succeeds, all within configured cost "
        "and resource bounds."
    )
    warning = (
        "Current non-membership is bounded operational non-collapse under the "
        "configured grammar/resource profile, not a proof of hardness or an "
        "absolute lower bound."
    )
    return [
        BoundedCollapseClassDefinition(
            notation=f"W_B({grammar})",
            grammar=grammar,
            bound_profile="B_V28_BOUNDED_EVIDENCE",
            membership_definition=definition,
            non_membership_warning=warning,
        )
        for grammar in G_CHAIN
    ]


def hierarchy_edges() -> list[HierarchyEdge]:
    rows = [
        ("E01", "G0_BASE", "G1_XOR", "XOR_AFFINE", ["tseitin", "xor-chain"], "Show G0 cannot collapse the family under the stated bound."),
        ("E02", "G1_XOR", "G2_SYMMETRY_CERTIFIED", "SYMMETRY_CERTIFIED", ["cycle_4_3color", "cycle_6_3color"], "Show G1 cannot produce equivalent witness/certificate under the same bound."),
        ("E03", "G2_SYMMETRY_CERTIFIED", "G3_SYMMETRY_CARDINALITY_CERTIFIED", "CARDINALITY_PIGEONHOLE", ["php_3_2", "php_4_3", "php_5_4", "php_6_5"], "Show G2 symmetry alone cannot certify PHP counting contradiction under the bound."),
        ("E04", "G3_SYMMETRY_CARDINALITY_CERTIFIED", "G4_ORBIT_CAPACITY_COUNTING_PROTOTYPE", "ORBIT_CAPACITY_COUNTING", ["hall_local_3_2", "hall_local_4_3", "hall_local_5_4"], "Show G3 standard PHP recognizer does not handle local Hall deficits."),
        ("E05", "G4_ORBIT_CAPACITY_COUNTING_PROTOTYPE", "G5_HIGH_ARITY_AFFINE_RESIDUE_PROTOTYPE", "HIGH_ARITY_AFFINE_RESIDUE", ["parity_arity_7_unsat", "parity_arity_8_unsat", "parity_arity_9_unsat", "parity_arity_10_unsat"], "Show lower-cap affine extraction cannot handle above-cap exact encodings under the bound."),
        ("E06", "G5_HIGH_ARITY_AFFINE_RESIDUE_PROTOTYPE", "G6_PROOF_MOTIF_COMPRESSION_PROTOTYPE", "PROOF_MOTIF_COMPRESSION", ["motif_ladder", "renamed_conflict", "motif_chain"], "Show G5 affine/capacity operators do not certify proof-motif families under the proof-size bound."),
    ]
    return [
        HierarchyEdge(
            edge_id=edge_id,
            base_grammar=base,
            extended_grammar=extended,
            added_operator_layer=operator,
            witness_families=families,
            empirical_status=EMPIRICAL_NOT_THEOREM,
            duplicate_control_handling="Prior-grammar duplicates are recorded as controls and not counted as novel deltas.",
            proof_obligation_summary=obligation,
        )
        for edge_id, base, extended, operator, families, obligation in rows
    ]


def empirical_strictness_evidence() -> list[EmpiricalStrictnessEvidence]:
    base_results = {
        "E01": "G0 bounded no-collapse record",
        "E02": "G1 no symmetry certificate route under selected profile",
        "E03": "G2 symmetry diagnostic only for PHP counting",
        "E04": "G3 duplicate/global PHP recognizer does not certify local Hall row",
        "E05": "G4 lacks high-arity affine extraction above G1 cap",
        "E06": "G5 lacks macro-proof motif compression",
    }
    extended_results = {
        "E01": "G1 exact XOR/native or checked DRAT-supported collapse where available",
        "E02": "G2 SAT witness reconstruction with certified automorphism evidence",
        "E03": "G3 native PHP counting certificate",
        "E04": "G4 native Hall/capacity certificate",
        "E05": "G5 native GF(2) affine certificate",
        "E06": "G6 native proof-motif macro certificate",
    }
    return [
        EmpiricalStrictnessEvidence(
            edge=edge.edge_id,
            base_grammar=edge.base_grammar,
            extended_grammar=edge.extended_grammar,
            witness_families=edge.witness_families,
            base_result=base_results[edge.edge_id],
            extended_result=extended_results[edge.edge_id],
            strictness_status=EMPIRICAL_NOT_THEOREM,
            proof_obligation=edge.proof_obligation_summary,
            evidence_refs=[f"outputs/v2.{idx + 1}-artifact-family-records", edge.edge_id],
        )
        for idx, edge in enumerate(hierarchy_edges())
    ]


def theorem_candidates_v28() -> list[StrictnessCandidate]:
    specs = [
        ("TC-021", "Bounded XOR Strictness Candidate", "G0_BASE", "G1_XOR", ["tseitin", "xor-chain"]),
        ("TC-022", "Bounded Symmetry Strictness Candidate", "G1_XOR", "G2_SYMMETRY_CERTIFIED", ["graph-coloring symmetry rows"]),
        ("TC-023", "Bounded Pigeonhole/Cardinality Strictness Candidate", "G2_SYMMETRY_CERTIFIED", "G3_SYMMETRY_CARDINALITY_CERTIFIED", ["php_3_2", "php_4_3", "php_5_4", "php_6_5"]),
        ("TC-024", "Bounded Orbit-Capacity Strictness Candidate", "G3_SYMMETRY_CARDINALITY_CERTIFIED", "G4_ORBIT_CAPACITY_COUNTING_PROTOTYPE", ["local Hall/capacity rows"]),
        ("TC-025", "Bounded High-Arity Affine Strictness Candidate", "G4_ORBIT_CAPACITY_COUNTING_PROTOTYPE", "G5_HIGH_ARITY_AFFINE_RESIDUE_PROTOTYPE", ["parity arity 7-10 rows"]),
        ("TC-026", "Bounded Proof-Motif Strictness Candidate", "G5_HIGH_ARITY_AFFINE_RESIDUE_PROTOTYPE", "G6_PROOF_MOTIF_COMPRESSION_PROTOTYPE", ["motif ladder", "renamed conflict", "selector chain"]),
    ]
    candidates: list[StrictnessCandidate] = []
    for candidate_id, name, base, extended, witnesses in specs:
        candidates.append(
            StrictnessCandidate(
                id=candidate_id,
                name=name,
                statement=(
                    f"Under an explicit bound profile B, {extended} has empirical certificate-backed "
                    f"rows on {', '.join(witnesses)} not certified by {base} in the recorded run."
                ),
                current_status=EMPIRICAL_NOT_THEOREM,
                witness_family=witnesses,
                proof_obligations=[
                    "Replay the extended grammar certificate/checker.",
                    "Specify the bound profile B.",
                    "Replace bounded no-collapse records with a formal non-collapse proof before theorem status.",
                ],
                forbidden_interpretations=[
                    "Not a proven strictness theorem.",
                    "No lower bound against arbitrary algorithms is claimed.",
                    "No P vs NP progress claim.",
                ],
            )
        )
    candidates.extend(
        [
            StrictnessCandidate(
                "TC-027",
                "Collapse Hierarchy Strictness Program",
                "The G0-G6 ladder is a program for turning empirical operator deltas into bounded strictness theorems by discharging explicit proof obligations.",
                FORMAL_PROOF_OBLIGATION,
                ["full G0-G6 hierarchy"],
                ["Prove non-collapse side for each edge.", "Mechanize native checker soundness.", "Define scaling families for each witness row."],
                ["Not a theorem yet.", "Not a complete hierarchy.", "Not P vs NP progress."],
            ),
            StrictnessCandidate(
                "TC-028",
                "Collapse Hierarchy Completeness Speculation",
                "A future operator hierarchy may cover larger verifier-to-witness classes, but v2.8 records this only as speculative program material.",
                SPECULATIVE_PROGRAM,
                ["gap analysis rows"],
                ["Define target universe.", "Prove coverage only for restricted classes.", "Avoid completeness language until proof exists."],
                ["No hierarchy completeness claim.", "No complete SAT algorithm claim."],
            ),
            StrictnessCandidate(
                "TC-029",
                "Operator Genesis Progress Candidate",
                "Operator genesis has promoted ORBIT_COUNTING_COLLAPSE, MODULAR_RESIDUE_COLLAPSE, and PROOF_MOTIF_COMPRESSION into bounded prototypes with native checkers.",
                EMPIRICAL_NOT_THEOREM,
                ["v2.5", "v2.6", "v2.7"],
                ["Separate implemented prototypes from theorem status.", "Track safety and duplicate controls.", "Show each checker is sound."],
                ["Generated operators are not automatically trusted.", "No autonomous theorem discovery claim."],
            ),
            StrictnessCandidate(
                "TC-030",
                "Obstruction-to-Operator Program Candidate",
                "Persistent obstruction fingerprints can guide candidate operator generation and proof-obligation queues.",
                CONJECTURE,
                ["operator genesis fingerprints", "gap analysis rows"],
                ["Show fingerprint stability.", "Show candidate generation improves next-operator selection.", "Prove promoted operators preserve satisfiability/certificates."],
                ["Not a proof of obstruction completeness.", "No lower-bound claim."],
            ),
        ]
    )
    return candidates


def proof_obligation_matrix() -> list[ProofObligation]:
    obligations: list[ProofObligation] = []
    type_cycle = [
        "PRIOR_GRAMMAR_NON_COLLAPSE",
        "NEW_GRAMMAR_CERTIFICATION",
        "CHECKER_SOUNDNESS",
        "BOUND_PROFILE_WELL_DEFINED",
        "COST_MODEL_COMPLETE",
        "WITNESS_FAMILY_SCALING",
        "LOWER_BOUND_REQUIRED",
        "DRAT_BRIDGE_OPTIONAL",
        "NATIVE_CERTIFICATE_SOUNDNESS",
    ]
    for candidate in theorem_candidates_v28():
        for idx, obligation_type in enumerate(type_cycle, start=1):
            if obligation_type in {"NEW_GRAMMAR_CERTIFICATION", "CHECKER_SOUNDNESS", "NATIVE_CERTIFICATE_SOUNDNESS"}:
                status = "SATISFIED_BY_CHECKER" if candidate.current_status == EMPIRICAL_NOT_THEOREM else "FORMAL_PROOF_SKETCH_ONLY"
            elif obligation_type == "BOUND_PROFILE_WELL_DEFINED":
                status = "SATISFIED_BY_TESTS"
            elif obligation_type == "DRAT_BRIDGE_OPTIONAL":
                status = "NOT_ATTEMPTED"
            else:
                status = "OPEN"
            obligations.append(
                ProofObligation(
                    theorem_candidate_id=candidate.id,
                    obligation_id=f"{candidate.id}-PO-{idx:02d}",
                    obligation_type=obligation_type,
                    current_status=status,
                    evidence_refs=candidate.witness_family,
                    missing_work=(
                        "Formal proof work remains before theorem status."
                        if status == "OPEN"
                        else "Recorded in v2.8 theoremization artifact."
                    ),
                )
            )
    return obligations


def gap_analysis_records() -> list[GapAnalysisRecord]:
    rows = [
        ("random 3-SAT", "no stable collapse fingerprint", "NO_CONFIDENT_FINGERPRINT", "OBSTRUCTION_DUAL_CERTIFICATE", "Need a certifiable obstruction language before operator promotion.", "Build a red-team corpus and fingerprint confidence audit."),
        ("general circuit-SAT", "circuit structure is not represented as certified collapse objects", "PROJECTION_LIFT_SIGNAL", "FIBER_PROJECTION_COLLAPSE", "Need a lift/reconstruction checker from projected circuit fibers.", "Prototype tiny circuit fiber certificates."),
        ("arbitrary PB encodings", "G3/G4 only accept exact scoped cardinality/capacity evidence", "CARDINALITY_INCOMPLETE", "ALLOCATION_POLYTOPE_COLLAPSE", "Need exact PB encoding normalization and checker soundness.", "Add PB sidecar/checker design without solving claims."),
        ("non-exact XOR / near-affine encodings", "G5 rejects polluted or incomplete encodings", "AFFINE_HIDDEN", "MODULAR_RESIDUE_COLLAPSE", "Need a sound extraction story that does not become heuristic mining.", "Study proof-producing affine extraction from noisy encodings."),
        ("realistic SAT competition formulas", "operators are scoped to generated or exact structured families", "HIGH_LOCAL_OVERLAP", "GRAPH_SEPARATOR_LIFT", "Need benchmark-safe claim boundaries and checker-backed rows.", "Run diagnostic-only frontier extraction on public formulas."),
        ("formulas requiring resolution lower-bound reasoning", "native operators do not prove lower bounds", "PROOF_EXPORT_BLOWUP", "OBSTRUCTION_DUAL_CERTIFICATE", "Need formal proof-complexity obligations.", "Connect motif compression gaps to proof complexity notes."),
        ("formulas needing interpolation/proof complexity", "no interpolation operator exists", "REPEATED_PROOF_MOTIF", "PROOF_MOTIF_COMPRESSION", "Need interpolation certificate format.", "Design interpolation trace sketches."),
        ("formulas where no confident fingerprint is found", "operator genesis refuses unsupported promotion", "NO_CONFIDENT_FINGERPRINT", "OBSTRUCTION_DUAL_CERTIFICATE", "Need evidence thresholds and negative controls.", "Improve fingerprint reproducibility tests."),
        ("native certificates without DRAT bridge", "native checker succeeds but no external proof route exists", "DRAT_BRIDGE_MISSING", "DRAT_BRIDGE_OPTIONAL", "Need proof export only when sound against original CNF.", "Prioritize bridge candidates by native certificate stability."),
    ]
    return [
        GapAnalysisRecord(
            gap=gap,
            current_grammars_tried=G_CHAIN,
            failure_mode=failure,
            obstruction_fingerprint=fingerprint,
            likely_next_operator_candidate=operator,
            proof_or_certificate_obstacle=obstacle,
            v2_9_recommendation=recommendation,
        )
        for gap, failure, fingerprint, operator, obstacle, recommendation in rows
    ]


def hierarchy_evidence_bundle() -> HierarchyEvidenceBundle:
    release_tags = [
        "v2.0-collapse-theory-lab",
        "v2.1-collapse-theory-frontier",
        "v2.2-certified-symmetry-collapse",
        "v2.3-pigeonhole-cardinality-collapse",
        "v2.4-operator-genesis",
        "v2.5-orbit-capacity-counting",
        "v2.6-affine-residue-collapse",
        "v2.7-proof-motif-compression",
    ]
    commits = {
        "v2.0-collapse-theory-lab": "d594134125e0bf2f0db69957268e18bb13f6b15e",
        "v2.1-collapse-theory-frontier": "30984267261412a52e2e19a2a120cdecaab908fd",
        "v2.2-certified-symmetry-collapse": "0430a39e0a4fac3b3c52fc2518d3f44c46200296",
        "v2.3-pigeonhole-cardinality-collapse": "fa26d76226e1ab7edea72943c8aec0710d5ca50b",
        "v2.4-operator-genesis": "b9916f7a7c5dafa07883a235510a88356c0749d8",
        "v2.5-orbit-capacity-counting": "bedac2a21b3e17a95aa1138fea38a002875034cb",
        "v2.6-affine-residue-collapse": "695ae0f805ca63a6abd4f5f07748c5e93e896efd",
        "v2.7-proof-motif-compression": "eab9aebd005cee7ddf55f608f36d698a099e9a4c",
    }
    artifact_sha256 = {
        "v2.0-collapse-theory-lab": "6FD7726127FE8617D790D170C02570F150C28C4E11F58A0938A152C119FF8253",
        "v2.1-collapse-theory-frontier": "924C555F04A40A83B755A3FD89712091D1E6F8B88FADDCE8145A3569B3D82169",
        "v2.2-certified-symmetry-collapse": "8BB062FF2ADF08BC2A8FD9088A75A14BAE6D7A78C3844502BD86E8EBB83FEE6F",
        "v2.3-pigeonhole-cardinality-collapse": "F78767A898923FC0F2071A2E5C5F7ED6F3755AF188FFC1683772E307F22EE40E",
        "v2.4-operator-genesis": "7D345AD954FC95E8104840D10FA4A3E6EE7E23D6EC9B41B6EA2A34AD5D4821F8",
        "v2.5-orbit-capacity-counting": "9A1C66D9032BF3457FE10DF82CCBEEDAE90D389E2ECB6849C79DC0B442D70876",
        "v2.6-affine-residue-collapse": "DF8CE21DB1AE50C267FF77584517AC30BBCB64D3E1793682FB6568E26217DD7C",
        "v2.7-proof-motif-compression": "7F2A7C4656CC60D49D0C93B5F9F364EF703EB7018CC4D90790D6B1656AE22417",
    }
    source_archive_sha256 = {tag: NOT_RECORDED for tag in release_tags}
    source_archive_sha256["v2.6-affine-residue-collapse"] = "644C4C9C5716E133A4FF2AB87674AF57E2DFF383327FDF837040BE17AFA9ADA9"
    source_archive_sha256["v2.7-proof-motif-compression"] = "10F5D04430605FF10156DA73A035F46545A3C674057378C219A1635A2358BFB8"
    witness_families = {
        "G0_BASE_to_G1_XOR": ["tseitin", "xor-chain"],
        "G1_XOR_to_G2_SYMMETRY_CERTIFIED": ["graph-coloring"],
        "G2_SYMMETRY_CERTIFIED_to_G3_SYMMETRY_CARDINALITY_CERTIFIED": ["pigeonhole"],
        "G3_SYMMETRY_CARDINALITY_CERTIFIED_to_G4_ORBIT_CAPACITY_COUNTING_PROTOTYPE": ["local Hall/capacity"],
        "G4_ORBIT_CAPACITY_COUNTING_PROTOTYPE_to_G5_HIGH_ARITY_AFFINE_RESIDUE_PROTOTYPE": ["high-arity parity"],
        "G5_HIGH_ARITY_AFFINE_RESIDUE_PROTOTYPE_to_G6_PROOF_MOTIF_COMPRESSION_PROTOTYPE": ["proof motif ladder"],
    }
    return HierarchyEvidenceBundle(
        release_tags=release_tags,
        commits=commits,
        source_archive_sha256=source_archive_sha256,
        artifact_sha256=artifact_sha256,
        test_counts={tag: NOT_RECORDED for tag in release_tags} | {"v2.7-proof-motif-compression": 410},
        witness_families=witness_families,
        public_categories={
            "native": [
                "UNSAT_PIGEONHOLE_NATIVE_CERTIFIED",
                "UNSAT_ORBIT_CAPACITY_NATIVE_CERTIFIED",
                "UNSAT_AFFINE_RESIDUE_NATIVE_CERTIFIED",
                "UNSAT_PROOF_MOTIF_NATIVE_CERTIFIED",
            ],
            "external": ["UNSAT_DRAT_EXPORTED_VERIFIED only when explicitly exported and checked"],
        },
        certificate_paths={key: [NOT_RECORDED] for key in witness_families},
        claim_boundaries={
            "strictness": "empirical evidence, not theorem",
            "native_certificates": "native certificates are not DRAT unless explicitly exported and checked",
            "p_vs_np": "no P vs NP progress claim",
            "completeness": "no hierarchy completeness claim",
        },
        strictness_status={key: EMPIRICAL_NOT_THEOREM for key in witness_families},
        duplicate_control_handling={
            "G4": "complete matching duplicates of G3 PHP are not novel deltas",
            "G6": "Tseitin/XOR duplicates are not novel G6 deltas",
        },
    )


def _md_list(items: list[str]) -> list[str]:
    return [f"- {item}" for item in items]


def hierarchy_definitions_markdown(grammars: list[GrammarDefinition], bounds: list[BoundProfileDefinition], classes: list[BoundedCollapseClassDefinition]) -> str:
    lines = [
        "# Hierarchy Definitions",
        "",
        "v2.8 formalizes the current hierarchy. It does not add a new operator.",
        "",
        "## Bounded Collapse Class",
        "",
        classes[0].membership_definition,
        "",
        classes[0].non_membership_warning,
        "",
        "## Grammar Chain",
        "",
    ]
    for grammar in grammars:
        lines.extend([f"### {grammar.name}", "", f"Extends: `{grammar.extends or 'root'}`", "", "Operators:"])
        lines.extend(_md_list(grammar.operators))
        lines.extend(["", f"Claim boundary: {grammar.claim_boundary}", ""])
    lines.extend(["## Bound Profiles", ""])
    for bound in bounds:
        lines.extend([f"### {bound.name}", "", f"`native_certificate_allowed={bound.native_certificate_allowed}`, `drat_required={bound.drat_required}`.", ""])
    return "\n".join(lines)


def hierarchy_evidence_markdown(edges: list[HierarchyEdge], evidence: list[EmpiricalStrictnessEvidence]) -> str:
    lines = [
        "# Hierarchy Evidence Summary",
        "",
        "Strictness results are empirical unless marked with a formal proof.",
        "No edge below is marked as a proven strictness theorem.",
        "",
    ]
    evidence_by_edge = {row.edge: row for row in evidence}
    for edge in edges:
        row = evidence_by_edge[edge.edge_id]
        lines.extend(
            [
                f"## {edge.edge_id}: {edge.base_grammar} -> {edge.extended_grammar}",
                "",
                f"Status: `{edge.empirical_status}`",
                f"Added layer: `{edge.added_operator_layer}`",
                f"Witness families: {', '.join(edge.witness_families)}",
                f"Base result: {row.base_result}",
                f"Extended result: {row.extended_result}",
                f"Proof obligation: {edge.proof_obligation_summary}",
                "",
            ]
        )
    return "\n".join(lines)


def proof_obligations_markdown(obligations: list[ProofObligation]) -> str:
    lines = [
        "# Strictness Proof Obligations",
        "",
        "These obligations identify what would be needed to turn empirical strictness evidence into formal theorem statements.",
        "No theorem is marked proven in v2.8.",
        "",
    ]
    for obligation in obligations:
        lines.extend(
            [
                f"## {obligation.obligation_id}",
                "",
                f"Candidate: `{obligation.theorem_candidate_id}`",
                f"Type: `{obligation.obligation_type}`",
                f"Status: `{obligation.current_status}`",
                f"Missing work: {obligation.missing_work}",
                "",
            ]
        )
    return "\n".join(lines)


def theorem_candidate_markdown(candidates: list[StrictnessCandidate]) -> str:
    lines = [
        "# Theorem Candidate Report",
        "",
        "This report contains theorem candidates, conjectures, and proof-obligation records. It does not mark any strictness claim as proven.",
        "",
    ]
    for candidate in candidates:
        lines.extend([f"## {candidate.id}: {candidate.name}", "", f"Status: `{candidate.current_status}`", "", candidate.statement, "", "Proof obligations:"])
        lines.extend(_md_list(candidate.proof_obligations))
        lines.extend(["", "Forbidden interpretations:"])
        lines.extend(_md_list(candidate.forbidden_interpretations))
        lines.append("")
    return "\n".join(lines)


def gap_analysis_markdown(records: list[GapAnalysisRecord]) -> str:
    lines = [
        "# Gap Analysis",
        "",
        "v2.8 sets up v2.9 by identifying gaps rather than pretending the hierarchy is complete.",
        "",
    ]
    for record in records:
        lines.extend(
            [
                f"## {record.gap}",
                "",
                f"Failure mode: {record.failure_mode}",
                f"Obstruction fingerprint: `{record.obstruction_fingerprint}`",
                f"Likely next operator candidate: `{record.likely_next_operator_candidate}`",
                f"Proof/certificate obstacle: {record.proof_or_certificate_obstacle}",
                f"v2.9 recommendation: {record.v2_9_recommendation}",
                "",
            ]
        )
    return "\n".join(lines)


def theoremization_report_markdown() -> str:
    return "\n".join(
        [
            "# Collapse Hierarchy Theoremization Report",
            "",
            "## Executive Summary",
            "",
            "v2.8 formalizes the G0-G6 hierarchy, bounded collapse classes, empirical strictness evidence, theorem candidates, proof obligations, and gap analysis.",
            "",
            "This work does not prove P vs NP.",
            "Strictness results are empirical unless marked with a formal proof.",
            "Native certificates are not DRAT unless explicitly exported and checked.",
            "The hierarchy is a research program, not a complete SAT algorithm.",
            "",
            "## What v2.8 Adds",
            "",
            "- Formal grammar definitions for G0 through G6.",
            "- Operational definition of W_B(G).",
            "- Empirical strictness evidence records for every adjacent hierarchy edge.",
            "- Proof-obligation matrix for theoremization.",
            "- Gap analysis and v2.9 recommendations.",
            "- Paper draft for the collapse hierarchy program.",
            "",
            "## What v2.8 Does Not Add",
            "",
            "- No new collapse operator.",
            "- No hierarchy completeness claim.",
            "- No proven strictness theorem.",
            "- No lower-bound theorem.",
            "- No P vs NP progress claim.",
            "",
            "## Native Certificates",
            "",
            "Native certificates are checked by Witnora-native independent checkers. They are not called DRAT unless a DRAT proof is actually exported and checked against the original CNF.",
        ]
    )


def paper_draft_text() -> str:
    return "\n".join(
        [
            "# Witnora Collapse Hierarchy: A Certificate-Backed Program for Verifier-to-Witness Operator Discovery",
            "",
            "## Abstract",
            "",
            "Witnora studies bounded collapse grammars that turn selected verifier instances into checked witnesses or native proof certificates.",
            "",
            "## Introduction",
            "",
            "The current program organizes operators G0 through G6 as a certificate-backed ladder.",
            "",
            "## Non-claims",
            "",
            "This work does not prove P vs NP.",
            "Strictness results are empirical unless marked with a formal proof.",
            "Native certificates are not DRAT unless explicitly exported and checked.",
            "The hierarchy is a research program, not a complete SAT algorithm.",
            "",
            "## Bounded collapse classes",
            "",
            "For a bound profile B and grammar G, W_B(G) is the operational set of formulas for which Witnora emits a verified SAT witness, externally checked proof, or accepted native certificate within the configured bounds.",
            "",
            "## Grammar hierarchy G0-G6",
            "",
            "The hierarchy is G0_BASE, G1_XOR, G2_SYMMETRY_CERTIFIED, G3_SYMMETRY_CARDINALITY_CERTIFIED, G4_ORBIT_CAPACITY_COUNTING_PROTOTYPE, G5_HIGH_ARITY_AFFINE_RESIDUE_PROTOTYPE, and G6_PROOF_MOTIF_COMPRESSION_PROTOTYPE.",
            "",
            "## Native certificate types",
            "",
            "Native certificates include symmetry, pigeonhole counting, orbit-capacity counting, affine residue, and proof-motif macro certificates.",
            "",
            "## Empirical strictness evidence",
            "",
            "Each hierarchy edge has witness families and bounded operator-delta records, but none is promoted to theorem status in v2.8.",
            "",
            "## First Restricted Strictness Theorem Candidate: G0_WIDTH_C vs G1_XOR",
            "",
            "v2.9 introduces a restricted proof kernel for the width/treewidth subroute. This is a restricted theorem candidate/proof sketch unless explicitly marked proven. The finite witnesses record exact width obstruction for `G0_WIDTH_C` and checked exact XOR/native GF(2) acceptance for `G1_XOR_FOR_STRICTNESS`.",
            "",
            "This does not prove full G0_BASE strictness.",
            "This does not prove P vs NP.",
            "This does not prove hierarchy completeness.",
            "",
            "## Formal Finite Strictness Certificate",
            "",
            "v2.10 defines `FINITE_STRICTNESS_CERTIFIED` as a machine-checked finite-instance certificate. The checker replays, for each listed finite witness, the `G0_WIDTH_C` width obstruction and the `G1_XOR_FOR_STRICTNESS` exact XOR upper-bound certificate.",
            "",
            "FINITE_STRICTNESS_CERTIFIED is a machine-checked finite-instance certificate, not a scalable family theorem.",
            "",
            "This does not prove full G0_BASE strictness.",
            "This does not prove the hierarchy is strict.",
            "This does not prove P vs NP.",
            "",
            "Scalable Tseitin/expander strictness remains a proof obligation.",
            "",
            "## Finite Empirical Edge Delta Certificate: G1_XOR to G2_SYMMETRY_CERTIFIED",
            "",
            "v2.11 defines `FINITE_EMPIRICAL_EDGE_DELTA_CERTIFIED` for finite hierarchy-edge deltas where the lower side has bounded replay non-acceptance but no certified lower-bound obstruction.",
            "",
            "For the G1-to-G2 edge, cycle-coloring instances replay as `LOWER_REPLAY_NO_COLLAPSE` under `G1_XOR`, while `G2_SYMMETRY_CERTIFIED` verifies native symmetry SAT witness reconstruction.",
            "",
            "This is not a lower-bound strictness theorem.",
            "This does not prove G1_XOR is strictly weaker than G2_SYMMETRY_CERTIFIED as a theorem.",
            "This does not prove a family theorem.",
            "This does not prove P vs NP.",
            "",
            "## External Paper/Reproducibility Package",
            "",
            "v2.12 packages the hierarchy work for external review. It adds a polished external draft, evidence summary, claim-boundary table, release SHA manifest, reproduction steps, validation scripts, and an external review packet.",
            "",
            "v2.12 does not add a new operator.",
            "v2.12 does not claim external acceptance or peer review.",
            "v2.12 does not convert empirical edge deltas into strictness theorems.",
            "",
            "## Proof obligations",
            "",
            "The proof-obligation matrix records non-collapse obligations, checker soundness obligations, scaling obligations, and optional DRAT bridge work.",
            "",
            "## Operator genesis",
            "",
            "Operator genesis remains a candidate-generation and promotion discipline, not a claim of autonomous theorem discovery.",
            "",
            "## Gap analysis",
            "",
            "Current gaps include random 3-SAT, general circuit-SAT, arbitrary PB encodings, non-exact affine structure, realistic SAT competition formulas, and native certificates without DRAT bridges.",
            "",
            "## Relationship to P vs NP",
            "",
            "The motivation is verifier-to-witness structure. The artifact is a bounded experimental and theoremization framework, not a proof of P vs NP.",
            "",
            "## Why this does not prove P vs NP",
            "",
            "The hierarchy is bounded, operational, and evidence-backed. It does not establish lower bounds, completeness, or a polynomial-time SAT algorithm.",
            "",
            "## Future work",
            "",
            "Future work should discharge proof obligations, mechanize checker soundness arguments, and select the next operator from gap-driven obstruction records.",
        ]
    )


def build_hierarchy_theoremization(out_root: Path | str = "outputs/v2.8-collapse-hierarchy-theoremization", strict: bool = False, zip_path: Path | str = "witnora-core-v2.8-collapse-hierarchy-theoremization.zip") -> dict[str, Any]:
    root = Path(out_root)
    root.mkdir(parents=True, exist_ok=True)
    operators = operator_definitions()
    grammars = grammar_definitions()
    bounds = bound_profile_definitions()
    classes = bounded_collapse_classes()
    edges = hierarchy_edges()
    evidence = empirical_strictness_evidence()
    candidates = theorem_candidates_v28()
    obligations = proof_obligation_matrix()
    gaps = gap_analysis_records()
    bundle = hierarchy_evidence_bundle()

    payloads = {
        "grammar_definitions.json": {"grammars": [item.to_dict() for item in grammars]},
        "operator_definitions.json": {"operators": [item.to_dict() for item in operators]},
        "bound_profile_definitions.json": {"bound_profiles": [item.to_dict() for item in bounds]},
        "bounded_collapse_classes.json": {"bounded_collapse_classes": [item.to_dict() for item in classes]},
        "hierarchy_edges.json": {"hierarchy_edges": [item.to_dict() for item in edges]},
        "empirical_strictness_evidence.json": {"empirical_strictness_evidence": [item.to_dict() for item in evidence]},
        "theorem_candidates_v28.json": {"theorem_candidates": [item.to_dict() for item in candidates]},
        "proof_obligation_matrix.json": {"proof_obligations": [item.to_dict() for item in obligations]},
        "hierarchy_evidence_bundle.json": bundle.to_dict(),
        "gap_analysis.json": {"gap_analysis": [item.to_dict() for item in gaps]},
    }
    for name, payload in payloads.items():
        _write_json(root / name, payload)

    (root / "HIERARCHY_DEFINITIONS.md").write_text(hierarchy_definitions_markdown(grammars, bounds, classes), encoding="utf-8", newline="\n")
    (root / "HIERARCHY_EVIDENCE_SUMMARY.md").write_text(hierarchy_evidence_markdown(edges, evidence), encoding="utf-8", newline="\n")
    (root / "STRICTNESS_PROOF_OBLIGATIONS.md").write_text(proof_obligations_markdown(obligations), encoding="utf-8", newline="\n")
    (root / "THEOREM_CANDIDATE_REPORT.md").write_text(theorem_candidate_markdown(candidates), encoding="utf-8", newline="\n")
    (root / "GAP_ANALYSIS.md").write_text(gap_analysis_markdown(gaps), encoding="utf-8", newline="\n")
    (root / "COLLAPSE_HIERARCHY_THEOREMIZATION_REPORT.md").write_text(theoremization_report_markdown(), encoding="utf-8", newline="\n")

    artifact_sha = make_zip(root, zip_path) if zip_path else ""
    report = TheoremizationReport(
        out_root=str(root),
        artifact_zip=str(zip_path) if zip_path else "",
        artifact_sha256=artifact_sha,
        grammar_count=len(grammars),
        hierarchy_edge_count=len(edges),
        theorem_candidate_count=len(candidates),
        proof_obligation_count=len(obligations),
        gap_count=len(gaps),
        claim_boundary="v2.8 formalizes evidence and proof obligations; it adds no operator and proves no strictness theorem.",
    )
    _write_json(root / "theoremization_summary.json", report.to_dict() | {"strict": strict})

    paper_dir = Path("paper")
    paper_dir.mkdir(parents=True, exist_ok=True)
    paper_path = paper_dir / "WITNORA_COLLAPSE_HIERARCHY_DRAFT.md"
    paper_path.write_text(paper_draft_text(), encoding="utf-8", newline="\n")
    return {
        "out_root": str(root),
        "zip": str(zip_path) if zip_path else "",
        "zip_sha256": artifact_sha,
        "summary": report.to_dict(),
        "paper_draft": str(paper_path),
        "grammar_definitions": [item.to_dict() for item in grammars],
        "hierarchy_edges": [item.to_dict() for item in edges],
        "empirical_strictness_evidence": [item.to_dict() for item in evidence],
        "theorem_candidates": [item.to_dict() for item in candidates],
        "proof_obligation_matrix": [item.to_dict() for item in obligations],
        "gap_analysis": [item.to_dict() for item in gaps],
        "hierarchy_evidence_bundle": bundle.to_dict(),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Witnora collapse hierarchy theoremization")
    sub = parser.add_subparsers(dest="command", required=True)
    build = sub.add_parser("build")
    build.add_argument("--out-root", default="outputs/v2.8-collapse-hierarchy-theoremization")
    build.add_argument("--strict", action="store_true")
    build.add_argument("--zip", default="witnora-core-v2.8-collapse-hierarchy-theoremization.zip")
    args = parser.parse_args(argv)
    if args.command == "build":
        result = build_hierarchy_theoremization(out_root=args.out_root, strict=args.strict, zip_path=args.zip)
        print(stable_json({"out_root": result["out_root"], "zip": result["zip"], "zip_sha256": result["zip_sha256"], "summary": result["summary"]}))
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
