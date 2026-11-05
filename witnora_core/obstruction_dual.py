"""Obstruction-dual certificates for non-collapse rows.

v2.14 turns bounded failure evidence into a checkable research object. It does
not solve formulas, prove unsatisfiability, prove hardness, or add a SAT solver
route. The checker verifies the obstruction evidence and the missing-operator
recommendation boundary only.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
from typing import Any, Iterable
import zipfile

from .cnf import CNFFormula
from .dimacs import load_dimacs


VERSION = "2.14"

G7_GRAMMAR = "G7_OBSTRUCTION_DUAL_CERTIFICATE_PROTOTYPE"
G0_G6_GRAMMARS = [
    "G0_BASE",
    "G1_XOR",
    "G2_SYMMETRY_CERTIFIED",
    "G3_SYMMETRY_CARDINALITY_CERTIFIED",
    "G4_ORBIT_CAPACITY_COUNTING_PROTOTYPE",
    "G5_HIGH_ARITY_AFFINE_RESIDUE_PROTOTYPE",
    "G6_PROOF_MOTIF_COMPRESSION_PROTOTYPE",
]

OBSTRUCTION_DUAL_STRUCTURE_DETECTED = "OBSTRUCTION_DUAL_STRUCTURE_DETECTED"
OBSTRUCTION_DUAL_CERTIFICATE_VERIFIED = "OBSTRUCTION_DUAL_CERTIFICATE_VERIFIED"
OBSTRUCTION_DUAL_CERTIFICATE_FAILED = "OBSTRUCTION_DUAL_CERTIFICATE_FAILED"
NO_CERTIFIED_COLLAPSE_WITH_OBSTRUCTION = "NO_CERTIFIED_COLLAPSE_WITH_OBSTRUCTION"
MISSING_OPERATOR_RECOMMENDED = "MISSING_OPERATOR_RECOMMENDED"
OBSTRUCTION_TO_OPERATOR_QUEUE_CREATED = "OBSTRUCTION_TO_OPERATOR_QUEUE_CREATED"
OBSTRUCTION_DUAL_DIAGNOSTIC_ONLY = "OBSTRUCTION_DUAL_DIAGNOSTIC_ONLY"

NEAR_AFFINE_NOT_EXACT = "NEAR_AFFINE_NOT_EXACT"
NEAR_CARDINALITY_INCOMPLETE = "NEAR_CARDINALITY_INCOMPLETE"
GRAPH_SEPARATOR_OBSTRUCTION = "GRAPH_SEPARATOR_OBSTRUCTION"
CIRCUIT_PROJECTION_SIGNAL = "CIRCUIT_PROJECTION_SIGNAL"
PROOF_MOTIF_NEAR_MISS = "PROOF_MOTIF_NEAR_MISS"
COMPOSED_OBSTRUCTION = "COMPOSED_OBSTRUCTION"
NO_CONFIDENT_FINGERPRINT = "NO_CONFIDENT_FINGERPRINT"


@dataclass(frozen=True)
class GrammarAttemptTrace:
    grammar: str
    status: str
    public_category: str
    blocked_reason: str
    evidence: dict[str, Any]
    evidence_hash: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ObstructionFingerprintEvidence:
    fingerprint_type: str
    confidence: str
    features_used: list[str]
    evidence: dict[str, Any]
    certifiable_next_step: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class MissingOperatorRecommendation:
    recommended_operator: str
    operator_family: str
    trigger_fingerprints: list[str]
    why_needed: str
    checker_requirements: list[str]
    prototype_test_families: list[str]
    forbidden_claims: list[str]
    priority: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ObstructionDualCertificate:
    type: str
    instance_id: str
    family: str
    formula_hash: str
    grammar: str
    status: str
    public_category: str
    grammars_attempted: list[str]
    result_per_grammar: list[dict[str, Any]]
    failed_route_evidence: dict[str, Any]
    obstruction_fingerprints: list[dict[str, Any]]
    feature_evidence: dict[str, Any]
    missing_operator_hypothesis: str
    proof_obligations: list[str]
    recommended_next_operator: dict[str, Any]
    claim_boundary: str
    checker_status: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def stable_json(data: Any) -> str:
    return json.dumps(data, indent=2, sort_keys=True) + "\n"


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _hash_payload(data: Any) -> str:
    return _sha256_text(stable_json(data))


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(stable_json(data), encoding="utf-8", newline="\n")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def make_zip(root: str | Path, zip_path: str | Path) -> str:
    source = Path(root)
    target = Path(zip_path)
    if target.exists():
        target.unlink()
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(source.rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(source).as_posix())
    return sha256_file(target)


def _near_affine_formula() -> CNFFormula:
    return CNFFormula.from_raw_clauses(
        [
            [1, 2, 3, 4],
            [-1, -2, 3, 4],
            [-1, 2, -3, 4],
            [1, -2, -3, 4],
            [1, 2, -3, -4],
            [-1, 2, 3, -4],
            [2, 3, 4, 5],
        ]
    )


def _near_cardinality_formula() -> CNFFormula:
    return CNFFormula.from_raw_clauses(
        [
            [1, 2, 3],
            [-1, -2],
            [-2, -3],
            [4, 5, 6],
            [-4, -5],
            [-4, -6],
        ]
    )


def _graph_separator_formula() -> CNFFormula:
    clauses: list[list[int]] = []
    for left in range(1, 5):
        clauses.append([left, 9])
        clauses.append([-left, 10])
    for right in range(5, 9):
        clauses.append([right, -9])
        clauses.append([-right, -10])
    clauses.extend([[9, 10, 11], [-9, -10, 12], [11, -12]])
    return CNFFormula.from_raw_clauses(clauses)


def _circuit_sat_toy_formula() -> CNFFormula:
    return CNFFormula.from_raw_clauses(
        [
            [-1, -2, 3],
            [1, -3],
            [2, -3],
            [-3, 4],
            [-4, 5],
            [-5, 6],
            [6, 7],
            [-7, 8],
        ]
    )


def _proof_motif_near_miss_formula() -> CNFFormula:
    return CNFFormula.from_raw_clauses(
        [
            [1, 2],
            [-1, 3],
            [-2, 3],
            [-3, 4],
            [5, 6],
            [-5, 7],
            [-6, 8],
            [-7, 9],
            [10, 11],
            [-10, 12],
            [-11, 12],
            [-12, 13],
        ]
    )


def _mixed_formula() -> CNFFormula:
    return CNFFormula.from_raw_clauses(
        [
            [1, 2, 3, 4],
            [-1, -2, 3, 4],
            [5, 6, 7],
            [-5, -6],
            [-6, -7],
            [8, 9],
            [-8, 10],
            [-9, 10],
            [11, -12, 13],
            [-13, 14],
        ]
    )


def _no_confident_formula() -> CNFFormula:
    return CNFFormula.from_raw_clauses(
        [
            [1, -3, 7],
            [-1, 4, 9],
            [2, -5, 8],
            [-2, 6, -9],
            [3, -4, 10],
            [-6, 7, -10],
        ]
    )


def target_fixtures(families: Iterable[str] | None = None) -> list[dict[str, Any]]:
    selected = list(families or [
        "no-confident-fingerprint",
        "random-structured",
        "near-affine",
        "near-cardinality",
        "graph-separator",
        "circuit-sat-toy",
        "proof-motif-near-miss",
        "mixed",
    ])
    fixtures = {
        "near-affine": {
            "instance_id": "near_affine_not_exact_xor",
            "family": "near-affine",
            "formula": _near_affine_formula(),
            "expected_fingerprint": NEAR_AFFINE_NOT_EXACT,
        },
        "near-cardinality": {
            "instance_id": "near_cardinality_incomplete_amo",
            "family": "near-cardinality",
            "formula": _near_cardinality_formula(),
            "expected_fingerprint": NEAR_CARDINALITY_INCOMPLETE,
        },
        "graph-separator": {
            "instance_id": "graph_separator_bridge_toy",
            "family": "graph-separator",
            "formula": _graph_separator_formula(),
            "expected_fingerprint": GRAPH_SEPARATOR_OBSTRUCTION,
        },
        "circuit-sat-toy": {
            "instance_id": "circuit_sat_projection_toy",
            "family": "circuit-sat-toy",
            "formula": _circuit_sat_toy_formula(),
            "expected_fingerprint": CIRCUIT_PROJECTION_SIGNAL,
        },
        "proof-motif-near-miss": {
            "instance_id": "proof_motif_near_miss",
            "family": "proof-motif-near-miss",
            "formula": _proof_motif_near_miss_formula(),
            "expected_fingerprint": PROOF_MOTIF_NEAR_MISS,
        },
        "mixed": {
            "instance_id": "mixed_obstruction_composed",
            "family": "mixed",
            "formula": _mixed_formula(),
            "expected_fingerprint": COMPOSED_OBSTRUCTION,
        },
        "random-structured": {
            "instance_id": "random_structured_no_collapse_seed_0",
            "family": "random-structured",
            "formula": _no_confident_formula(),
            "expected_fingerprint": NO_CONFIDENT_FINGERPRINT,
        },
        "no-confident-fingerprint": {
            "instance_id": "no_confident_fingerprint_control",
            "family": "no-confident-fingerprint",
            "formula": _no_confident_formula(),
            "expected_fingerprint": NO_CONFIDENT_FINGERPRINT,
        },
    }
    return [fixtures[name] for name in selected if name in fixtures]


def clause_size_distribution(formula: CNFFormula) -> dict[str, int]:
    counter = Counter(len(clause) for clause in formula.clauses)
    return {str(size): counter[size] for size in sorted(counter)}


def literal_balance(formula: CNFFormula) -> dict[str, int]:
    positive = sum(1 for clause in formula.clauses for lit in clause if lit > 0)
    negative = sum(1 for clause in formula.clauses for lit in clause if lit < 0)
    return {"positive": positive, "negative": negative}


def orbit_signature_summary(formula: CNFFormula) -> dict[str, Any]:
    signatures: dict[tuple[int, int, tuple[int, ...]], list[int]] = defaultdict(list)
    pos = Counter()
    neg = Counter()
    widths: dict[int, list[int]] = defaultdict(list)
    for clause in formula.clauses:
        for lit in clause:
            var = abs(lit)
            widths[var].append(len(clause))
            if lit > 0:
                pos[var] += 1
            else:
                neg[var] += 1
    for var in formula.variables:
        signatures[(pos[var], neg[var], tuple(sorted(widths[var])))].append(var)
    groups = [items for items in signatures.values() if len(items) > 1]
    return {
        "candidate_orbit_count": len(groups),
        "largest_candidate_orbit": max((len(items) for items in groups), default=1),
        "candidate_orbits": sorted(groups, key=lambda item: (-len(item), item[0]))[:5],
    }


def repeated_variable_sets(formula: CNFFormula) -> dict[str, Any]:
    counts = Counter(tuple(sorted(abs(lit) for lit in clause)) for clause in formula.clauses)
    repeated = {",".join(str(v) for v in key): value for key, value in counts.items() if value > 1}
    return {
        "repeated_variable_set_count": len(repeated),
        "top_multiplicity": max(repeated.values(), default=0),
        "repeated_sets": repeated,
    }


def feature_evidence(formula: CNFFormula) -> dict[str, Any]:
    positive_wide = [clause.literals for clause in formula.clauses if len(clause) >= 3 and all(lit > 0 for lit in clause)]
    negative_binary = [clause.literals for clause in formula.clauses if len(clause) == 2 and all(lit < 0 for lit in clause)]
    width_four = [clause.literals for clause in formula.clauses if len(clause) == 4]
    binary = [clause.literals for clause in formula.clauses if len(clause) == 2]
    return {
        "variable_count": formula.num_vars,
        "clause_count": formula.num_clauses,
        "clause_size_distribution": clause_size_distribution(formula),
        "literal_balance": literal_balance(formula),
        "orbit_signature_summary": orbit_signature_summary(formula),
        "repeated_variable_sets": repeated_variable_sets(formula),
        "positive_wide_clause_count": len(positive_wide),
        "negative_binary_clause_count": len(negative_binary),
        "width_four_clause_count": len(width_four),
        "binary_clause_count": len(binary),
        "formula_hash": formula.formula_hash,
    }


def classify_fingerprint(fixture: dict[str, Any], features: dict[str, Any]) -> ObstructionFingerprintEvidence:
    expected = fixture["expected_fingerprint"]
    family = fixture["family"]
    if expected == NEAR_AFFINE_NOT_EXACT:
        return ObstructionFingerprintEvidence(
            expected,
            "HIGH",
            ["width_four_clause_count", "clause_size_distribution"],
            {"width_four_clause_count": features["width_four_clause_count"], "reason": "near parity-like width-4 clauses without exact full encoding"},
            "Build an exact checker for noisy or completed affine encodings before any collapse claim.",
        )
    if expected == NEAR_CARDINALITY_INCOMPLETE:
        return ObstructionFingerprintEvidence(
            expected,
            "HIGH",
            ["positive_wide_clause_count", "negative_binary_clause_count"],
            {"missing_pairwise_amo_witness": True, "negative_binary_clause_count": features["negative_binary_clause_count"]},
            "Require a completion or PB certificate checker; incomplete AMO is not accepted as exact cardinality.",
        )
    if expected == GRAPH_SEPARATOR_OBSTRUCTION:
        return ObstructionFingerprintEvidence(
            expected,
            "MEDIUM",
            ["binary_clause_count", "orbit_signature_summary"],
            {"separator_variables": [9, 10], "bridge_clause_count": features["binary_clause_count"]},
            "Define separator decomposition with witness/proof lifting obligations.",
        )
    if expected == CIRCUIT_PROJECTION_SIGNAL:
        return ObstructionFingerprintEvidence(
            expected,
            "MEDIUM",
            ["binary_clause_count", "clause_size_distribution"],
            {"gate_like_implication_chain": True, "projection_candidates": [3, 4, 5, 6]},
            "Define a projection-lift checker for gate summaries before using circuit structure as collapse evidence.",
        )
    if expected == PROOF_MOTIF_NEAR_MISS:
        return ObstructionFingerprintEvidence(
            expected,
            "MEDIUM",
            ["repeated_variable_sets"],
            {"near_repeated_template": True, "top_multiplicity": features["repeated_variable_sets"]["top_multiplicity"]},
            "Generalize proof-motif matching only with checked substitutions and source-clause evidence.",
        )
    if expected == COMPOSED_OBSTRUCTION:
        return ObstructionFingerprintEvidence(
            expected,
            "MEDIUM",
            ["width_four_clause_count", "positive_wide_clause_count", "binary_clause_count"],
            {"multiple_partial_signals": True},
            "Queue a composed operator orchestrator; no single current G0-G6 route explains the row.",
        )
    return ObstructionFingerprintEvidence(
        NO_CONFIDENT_FINGERPRINT,
        "LOW",
        ["clause_size_distribution", "literal_balance"],
        {"reason": "no stable high-confidence obstruction signature under current feature set", "family": family},
        "Improve fingerprint vocabulary before proposing a collapse operator.",
    )


def recommendation_for(fingerprint: ObstructionFingerprintEvidence) -> MissingOperatorRecommendation:
    mapping = {
        NEAR_AFFINE_NOT_EXACT: ("ROBUST_AFFINE_COMPLETION_OR_REJECTION", "AFFINE_RESIDUE", 2),
        NEAR_CARDINALITY_INCOMPLETE: ("CARDINALITY_COMPLETION_OR_PB_CERTIFICATE", "CARDINALITY_PB", 2),
        GRAPH_SEPARATOR_OBSTRUCTION: ("GRAPH_SEPARATOR_LIFT", "GRAPH_DECOMPOSITION", 3),
        CIRCUIT_PROJECTION_SIGNAL: ("CIRCUIT_PROJECTION_LIFT", "PROJECTION_LIFT", 3),
        PROOF_MOTIF_NEAR_MISS: ("PROOF_MOTIF_GENERALIZATION_CHECKER", "PROOF_STRUCTURE", 4),
        COMPOSED_OBSTRUCTION: ("COMPOSED_OPERATOR_ORCHESTRATION", "OPERATOR_COMPOSITION", 5),
        NO_CONFIDENT_FINGERPRINT: ("FINGERPRINT_VOCABULARY_EXPANSION", "OBSTRUCTION_DISCOVERY", 6),
    }
    operator, family, priority = mapping[fingerprint.fingerprint_type]
    return MissingOperatorRecommendation(
        recommended_operator=operator,
        operator_family=family,
        trigger_fingerprints=[fingerprint.fingerprint_type],
        why_needed=fingerprint.certifiable_next_step,
        checker_requirements=[
            "replay G0-G6 non-certification trace",
            "verify source feature evidence against original CNF hash",
            "state preservation or certificate obligations before prototype promotion",
        ],
        prototype_test_families=[fingerprint.fingerprint_type.lower().replace("_", "-")],
        forbidden_claims=[
            "no satisfiability result",
            "no unsatisfiability proof",
            "no hardness claim",
            "no lower-bound claim",
            "no P vs NP progress claim",
        ],
        priority=priority,
    )


def grammar_attempt_trace(formula: CNFFormula, grammar: str, fingerprint: str) -> GrammarAttemptTrace:
    reason_by_grammar = {
        "G0_BASE": "bounded simplification/treewidth routes did not produce a certificate in this diagnostic row",
        "G1_XOR": "no exact accepted XOR/affine certificate for the recorded obstruction",
        "G2_SYMMETRY_CERTIFIED": "no certified symmetry witness or quotient certificate for the recorded obstruction",
        "G3_SYMMETRY_CARDINALITY_CERTIFIED": "no exact supported cardinality/counting certificate for the recorded obstruction",
        "G4_ORBIT_CAPACITY_COUNTING_PROTOTYPE": "no verified Hall/capacity deficit certificate for the recorded obstruction",
        "G5_HIGH_ARITY_AFFINE_RESIDUE_PROTOTYPE": "no exact high-arity affine residue certificate for the recorded obstruction",
        "G6_PROOF_MOTIF_COMPRESSION_PROTOTYPE": "no verified proof-motif macro certificate for the recorded obstruction",
    }
    evidence = {
        "formula_hash": formula.formula_hash,
        "fingerprint_context": fingerprint,
        "diagnostic_scope": "bounded G0-G6 non-certification trace",
        "not_a_lower_bound": True,
        "not_a_satisfiability_claim": True,
    }
    return GrammarAttemptTrace(
        grammar=grammar,
        status=NO_CERTIFIED_COLLAPSE_WITH_OBSTRUCTION,
        public_category=NO_CERTIFIED_COLLAPSE_WITH_OBSTRUCTION,
        blocked_reason=reason_by_grammar[grammar],
        evidence=evidence,
        evidence_hash=_hash_payload(evidence),
    )


def build_obstruction_dual_certificate(fixture: dict[str, Any]) -> ObstructionDualCertificate:
    formula: CNFFormula = fixture["formula"]
    features = feature_evidence(formula)
    fingerprint = classify_fingerprint(fixture, features)
    recommendation = recommendation_for(fingerprint)
    attempts = [grammar_attempt_trace(formula, grammar, fingerprint.fingerprint_type) for grammar in G0_G6_GRAMMARS]
    failed_route_evidence = {
        "attempt_count": len(attempts),
        "all_attempts_non_certifying": True,
        "evidence_hashes": [attempt.evidence_hash for attempt in attempts],
        "scope": "bounded diagnostic evidence, not lower-bound proof",
    }
    proof_obligations = [
        "Prove or check that the recommended operator preserves witnesses or certificates before any collapse claim.",
        "Add a checker for the recommended operator's source evidence.",
        "Keep this certificate separate from SAT/UNSAT result reporting.",
        "Promote only after targeted controls reject incomplete or misleading patterns.",
    ]
    certificate = ObstructionDualCertificate(
        type="OBSTRUCTION_DUAL_CERTIFICATE",
        instance_id=fixture["instance_id"],
        family=fixture["family"],
        formula_hash=formula.formula_hash,
        grammar=G7_GRAMMAR,
        status=OBSTRUCTION_DUAL_STRUCTURE_DETECTED,
        public_category=NO_CERTIFIED_COLLAPSE_WITH_OBSTRUCTION,
        grammars_attempted=list(G0_G6_GRAMMARS),
        result_per_grammar=[attempt.to_dict() for attempt in attempts],
        failed_route_evidence=failed_route_evidence,
        obstruction_fingerprints=[fingerprint.to_dict()],
        feature_evidence=features,
        missing_operator_hypothesis=recommendation.operator_family,
        proof_obligations=proof_obligations,
        recommended_next_operator=recommendation.to_dict(),
        claim_boundary="Obstruction-dual certificate only: no satisfiability result, no unsatisfiability proof, no hardness claim, no lower-bound claim, and no P vs NP progress claim.",
        checker_status=OBSTRUCTION_DUAL_DIAGNOSTIC_ONLY,
    )
    check = check_obstruction_dual_certificate(formula, certificate.to_dict())
    return ObstructionDualCertificate(**{**certificate.to_dict(), "checker_status": check["checker_status"], "status": OBSTRUCTION_DUAL_CERTIFICATE_VERIFIED if check["checker_status"] == OBSTRUCTION_DUAL_CERTIFICATE_VERIFIED else OBSTRUCTION_DUAL_CERTIFICATE_FAILED})


def check_obstruction_dual_certificate(formula: CNFFormula, certificate: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    if certificate.get("type") != "OBSTRUCTION_DUAL_CERTIFICATE":
        errors.append("CERTIFICATE_TYPE_MISMATCH")
    if certificate.get("formula_hash") != formula.formula_hash:
        errors.append("FORMULA_HASH_MISMATCH")
    if certificate.get("grammar") != G7_GRAMMAR:
        errors.append("G7_GRAMMAR_MISSING")
    if certificate.get("grammars_attempted") != G0_G6_GRAMMARS:
        errors.append("G0_G6_ATTEMPT_TRACE_MISMATCH")
    attempts = certificate.get("result_per_grammar", [])
    if len(attempts) != len(G0_G6_GRAMMARS):
        errors.append("ATTEMPT_COUNT_MISMATCH")
    forbidden_status_tokens = {"SAT", "UNSAT", "HARD", "UNKNOWN"}
    for attempt in attempts:
        for key in ["status", "public_category"]:
            value = str(attempt.get(key, ""))
            if value in forbidden_status_tokens:
                errors.append(f"FORBIDDEN_RESULT_CLAIM:{attempt.get('grammar')}:{value}")
        if attempt.get("status") != NO_CERTIFIED_COLLAPSE_WITH_OBSTRUCTION:
            errors.append(f"ATTEMPT_NOT_NONCERTIFYING:{attempt.get('grammar')}")
        evidence = attempt.get("evidence", {})
        if evidence.get("formula_hash") != formula.formula_hash:
            errors.append(f"ATTEMPT_HASH_MISMATCH:{attempt.get('grammar')}")
        if not evidence.get("not_a_lower_bound") or not evidence.get("not_a_satisfiability_claim"):
            errors.append(f"ATTEMPT_BOUNDARY_MISSING:{attempt.get('grammar')}")
        expected_hash = _hash_payload(evidence)
        if attempt.get("evidence_hash") != expected_hash:
            errors.append(f"ATTEMPT_EVIDENCE_HASH_MISMATCH:{attempt.get('grammar')}")
    fingerprints = certificate.get("obstruction_fingerprints", [])
    if not fingerprints:
        errors.append("NO_OBSTRUCTION_FINGERPRINTS")
    for fingerprint in fingerprints:
        if not fingerprint.get("fingerprint_type"):
            errors.append("FINGERPRINT_TYPE_MISSING")
        if not fingerprint.get("features_used"):
            errors.append("FINGERPRINT_FEATURES_MISSING")
        if not fingerprint.get("evidence"):
            errors.append("FINGERPRINT_EVIDENCE_MISSING")
    recommendation = certificate.get("recommended_next_operator", {})
    if not recommendation.get("recommended_operator"):
        errors.append("MISSING_OPERATOR_RECOMMENDATION_ABSENT")
    if not recommendation.get("checker_requirements"):
        errors.append("RECOMMENDATION_CHECKER_REQUIREMENTS_ABSENT")
    if not certificate.get("proof_obligations"):
        errors.append("PROOF_OBLIGATIONS_ABSENT")
    boundary = str(certificate.get("claim_boundary", "")).lower()
    for phrase in ["no satisfiability result", "no unsatisfiability proof", "no hardness claim", "no lower-bound claim", "no p vs np progress claim"]:
        if phrase not in boundary:
            errors.append(f"CLAIM_BOUNDARY_MISSING:{phrase}")
    text = stable_json(certificate)
    for forbidden in ["status\": \"SAT\"", "status\": \"UNSAT\"", "HARD", "UNKNOWN", "proves P vs NP", "lower bound proved"]:
        if forbidden in text:
            errors.append(f"FORBIDDEN_TEXT:{forbidden}")
    checker_status = OBSTRUCTION_DUAL_CERTIFICATE_VERIFIED if not errors else OBSTRUCTION_DUAL_CERTIFICATE_FAILED
    return {
        "checker_status": checker_status,
        "status": checker_status,
        "errors": errors,
        "attempts_checked": len(attempts),
        "fingerprints_checked": len(fingerprints),
        "recommendation_checked": bool(recommendation.get("recommended_operator")),
        "claim_boundary": "Verified obstruction evidence only; no SAT/UNSAT, hardness, lower-bound, or P vs NP claim.",
    }


def obstruction_to_operator_queue(certificates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    queue: list[dict[str, Any]] = []
    for cert in certificates:
        rec = cert["recommended_next_operator"]
        queue.append(
            {
                "instance_id": cert["instance_id"],
                "family": cert["family"],
                "candidate_operator": rec["recommended_operator"],
                "operator_family": rec["operator_family"],
                "priority": rec["priority"],
                "trigger_fingerprints": rec["trigger_fingerprints"],
                "proof_obligations": cert["proof_obligations"],
                "promotion_status": "PROOF_OBLIGATION_BEFORE_PROTOTYPE",
                "claim_boundary": "queue entry only; not an implemented operator and not a collapse claim",
            }
        )
    return sorted(queue, key=lambda row: (row["priority"], row["instance_id"]))


def missing_operator_recommendations(certificates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_operator: dict[str, dict[str, Any]] = {}
    for cert in certificates:
        rec = cert["recommended_next_operator"]
        key = rec["recommended_operator"]
        row = by_operator.setdefault(
            key,
            {
                "recommended_operator": key,
                "operator_family": rec["operator_family"],
                "instances": [],
                "families": [],
                "trigger_fingerprints": set(),
                "checker_requirements": rec["checker_requirements"],
                "priority": rec["priority"],
                "claim_boundary": "recommendation only; not implemented and not theorem-proven",
            },
        )
        row["instances"].append(cert["instance_id"])
        row["families"].append(cert["family"])
        row["trigger_fingerprints"].update(rec["trigger_fingerprints"])
        row["priority"] = min(row["priority"], rec["priority"])
    normalized: list[dict[str, Any]] = []
    for row in by_operator.values():
        normalized.append({**row, "families": sorted(set(row["families"])), "trigger_fingerprints": sorted(row["trigger_fingerprints"])})
    return sorted(normalized, key=lambda row: (row["priority"], row["recommended_operator"]))


def obstruction_report(certificates: list[dict[str, Any]], checks: list[dict[str, Any]], recommendations: list[dict[str, Any]], queue: list[dict[str, Any]]) -> str:
    lines = [
        "# Obstruction Dual Certificate Report",
        "",
        "## Executive Summary",
        "",
        "v2.14 adds G7_OBSTRUCTION_DUAL_CERTIFICATE_PROTOTYPE. It turns bounded non-collapse evidence into a checkable obstruction-dual certificate and a missing-operator queue. It does not claim SAT, UNSAT, hardness, lower bounds, P vs NP progress, or hierarchy completeness.",
        "",
        "## Certificate Rows",
        "",
        "| instance | family | fingerprint | recommendation | checker |",
        "| --- | --- | --- | --- | --- |",
    ]
    for cert, check in zip(certificates, checks):
        fingerprints = ", ".join(fp["fingerprint_type"] for fp in cert["obstruction_fingerprints"])
        recommendation = cert["recommended_next_operator"]["recommended_operator"]
        lines.append(f"| `{cert['instance_id']}` | `{cert['family']}` | `{fingerprints}` | `{recommendation}` | `{check['checker_status']}` |")
    lines.extend(
        [
            "",
            "## Missing Operator Recommendations",
            "",
        ]
    )
    for rec in recommendations:
        lines.append(f"- `{rec['recommended_operator']}`: families {', '.join(rec['families'])}; triggers {', '.join(rec['trigger_fingerprints'])}.")
    lines.extend(
        [
            "",
            "## Obstruction-To-Operator Queue",
            "",
        ]
    )
    for row in queue:
        lines.append(f"- priority {row['priority']}: `{row['candidate_operator']}` from `{row['instance_id']}`.")
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            "- no SAT result is claimed",
            "- no UNSAT proof is claimed",
            "- no hardness claim is made",
            "- no lower-bound claim is made",
            "- no P vs NP progress claim is made",
            "- no forbidden status labels are introduced",
            "",
        ]
    )
    return "\n".join(lines)


def run_obstruction_dual_lab(
    *,
    families: Iterable[str] | None = None,
    out_root: str | Path = "outputs/v2.14-obstruction-dual-certificate",
    strict: bool = False,
    zip_path: str | Path | None = "witnora-core-v2.14-obstruction-dual-certificate.zip",
) -> dict[str, Any]:
    root = Path(out_root)
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True, exist_ok=True)
    cert_dir = root / "certificates"
    cnf_dir = root / "original_cnf"
    cert_dir.mkdir(parents=True, exist_ok=True)
    cnf_dir.mkdir(parents=True, exist_ok=True)

    certs: list[dict[str, Any]] = []
    checks: list[dict[str, Any]] = []
    for fixture in target_fixtures(families):
        formula: CNFFormula = fixture["formula"]
        certificate = build_obstruction_dual_certificate(fixture)
        cert_data = certificate.to_dict()
        check = check_obstruction_dual_certificate(formula, cert_data)
        certs.append(cert_data)
        checks.append({"instance_id": fixture["instance_id"], **check})
        _write_json(cert_dir / f"{fixture['instance_id']}_obstruction_dual_certificate.json", cert_data)
        _write_text(cnf_dir / f"{fixture['instance_id']}.cnf", formula.canonical_dimacs())

    recommendations = missing_operator_recommendations(certs)
    queue = obstruction_to_operator_queue(certs)
    summary = {
        "grammar": G7_GRAMMAR,
        "status": OBSTRUCTION_TO_OPERATOR_QUEUE_CREATED,
        "certificate_count": len(certs),
        "verified_certificates": sum(1 for check in checks if check["checker_status"] == OBSTRUCTION_DUAL_CERTIFICATE_VERIFIED),
        "recommendation_count": len(recommendations),
        "queue_count": len(queue),
        "strict": strict,
        "claim_boundary": "Obstruction-dual evidence only; no SAT/UNSAT, hardness, lower-bound, P vs NP, or hierarchy-completeness claim.",
    }
    outputs = {
        "obstruction_dual_certificates.json": {"certificates": certs},
        "obstruction_dual_checker_summary.json": {"checks": checks},
        "missing_operator_recommendations.json": {"recommendations": recommendations},
        "obstruction_to_operator_queue.json": {"queue": queue},
        "g7_obstruction_dual_summary.json": summary,
        "manifest.json": {
            "version": VERSION,
            "created_utc": datetime.now(timezone.utc).isoformat(),
            "grammar": G7_GRAMMAR,
            "statuses": [
                OBSTRUCTION_DUAL_STRUCTURE_DETECTED,
                OBSTRUCTION_DUAL_CERTIFICATE_VERIFIED,
                OBSTRUCTION_DUAL_CERTIFICATE_FAILED,
                NO_CERTIFIED_COLLAPSE_WITH_OBSTRUCTION,
                MISSING_OPERATOR_RECOMMENDED,
                OBSTRUCTION_TO_OPERATOR_QUEUE_CREATED,
                OBSTRUCTION_DUAL_DIAGNOSTIC_ONLY,
            ],
            "claim_boundary": summary["claim_boundary"],
        },
    }
    for name, payload in outputs.items():
        _write_json(root / name, payload)
    _write_text(root / "OBSTRUCTION_DUAL_CERTIFICATE_REPORT.md", obstruction_report(certs, checks, recommendations, queue))
    digest = make_zip(root, zip_path) if zip_path else ""
    return {
        "out_root": str(root),
        "zip": str(zip_path) if zip_path else "",
        "zip_sha256": digest,
        "obstruction_dual_certificates": certs,
        "obstruction_dual_checker_summary": checks,
        "missing_operator_recommendations": recommendations,
        "obstruction_to_operator_queue": queue,
        "g7_obstruction_dual_summary": summary,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build/check v2.14 obstruction-dual certificates")
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run")
    run.add_argument(
        "--families",
        nargs="+",
        default=[
            "no-confident-fingerprint",
            "random-structured",
            "near-affine",
            "near-cardinality",
            "graph-separator",
            "circuit-sat-toy",
            "proof-motif-near-miss",
            "mixed",
        ],
    )
    run.add_argument("--out-root", default="outputs/v2.14-obstruction-dual-certificate")
    run.add_argument("--zip", default="witnora-core-v2.14-obstruction-dual-certificate.zip")
    run.add_argument("--strict", action="store_true")
    check = sub.add_parser("check")
    check.add_argument("--cnf", required=True)
    check.add_argument("--certificate", required=True)
    args = parser.parse_args(argv)
    if args.command == "run":
        result = run_obstruction_dual_lab(families=args.families, out_root=args.out_root, strict=args.strict, zip_path=args.zip)
        print(
            stable_json(
                {
                    "out_root": result["out_root"],
                    "zip": result["zip"],
                    "zip_sha256": result["zip_sha256"],
                    "summary": result["g7_obstruction_dual_summary"],
                }
            )
        )
        return 0
    if args.command == "check":
        formula = load_dimacs(args.cnf)
        certificate = json.loads(Path(args.certificate).read_text(encoding="utf-8"))
        result = check_obstruction_dual_certificate(formula, certificate)
        print(stable_json(result))
        return 0 if result["checker_status"] == OBSTRUCTION_DUAL_CERTIFICATE_VERIFIED else 1
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
