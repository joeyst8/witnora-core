"""Finite empirical edge-delta certificates for hierarchy edges.

v2.11 generalizes the finite certificate machinery without weakening the word
strictness.  A lower-grammar replay that returns bounded no-collapse evidence
is not a lower-bound proof, so the G1->G2 certificate uses
FINITE_EMPIRICAL_EDGE_DELTA_CERTIFIED rather than FINITE_STRICTNESS_CERTIFIED.
"""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import asdict, dataclass
from hashlib import sha256
from pathlib import Path
from typing import Any, Iterable

from .cnf import CNFFormula, formula_satisfied
from .collapse_theory import (
    SAT_ASSIGNMENT_VERIFIED,
    SYMMETRY_SAT_WITNESS_RECONSTRUCTED,
    TheoryInstance,
    build_symmetry_certificate,
    check_symmetry_certificate,
)
from .strictness_proof import make_zip, stable_json
from .xor import detect_cnf_xor_patterns


FINITE_EDGE_DELTA_CERTIFICATE = "FINITE_EDGE_DELTA_CERTIFICATE"
FINITE_EDGE_DELTA_CERTIFICATE_VERIFIED = "FINITE_EDGE_DELTA_CERTIFICATE_VERIFIED"
FINITE_EDGE_DELTA_CERTIFICATE_FAILED = "FINITE_EDGE_DELTA_CERTIFICATE_FAILED"
FINITE_EMPIRICAL_EDGE_DELTA_CERTIFIED = "FINITE_EMPIRICAL_EDGE_DELTA_CERTIFIED"
FINITE_STRICTNESS_CERTIFIED = "FINITE_STRICTNESS_CERTIFIED"
FINITE = "FINITE"

LOWER_BOUND_CERTIFIED = "LOWER_BOUND_CERTIFIED"
LOWER_REPLAY_NO_COLLAPSE = "LOWER_REPLAY_NO_COLLAPSE"
UPPER_CERTIFIED = "UPPER_CERTIFIED"
NO_COLLAPSE_FOUND = "NO_COLLAPSE_FOUND"
NO_XOR_STRUCTURE_DETECTED = "NO_XOR_STRUCTURE_DETECTED"
NOT_A_DELTA = "NOT_A_DELTA"
NOT_CLAIMED = "NOT_CLAIMED"
PROOF_OBLIGATION = "PROOF_OBLIGATION"

G1_XOR = "G1_XOR"
G2_SYMMETRY_CERTIFIED = "G2_SYMMETRY_CERTIFIED"
G2_SYMMETRY_CERTIFICATE_VERIFIED = "G2_SYMMETRY_CERTIFICATE_VERIFIED"
G2_SYMMETRY_WITNESS_RECONSTRUCTION = "G2_SYMMETRY_WITNESS_RECONSTRUCTION"

DEFAULT_EDGE = f"{G1_XOR}:{G2_SYMMETRY_CERTIFIED}"
DEFAULT_EDGE_INSTANCES = (
    "cycle_4_3color",
    "cycle_6_3color",
    "cycle_8_3color",
    "cycle_10_3color",
)
LOWER_SOLVES_CONTROL = "lower_solves_control"


@dataclass(frozen=True)
class InstanceEdgeDeltaRecord:
    instance_id: str
    formula_hash: str
    family: str
    lower_result: dict[str, Any]
    upper_result: dict[str, Any]
    instance_checker_status: str
    claim_boundary: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class FiniteEdgeDeltaCertificate:
    type: str
    certificate_id: str
    lower_grammar: str
    upper_grammar: str
    bound_profile: dict[str, Any]
    claim_scope: str
    evidence_grade: str
    instances: list[dict[str, Any]]
    lower_evidence: list[dict[str, Any]]
    upper_evidence: list[dict[str, Any]]
    checker_status: str
    forbidden_interpretations: list[str]
    family_theorem_status: str
    strictness_theorem_status: str
    excluded_instances: list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class FiniteEdgeDeltaCheckerResult:
    certificate_id: str
    checked_instances: int
    passed_instances: list[str]
    failed_instances: list[str]
    checker_status: str
    evidence_grade: str
    errors: list[str]
    warnings: list[str]
    claim_boundary: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(stable_json(data) + "\n", encoding="utf-8", newline="\n")


def _cycle_edges(vertices: int) -> list[tuple[int, int]]:
    return [(idx, idx + 1) for idx in range(1, vertices)] + [(vertices, 1)]


def _graph_coloring_var(vertex: int, color: int, colors: int) -> int:
    return (vertex - 1) * colors + color


def _graph_coloring_formula(vertices: int, edges: Iterable[tuple[int, int]], colors: int) -> CNFFormula:
    clauses: list[list[int]] = []
    for vertex in range(1, vertices + 1):
        clauses.append([_graph_coloring_var(vertex, color, colors) for color in range(1, colors + 1)])
        for color_a in range(1, colors + 1):
            for color_b in range(color_a + 1, colors + 1):
                clauses.append(
                    [
                        -_graph_coloring_var(vertex, color_a, colors),
                        -_graph_coloring_var(vertex, color_b, colors),
                    ]
                )
    for left, right in edges:
        for color in range(1, colors + 1):
            clauses.append(
                [
                    -_graph_coloring_var(left, color, colors),
                    -_graph_coloring_var(right, color, colors),
                ]
            )
    return CNFFormula.from_raw_clauses(clauses)


def cycle_coloring_instance(instance_id: str) -> TheoryInstance:
    if not instance_id.startswith("cycle_") or not instance_id.endswith("_3color"):
        raise ValueError(f"unsupported finite edge-delta instance: {instance_id}")
    parts = instance_id.split("_")
    vertices = int(parts[1])
    colors = 3
    return TheoryInstance(
        instance_id=instance_id,
        family="graph-coloring",
        formula=_graph_coloring_formula(vertices, _cycle_edges(vertices), colors),
        source="built_in_finite_edge_delta_cycle_coloring",
        notes=f"symmetric 3-coloring encoding for a {vertices}-cycle graph",
    )


def finite_edge_bound_profile() -> dict[str, Any]:
    return {
        "name": "V2_11_G1_G2_FINITE_EMPIRICAL_EDGE_DELTA_PROFILE",
        "lower_grammar": G1_XOR,
        "upper_grammar": G2_SYMMETRY_CERTIFIED,
        "claim_scope": FINITE,
        "lower_evidence_type": LOWER_REPLAY_NO_COLLAPSE,
        "upper_evidence_type": UPPER_CERTIFIED,
        "xor_max_k": 6,
        "symmetry_certificate_required": True,
        "sat_assignment_verification_required": True,
        "lower_bound_claim": "not claimed",
        "family_theorem_status": NOT_CLAIMED,
        "strictness_theorem_status": PROOF_OBLIGATION,
    }


def replay_lower_g1(instance: TheoryInstance) -> dict[str, Any]:
    system = detect_cnf_xor_patterns(instance.formula, include_3var=True, max_k=6)
    equations = [equation.to_dict() for equation in system.equations]
    if equations:
        return {
            "grammar": G1_XOR,
            "replay_status": NOT_A_DELTA,
            "public_category": SAT_ASSIGNMENT_VERIFIED,
            "bound_profile": finite_edge_bound_profile(),
            "evidence_type": UPPER_CERTIFIED,
            "lower_bound_certificate": None,
            "detected_equations": equations,
            "claim_boundary": "Lower grammar accepted or found affine structure; this row is not counted as a G1->G2 empirical delta.",
        }
    return {
        "grammar": G1_XOR,
        "replay_status": LOWER_REPLAY_NO_COLLAPSE,
        "public_category": NO_COLLAPSE_FOUND,
        "bound_profile": finite_edge_bound_profile(),
        "evidence_type": LOWER_REPLAY_NO_COLLAPSE,
        "lower_bound_certificate": None,
        "diagnostic": NO_XOR_STRUCTURE_DETECTED,
        "detected_equations": [],
        "claim_boundary": "Bounded replay non-acceptance only; not a lower-bound proof and not non-membership.",
    }


def replay_upper_g2(instance: TheoryInstance) -> dict[str, Any]:
    certificate = build_symmetry_certificate(instance)
    check = check_symmetry_certificate(instance.formula, certificate)
    assignment = {int(var): bool(value) for var, value in certificate.lifted_assignment.items()}
    witness_ok = bool(assignment) and formula_satisfied(instance.formula, assignment)
    verified = (
        certificate.status == SYMMETRY_SAT_WITNESS_RECONSTRUCTED
        and certificate.checker_status == "PASS"
        and check["checker_status"] == "PASS"
        and witness_ok
    )
    return {
        "grammar": G2_SYMMETRY_CERTIFIED,
        "replay_status": SYMMETRY_SAT_WITNESS_RECONSTRUCTED if verified else "G2_SYMMETRY_REPLAY_FAILED",
        "public_category": SAT_ASSIGNMENT_VERIFIED if verified else NO_COLLAPSE_FOUND,
        "certificate_type": G2_SYMMETRY_WITNESS_RECONSTRUCTION,
        "checker_status": G2_SYMMETRY_CERTIFICATE_VERIFIED if verified else "G2_SYMMETRY_CERTIFICATE_FAILED",
        "witness_or_certificate_verified": verified,
        "symmetry_certificate": certificate.to_dict(),
        "symmetry_checker": check,
        "assignment_satisfies_original_cnf": witness_ok,
        "claim_boundary": "G2 upper evidence is a checked native symmetry SAT witness reconstruction, not DRAT.",
    }


def candidate_edge_delta_record(instance_id: str) -> InstanceEdgeDeltaRecord:
    if instance_id == LOWER_SOLVES_CONTROL:
        instance = cycle_coloring_instance("cycle_4_3color")
        lower = replay_lower_g1(instance) | {
            "replay_status": "LOWER_SOLVES_CONTROL",
            "public_category": SAT_ASSIGNMENT_VERIFIED,
            "evidence_type": UPPER_CERTIFIED,
            "claim_boundary": "Control row: if the lower grammar solves, the row is not a delta.",
        }
        upper = replay_upper_g2(instance)
        return InstanceEdgeDeltaRecord(
            instance_id=instance_id,
            formula_hash=instance.formula.formula_hash,
            family=instance.family,
            lower_result=lower,
            upper_result=upper,
            instance_checker_status=NOT_A_DELTA,
            claim_boundary="control row only; lower grammar acceptance prevents edge-delta certification",
        )

    instance = cycle_coloring_instance(instance_id)
    lower = replay_lower_g1(instance)
    upper = replay_upper_g2(instance)
    status = (
        FINITE_EMPIRICAL_EDGE_DELTA_CERTIFIED
        if lower["evidence_type"] == LOWER_REPLAY_NO_COLLAPSE and upper["witness_or_certificate_verified"]
        else NOT_A_DELTA
    )
    return InstanceEdgeDeltaRecord(
        instance_id=instance_id,
        formula_hash=instance.formula.formula_hash,
        family=instance.family,
        lower_result=lower,
        upper_result=upper,
        instance_checker_status=status,
        claim_boundary="finite empirical edge delta only; not a lower-bound strictness theorem and not a family theorem",
    )


def _certificate_id(records: list[dict[str, Any]]) -> str:
    payload = {
        "type": FINITE_EDGE_DELTA_CERTIFICATE,
        "lower_grammar": G1_XOR,
        "upper_grammar": G2_SYMMETRY_CERTIFIED,
        "claim_scope": FINITE,
        "evidence_grade": FINITE_EMPIRICAL_EDGE_DELTA_CERTIFIED,
        "instances": [record["instance_id"] for record in records],
        "hashes": [record["formula_hash"] for record in records],
    }
    return "FED-" + sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest().upper()[:16]


def build_finite_edge_delta_certificate(
    *,
    edge: str = DEFAULT_EDGE,
    instances: Iterable[str] = DEFAULT_EDGE_INSTANCES,
) -> FiniteEdgeDeltaCertificate:
    if edge != DEFAULT_EDGE:
        raise ValueError(f"unsupported finite edge-delta edge: {edge}")
    certified_records: list[InstanceEdgeDeltaRecord] = []
    excluded: list[dict[str, Any]] = []
    for instance_id in instances:
        record = candidate_edge_delta_record(instance_id)
        if record.instance_checker_status == FINITE_EMPIRICAL_EDGE_DELTA_CERTIFIED:
            certified_records.append(record)
        else:
            excluded.append(
                {
                    "instance_id": instance_id,
                    "status": NOT_A_DELTA,
                    "reason": "lower grammar accepted or upper grammar failed verification",
                    "claim_boundary": "Excluded rows are not counted as finite empirical edge deltas.",
                }
            )
    record_dicts = [record.to_dict() for record in certified_records]
    all_pass = bool(record_dicts) and len(excluded) == 0
    return FiniteEdgeDeltaCertificate(
        type=FINITE_EDGE_DELTA_CERTIFICATE,
        certificate_id=_certificate_id(record_dicts),
        lower_grammar=G1_XOR,
        upper_grammar=G2_SYMMETRY_CERTIFIED,
        bound_profile=finite_edge_bound_profile(),
        claim_scope=FINITE,
        evidence_grade=FINITE_EMPIRICAL_EDGE_DELTA_CERTIFIED,
        instances=record_dicts,
        lower_evidence=[record["lower_result"] for record in record_dicts],
        upper_evidence=[record["upper_result"] for record in record_dicts],
        checker_status=FINITE_EDGE_DELTA_CERTIFICATE_VERIFIED if all_pass else FINITE_EDGE_DELTA_CERTIFICATE_FAILED,
        forbidden_interpretations=[
            "not lower-bound strictness",
            "not full G1-vs-G2 theorem",
            "not family theorem",
            "not hierarchy completeness",
            "not P vs NP progress",
            "native certificates are not DRAT",
        ],
        family_theorem_status=NOT_CLAIMED,
        strictness_theorem_status=PROOF_OBLIGATION,
        excluded_instances=excluded,
    )


def _status_values(obj: Any) -> Iterable[str]:
    if isinstance(obj, dict):
        for key, value in obj.items():
            key_text = str(key)
            if key_text.endswith("status") or key_text in {"status", "checker_status", "evidence_grade"}:
                if isinstance(value, str):
                    yield value
            yield from _status_values(value)
    elif isinstance(obj, list):
        for item in obj:
            yield from _status_values(item)


def _load_certificate(certificate: str | Path | dict[str, Any]) -> dict[str, Any]:
    if isinstance(certificate, dict):
        return certificate
    return json.loads(Path(certificate).read_text(encoding="utf-8"))


def check_finite_edge_delta_certificate(certificate: str | Path | dict[str, Any]) -> FiniteEdgeDeltaCheckerResult:
    cert = _load_certificate(certificate)
    errors: list[str] = []
    warnings: list[str] = []
    passed: list[str] = []
    failed: list[str] = []

    if cert.get("type") != FINITE_EDGE_DELTA_CERTIFICATE:
        errors.append("certificate type is not FINITE_EDGE_DELTA_CERTIFICATE")
    if cert.get("lower_grammar") != G1_XOR:
        errors.append("lower_grammar must be G1_XOR")
    if cert.get("upper_grammar") != G2_SYMMETRY_CERTIFIED:
        errors.append("upper_grammar must be G2_SYMMETRY_CERTIFIED")
    if cert.get("claim_scope") != FINITE:
        errors.append("claim_scope must be FINITE")
    if cert.get("evidence_grade") != FINITE_EMPIRICAL_EDGE_DELTA_CERTIFIED:
        errors.append("G1->G2 certificate must use FINITE_EMPIRICAL_EDGE_DELTA_CERTIFIED")
    if cert.get("family_theorem_status") != NOT_CLAIMED:
        errors.append("family theorem must not be claimed")
    if cert.get("strictness_theorem_status") != PROOF_OBLIGATION:
        errors.append("strictness theorem must remain a proof obligation")

    forbidden_text = json.dumps(cert, sort_keys=True)
    for forbidden in [
        "G1_XOR lower bound proven",
        "G1_XOR strictly weaker than G2 as a theorem",
        "family theorem proven",
        "hierarchy completeness is proven",
        "proves P vs NP",
        "FINITE_STRICTNESS_CERTIFIED",
    ]:
        if forbidden in forbidden_text and forbidden != cert.get("evidence_grade"):
            errors.append(f"forbidden claim present: {forbidden}")
    statuses = list(_status_values(cert))
    if "HARD" in statuses or "UNKNOWN" in statuses:
        errors.append("HARD/UNKNOWN status is forbidden")

    for record in cert.get("instances", []):
        instance_id = str(record.get("instance_id", ""))
        try:
            instance = cycle_coloring_instance(instance_id)
            lower = replay_lower_g1(instance)
            upper = replay_upper_g2(instance)
            if record.get("formula_hash") != instance.formula.formula_hash:
                raise ValueError("formula hash mismatch")
            stored_lower = record.get("lower_result", {})
            stored_upper = record.get("upper_result", {})
            lower_ok = (
                stored_lower.get("evidence_type") == LOWER_REPLAY_NO_COLLAPSE
                and stored_lower.get("replay_status") == LOWER_REPLAY_NO_COLLAPSE
                and stored_lower.get("public_category") == NO_COLLAPSE_FOUND
                and stored_lower.get("lower_bound_certificate") is None
                and lower["evidence_type"] == LOWER_REPLAY_NO_COLLAPSE
            )
            upper_ok = (
                stored_upper.get("checker_status") == G2_SYMMETRY_CERTIFICATE_VERIFIED
                and stored_upper.get("witness_or_certificate_verified") is True
                and stored_upper.get("public_category") == SAT_ASSIGNMENT_VERIFIED
                and upper["witness_or_certificate_verified"] is True
            )
            if record.get("instance_checker_status") != FINITE_EMPIRICAL_EDGE_DELTA_CERTIFIED:
                raise ValueError("instance status is not finite empirical edge delta certified")
            if lower_ok and upper_ok:
                passed.append(instance_id)
            else:
                failed.append(instance_id)
                errors.append(f"instance replay failed: {instance_id}")
        except Exception as exc:  # noqa: BLE001 - checker reports structured failures.
            failed.append(instance_id)
            errors.append(f"instance replay failed: {instance_id}: {exc}")

    for exclusion in cert.get("excluded_instances", []):
        warnings.append(f"excluded non-delta instance: {exclusion.get('instance_id')}")

    checker_status = (
        FINITE_EDGE_DELTA_CERTIFICATE_VERIFIED
        if not errors and len(passed) == len(cert.get("instances", []))
        else FINITE_EDGE_DELTA_CERTIFICATE_FAILED
    )
    return FiniteEdgeDeltaCheckerResult(
        certificate_id=str(cert.get("certificate_id", "")),
        checked_instances=len(cert.get("instances", [])),
        passed_instances=passed,
        failed_instances=failed,
        checker_status=checker_status,
        evidence_grade=FINITE_EMPIRICAL_EDGE_DELTA_CERTIFIED,
        errors=errors,
        warnings=warnings,
        claim_boundary="finite empirical replay delta only; not lower-bound strictness, not a family theorem, not P vs NP progress",
    )


def finite_edge_delta_report(*, certificate: dict[str, Any], checker_result: dict[str, Any]) -> str:
    lines = [
        "# Finite Empirical Edge Delta Certificate: G1 -> G2",
        "",
        "v2.11 records a finite replayed delta for `G1_XOR` versus `G2_SYMMETRY_CERTIFIED`.",
        "",
        "`FINITE_EMPIRICAL_EDGE_DELTA_CERTIFIED` records a finite replayed delta, not a lower-bound strictness theorem.",
        "Unlike v2.10's finite strictness certificate, v2.11 does not provide certified lower-bound obstruction for the lower grammar.",
        "The lower result is bounded replay evidence only.",
        "This does not prove `G1_XOR` is strictly weaker than `G2_SYMMETRY_CERTIFIED` as a theorem.",
        "This does not prove a family theorem.",
        "This does not prove P vs NP.",
        "",
        f"- Certificate id: `{certificate['certificate_id']}`",
        f"- Checker status: `{checker_result['checker_status']}`",
        f"- Evidence grade: `{certificate['evidence_grade']}`",
        f"- Lower grammar: `{certificate['lower_grammar']}`",
        f"- Upper grammar: `{certificate['upper_grammar']}`",
        "",
        "## Certified Finite Instances",
        "",
    ]
    for record in certificate["instances"]:
        lines.extend(
            [
                f"### {record['instance_id']}",
                "",
                f"- Family: `{record['family']}`",
                f"- Formula hash: `{record['formula_hash']}`",
                f"- Lower replay: `{record['lower_result']['replay_status']}` / `{record['lower_result']['public_category']}`",
                f"- Lower evidence: `{record['lower_result']['evidence_type']}`",
                f"- Upper replay: `{record['upper_result']['replay_status']}`",
                f"- Upper checker: `{record['upper_result']['checker_status']}`",
                f"- Instance status: `{record['instance_checker_status']}`",
                "",
            ]
        )
    lines.extend(
        [
            "## Claim Boundary",
            "",
            "- Lower replay is not called a lower-bound proof.",
            "- No G1-vs-G2 family theorem claim.",
            "- No hierarchy completeness claim.",
            "- No P vs NP progress claim.",
            "- Native symmetry certificates are not DRAT.",
            "",
        ]
    )
    return "\n".join(lines)


def theorem_candidate_updates(certificate: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "id": "TC-034",
            "name": "Finite G1-to-G2 Empirical Edge Delta Certificate",
            "statement": (
                "For the finite checked instance set I, each F in I is not accepted by G1_XOR "
                "under the configured bound profile during replay, while G2_SYMMETRY_CERTIFIED "
                "verifies a SAT witness reconstruction."
            ),
            "status": FINITE_EMPIRICAL_EDGE_DELTA_CERTIFIED,
            "supporting_witnesses": [record["instance_id"] for record in certificate["instances"]],
            "forbidden_interpretations": certificate["forbidden_interpretations"],
        },
        {
            "id": "TC-035",
            "name": "G1-to-G2 Symmetry Strictness Candidate",
            "status": PROOF_OBLIGATION,
            "supporting_witnesses": ["cycle graph coloring symmetry family"],
            "forbidden_interpretations": [
                "not lower-bound strictness",
                "not a G1-vs-G2 family theorem",
                "not P vs NP progress",
            ],
        },
    ]


def build_outputs(
    *,
    edge: str = DEFAULT_EDGE,
    instances: Iterable[str] = DEFAULT_EDGE_INSTANCES,
    out_root: str | Path = "outputs/v2.11-finite-edge-delta-g1-g2",
    strict: bool = False,
    zip_path: str | Path = "witnora-core-v2.11-finite-edge-delta-g1-g2.zip",
) -> dict[str, Any]:
    root = Path(out_root)
    root.mkdir(parents=True, exist_ok=True)
    cert = build_finite_edge_delta_certificate(edge=edge, instances=instances)
    checker = check_finite_edge_delta_certificate(cert.to_dict())
    cert_dict = cert.to_dict() | {"checker_status": checker.checker_status}
    checker_dict = checker.to_dict()
    payloads = {
        "finite_edge_delta_certificate.json": cert_dict,
        "finite_edge_delta_checker_result.json": checker_dict,
        "instance_edge_delta_records.json": {"instance_edge_delta_records": cert_dict["instances"]},
        "lower_g1_replay_summary.json": {
            "lower_g1_replay_summary": [
                {
                    "instance_id": record["instance_id"],
                    "replay_status": record["lower_result"]["replay_status"],
                    "public_category": record["lower_result"]["public_category"],
                    "evidence_type": record["lower_result"]["evidence_type"],
                    "lower_bound_certificate": record["lower_result"]["lower_bound_certificate"],
                }
                for record in cert_dict["instances"]
            ]
        },
        "upper_g2_replay_summary.json": {
            "upper_g2_replay_summary": [
                {
                    "instance_id": record["instance_id"],
                    "replay_status": record["upper_result"]["replay_status"],
                    "public_category": record["upper_result"]["public_category"],
                    "checker_status": record["upper_result"]["checker_status"],
                    "witness_or_certificate_verified": record["upper_result"]["witness_or_certificate_verified"],
                }
                for record in cert_dict["instances"]
            ]
        },
        "edge_delta_claim_boundary.json": {
            "claim_scope": FINITE,
            "evidence_grade": FINITE_EMPIRICAL_EDGE_DELTA_CERTIFIED,
            "lower_replay_is_lower_bound": False,
            "family_theorem_status": NOT_CLAIMED,
            "strictness_theorem_status": PROOF_OBLIGATION,
            "no_p_vs_np_claim": True,
            "native_certificates_are_not_drat": True,
        },
        "theorem_candidate_updates.json": {"theorem_candidate_updates": theorem_candidate_updates(cert_dict)},
    }
    for name, payload in payloads.items():
        _write_json(root / name, payload)
    with (root / "finite_edge_delta_summary.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "instance_id",
                "family",
                "lower_grammar",
                "lower_replay_status",
                "lower_evidence_type",
                "upper_grammar",
                "upper_checker_status",
                "instance_checker_status",
            ],
        )
        writer.writeheader()
        for record in cert_dict["instances"]:
            writer.writerow(
                {
                    "instance_id": record["instance_id"],
                    "family": record["family"],
                    "lower_grammar": cert_dict["lower_grammar"],
                    "lower_replay_status": record["lower_result"]["replay_status"],
                    "lower_evidence_type": record["lower_result"]["evidence_type"],
                    "upper_grammar": cert_dict["upper_grammar"],
                    "upper_checker_status": record["upper_result"]["checker_status"],
                    "instance_checker_status": record["instance_checker_status"],
                }
            )
    (root / "FINITE_EDGE_DELTA_G1_G2_REPORT.md").write_text(
        finite_edge_delta_report(certificate=cert_dict, checker_result=checker_dict),
        encoding="utf-8",
        newline="\n",
    )
    digest = make_zip(root, zip_path) if zip_path else ""
    return {
        "out_root": str(root),
        "zip": str(zip_path) if zip_path else "",
        "zip_sha256": digest,
        "strict": strict,
        "finite_edge_delta_certificate": cert_dict,
        "finite_edge_delta_checker_result": checker_dict,
        "instance_edge_delta_records": cert_dict["instances"],
        "theorem_candidate_updates": theorem_candidate_updates(cert_dict),
    }


def check_command(*, certificate_path: str | Path, out_root: str | Path) -> dict[str, Any]:
    root = Path(out_root)
    root.mkdir(parents=True, exist_ok=True)
    result = check_finite_edge_delta_certificate(certificate_path)
    _write_json(root / "finite_edge_delta_checker_result.json", result.to_dict())
    return {"out_root": str(root), "finite_edge_delta_checker_result": result.to_dict()}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build/check finite empirical edge-delta certificates")
    sub = parser.add_subparsers(dest="command", required=True)
    build = sub.add_parser("build")
    build.add_argument("--edge", default=DEFAULT_EDGE)
    build.add_argument("--instances", nargs="+", default=list(DEFAULT_EDGE_INSTANCES))
    build.add_argument("--out-root", default="outputs/v2.11-finite-edge-delta-g1-g2")
    build.add_argument("--strict", action="store_true")
    build.add_argument("--zip", default="witnora-core-v2.11-finite-edge-delta-g1-g2.zip")
    check = sub.add_parser("check")
    check.add_argument("--certificate", required=True)
    check.add_argument("--out-root", default="outputs/v2.11-finite-edge-delta-g1-g2/check")
    check.add_argument("--strict", action="store_true")
    args = parser.parse_args(argv)
    if args.command == "build":
        result = build_outputs(
            edge=args.edge,
            instances=args.instances,
            out_root=args.out_root,
            strict=args.strict,
            zip_path=args.zip,
        )
        print(
            stable_json(
                {
                    "out_root": result["out_root"],
                    "zip": result["zip"],
                    "zip_sha256": result["zip_sha256"],
                    "checker_status": result["finite_edge_delta_checker_result"]["checker_status"],
                    "evidence_grade": result["finite_edge_delta_certificate"]["evidence_grade"],
                    "certified_instances": [record["instance_id"] for record in result["instance_edge_delta_records"]],
                }
            )
        )
        return 0
    if args.command == "check":
        result = check_command(certificate_path=args.certificate, out_root=args.out_root)
        print(stable_json(result["finite_edge_delta_checker_result"]))
        return 0 if result["finite_edge_delta_checker_result"]["checker_status"] == FINITE_EDGE_DELTA_CERTIFICATE_VERIFIED else 1
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
