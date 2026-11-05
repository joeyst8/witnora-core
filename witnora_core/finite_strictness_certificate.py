"""Finite strictness certificates for restricted G0_WIDTH_C vs G1_XOR.

v2.10 packages the v2.9 strictness proof kernel as a reusable finite
certificate. The certificate is deliberately finite and restricted. It does not
claim full G0_BASE strictness, a scalable family theorem, hierarchy
completeness, or P vs NP progress.
"""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable

from .strictness_proof import (
    FAILED_PROOF_OBLIGATION,
    FULL_G0_STRICTNESS_NOT_CLAIMED,
    G1_XOR_UPPER_BOUND_VERIFIED,
    RESTRICTED_G0_WIDTH_ROUTE_REJECTED,
    SCALABLE_FAMILY_PROOF_OBLIGATION,
    WIDTH_OBSTRUCTION_VERIFIED,
    build_width_obstruction_certificate,
    build_xor_upper_bound_certificate,
    make_zip,
    proof_obligation_updates,
    restricted_grammar_definitions,
    sha256_file,
    stable_json,
    strictness_witness_formula,
)


FINITE_STRICTNESS_CERTIFICATE = "FINITE_STRICTNESS_CERTIFICATE"
FINITE_STRICTNESS_CERTIFICATE_VERIFIED = "FINITE_STRICTNESS_CERTIFICATE_VERIFIED"
FINITE_STRICTNESS_CERTIFIED = "FINITE_STRICTNESS_CERTIFIED"
FINITE_STRICTNESS_CERTIFICATE_FAILED = "FINITE_STRICTNESS_CERTIFICATE_FAILED"
FINITE_STRICTNESS_PROOF_SKETCH_ONLY = "FINITE_STRICTNESS_PROOF_SKETCH_ONLY"
FINITE = "FINITE"
G0_WIDTH_C = "G0_WIDTH_C"
G1_XOR_FOR_STRICTNESS = "G1_XOR_FOR_STRICTNESS"
NOT_CLAIMED = "NOT_CLAIMED"
NOT_INCLUDED_RESOURCE_CAP = "NOT_INCLUDED_RESOURCE_CAP"
WIDTH_CERTIFICATION_NOT_ATTEMPTED = "WIDTH_CERTIFICATION_NOT_ATTEMPTED"

DEFAULT_FINITE_INSTANCES = (
    "tseitin_10",
    "xor_chain_unsat_n5",
    "tseitin_12",
    "xor_chain_unsat_n7",
    "tseitin_14",
    "xor_chain_unsat_n9",
)
RESOURCE_LIMITED_INSTANCE_IDS = {
    "tseitin_30",
    "tseitin_expander_candidate",
    "xor_chain_unsat_n30",
}


@dataclass(frozen=True)
class InstanceStrictnessRecord:
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
class FiniteStrictnessCertificate:
    type: str
    certificate_id: str
    lower_grammar: str
    upper_grammar: str
    bound_profile: dict[str, Any]
    cap_c: int
    claim_scope: str
    instances: list[dict[str, Any]]
    lower_bound_evidence: list[dict[str, Any]]
    upper_bound_evidence: list[dict[str, Any]]
    checker_status: str
    strictness_status: str
    forbidden_interpretations: list[str]
    scalable_family_status: str
    resource_exclusions: list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class FiniteStrictnessCheckerResult:
    certificate_id: str
    checked_instances: int
    passed_instances: list[str]
    failed_instances: list[str]
    checker_status: str
    errors: list[str]
    warnings: list[str]
    claim_boundary: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(stable_json(data) + "\n", encoding="utf-8", newline="\n")


def _certificate_hash_payload(
    *, instances: list[dict[str, Any]], cap_c: int, resource_exclusions: list[dict[str, Any]]
) -> str:
    payload = {
        "type": FINITE_STRICTNESS_CERTIFICATE,
        "lower_grammar": G0_WIDTH_C,
        "upper_grammar": G1_XOR_FOR_STRICTNESS,
        "cap_c": cap_c,
        "claim_scope": FINITE,
        "instances": instances,
        "resource_exclusions": resource_exclusions,
    }
    import hashlib

    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest().upper()


def bound_profile(cap_c: int) -> dict[str, Any]:
    return {
        "name": "V2_10_RESTRICTED_G0_G1_FINITE_BOUND_PROFILE",
        "cap_c": cap_c,
        "width_route": G0_WIDTH_C,
        "upper_route": G1_XOR_FOR_STRICTNESS,
        "claim_scope": FINITE,
        "native_certificate_allowed": True,
        "drat_required": False,
        "full_g0_base_claim": FULL_G0_STRICTNESS_NOT_CLAIMED,
        "scalable_family_status": SCALABLE_FAMILY_PROOF_OBLIGATION,
    }


def _resource_exclusion(instance_id: str) -> dict[str, Any]:
    return {
        "instance_id": instance_id,
        "status": NOT_INCLUDED_RESOURCE_CAP,
        "reason": WIDTH_CERTIFICATION_NOT_ATTEMPTED,
        "claim_boundary": "Excluded instances are not counted toward FINITE_STRICTNESS_CERTIFIED.",
    }


def _instance_record(instance_id: str, cap_c: int) -> InstanceStrictnessRecord:
    family, formula, description = strictness_witness_formula(instance_id)
    width = build_width_obstruction_certificate(formula, instance_id=instance_id, cap_c=cap_c)
    xor = build_xor_upper_bound_certificate(formula, instance_id=instance_id)
    lower_ok = (
        width.checker_status == WIDTH_OBSTRUCTION_VERIFIED
        and (width.certified_lower_bound or 0) > cap_c
    )
    upper_ok = xor.checker_status == G1_XOR_UPPER_BOUND_VERIFIED and xor.extraction_verified
    instance_status = FINITE_STRICTNESS_CERTIFIED if lower_ok and upper_ok else FINITE_STRICTNESS_CERTIFICATE_FAILED
    return InstanceStrictnessRecord(
        instance_id=instance_id,
        formula_hash=formula.formula_hash,
        family=family,
        lower_result={
            "width_obstruction_certificate": width.to_dict() | {"description": description},
            "certified_lower_bound": width.certified_lower_bound,
            "cap_c": cap_c,
            "restricted_route_result": RESTRICTED_G0_WIDTH_ROUTE_REJECTED if lower_ok else FAILED_PROOF_OBLIGATION,
        },
        upper_result={
            "xor_upper_bound_certificate": xor.to_dict(),
            "extraction_verified": xor.extraction_verified,
            "sat_or_unsat_result": xor.sat_or_unsat_result,
            "certification_level": xor.certification_level,
        },
        instance_checker_status=instance_status,
        claim_boundary="finite restricted G0_WIDTH_C vs G1_XOR_FOR_STRICTNESS instance only; not a family theorem",
    )


def build_finite_strictness_certificate(
    *,
    instances: Iterable[str] = DEFAULT_FINITE_INSTANCES,
    cap_c: int = 4,
) -> FiniteStrictnessCertificate:
    records: list[InstanceStrictnessRecord] = []
    resource_exclusions: list[dict[str, Any]] = []
    for instance_id in instances:
        if instance_id in RESOURCE_LIMITED_INSTANCE_IDS or instance_id.endswith("_resource_cap"):
            resource_exclusions.append(_resource_exclusion(instance_id))
            continue
        records.append(_instance_record(instance_id, cap_c))
    instance_dicts = [record.to_dict() for record in records]
    lower_bound_evidence = [record.lower_result for record in records]
    upper_bound_evidence = [record.upper_result for record in records]
    all_pass = bool(records) and all(record.instance_checker_status == FINITE_STRICTNESS_CERTIFIED for record in records)
    certificate_id = "FSC-" + _certificate_hash_payload(
        instances=instance_dicts,
        cap_c=cap_c,
        resource_exclusions=resource_exclusions,
    )[:16]
    return FiniteStrictnessCertificate(
        type=FINITE_STRICTNESS_CERTIFICATE,
        certificate_id=certificate_id,
        lower_grammar=G0_WIDTH_C,
        upper_grammar=G1_XOR_FOR_STRICTNESS,
        bound_profile=bound_profile(cap_c),
        cap_c=cap_c,
        claim_scope=FINITE,
        instances=instance_dicts,
        lower_bound_evidence=lower_bound_evidence,
        upper_bound_evidence=upper_bound_evidence,
        checker_status=FINITE_STRICTNESS_CERTIFICATE_VERIFIED if all_pass else FINITE_STRICTNESS_CERTIFICATE_FAILED,
        strictness_status=FINITE_STRICTNESS_CERTIFIED if all_pass else FINITE_STRICTNESS_PROOF_SKETCH_ONLY,
        forbidden_interpretations=[
            "not full G0_BASE strictness",
            "not scalable family theorem",
            "not hierarchy strictness theorem",
            "not hierarchy completeness",
            "not P vs NP progress",
            "native certificates are not DRAT",
        ],
        scalable_family_status=SCALABLE_FAMILY_PROOF_OBLIGATION,
        resource_exclusions=resource_exclusions,
    )


def _status_values(obj: Any) -> Iterable[str]:
    if isinstance(obj, dict):
        for key, value in obj.items():
            if key.endswith("status") or key in {"status", "checker_status", "strictness_status"}:
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


def check_finite_strictness_certificate(certificate: str | Path | dict[str, Any]) -> FiniteStrictnessCheckerResult:
    cert = _load_certificate(certificate)
    errors: list[str] = []
    warnings: list[str] = []
    passed: list[str] = []
    failed: list[str] = []

    if cert.get("type") != FINITE_STRICTNESS_CERTIFICATE:
        errors.append("certificate type is not FINITE_STRICTNESS_CERTIFICATE")
    if cert.get("lower_grammar") != G0_WIDTH_C:
        errors.append("lower_grammar must be restricted G0_WIDTH_C")
    if cert.get("upper_grammar") != G1_XOR_FOR_STRICTNESS:
        errors.append("upper_grammar must be G1_XOR_FOR_STRICTNESS")
    if cert.get("claim_scope") != FINITE:
        errors.append("claim_scope must be FINITE")
    if cert.get("cap_c") is None:
        errors.append("cap_c is missing")
    if cert.get("strictness_status") not in {FINITE_STRICTNESS_CERTIFIED, FINITE_STRICTNESS_PROOF_SKETCH_ONLY}:
        errors.append("invalid finite strictness status")
    if cert.get("scalable_family_status") not in {SCALABLE_FAMILY_PROOF_OBLIGATION, NOT_CLAIMED}:
        errors.append("scalable family theorem must remain a proof obligation or not claimed")
    forbidden_text = json.dumps(cert, sort_keys=True)
    for forbidden in [
        "full G0_BASE strictness is proven",
        "scalable Tseitin family theorem is proven",
        "hierarchy completeness is proven",
        "proves P vs NP",
        "PROVEN_FAMILY_THEOREM",
    ]:
        if forbidden in forbidden_text:
            errors.append(f"forbidden claim present: {forbidden}")
    statuses = list(_status_values(cert))
    if "HARD" in statuses or "UNKNOWN" in statuses:
        errors.append("HARD/UNKNOWN status is forbidden")

    cap_c = int(cert.get("cap_c", -1))
    for record in cert.get("instances", []):
        instance_id = str(record.get("instance_id", ""))
        try:
            _, formula, _ = strictness_witness_formula(instance_id)
            if record.get("formula_hash") != formula.formula_hash:
                raise ValueError("formula hash mismatch")
            width = build_width_obstruction_certificate(formula, instance_id=instance_id, cap_c=cap_c)
            xor = build_xor_upper_bound_certificate(formula, instance_id=instance_id)
            lower = record.get("lower_result", {})
            upper = record.get("upper_result", {})
            lower_ok = (
                width.checker_status == WIDTH_OBSTRUCTION_VERIFIED
                and (width.certified_lower_bound or 0) > cap_c
                and lower.get("restricted_route_result") == RESTRICTED_G0_WIDTH_ROUTE_REJECTED
                and lower.get("certified_lower_bound") == width.certified_lower_bound
            )
            upper_ok = (
                xor.checker_status == G1_XOR_UPPER_BOUND_VERIFIED
                and xor.extraction_verified
                and upper.get("extraction_verified") is True
                and upper.get("sat_or_unsat_result") == xor.sat_or_unsat_result
            )
            if lower_ok and upper_ok:
                passed.append(instance_id)
            else:
                failed.append(instance_id)
                errors.append(f"instance replay failed: {instance_id}")
        except Exception as exc:  # noqa: BLE001 - checker returns structured failure.
            failed.append(instance_id)
            errors.append(f"instance replay failed: {instance_id}: {exc}")

    for exclusion in cert.get("resource_exclusions", []):
        if exclusion.get("status") != NOT_INCLUDED_RESOURCE_CAP:
            errors.append(f"resource exclusion has wrong status: {exclusion.get('instance_id')}")
        warnings.append(f"resource-limited instance excluded: {exclusion.get('instance_id')}")

    checker_status = FINITE_STRICTNESS_CERTIFICATE_VERIFIED if not errors and len(passed) == len(cert.get("instances", [])) else FINITE_STRICTNESS_CERTIFICATE_FAILED
    return FiniteStrictnessCheckerResult(
        certificate_id=str(cert.get("certificate_id", "")),
        checked_instances=len(cert.get("instances", [])),
        passed_instances=passed,
        failed_instances=failed,
        checker_status=checker_status,
        errors=errors,
        warnings=warnings,
        claim_boundary="finite checked instances only; not full G0_BASE strictness, not a scalable family theorem, not P vs NP progress",
    )


def finite_strictness_report(
    *,
    certificate: dict[str, Any],
    checker_result: dict[str, Any],
) -> str:
    lines = [
        "# Formal Finite Strictness Certificate",
        "",
        "v2.10 defines and checks a finite strictness certificate for restricted `G0_WIDTH_C` versus `G1_XOR_FOR_STRICTNESS`.",
        "",
        "`FINITE_STRICTNESS_CERTIFIED` is a machine-checked finite-instance certificate, not a scalable family theorem.",
        "This does not prove full `G0_BASE` strictness.",
        "This does not prove the hierarchy is strict.",
        "This does not prove P vs NP.",
        "Scalable Tseitin/expander strictness remains a proof obligation.",
        "",
        f"- Certificate id: `{certificate['certificate_id']}`",
        f"- Cap c: `{certificate['cap_c']}`",
        f"- Checker status: `{checker_result['checker_status']}`",
        f"- Strictness status: `{certificate['strictness_status']}`",
        "",
        "## Certified Finite Instances",
        "",
    ]
    for record in certificate["instances"]:
        lower = record["lower_result"]
        upper = record["upper_result"]
        lines.extend(
            [
                f"### {record['instance_id']}",
                "",
                f"- Family: `{record['family']}`",
                f"- Formula hash: `{record['formula_hash']}`",
                f"- Width lower bound: `{lower['certified_lower_bound']}`",
                f"- Restricted route: `{lower['restricted_route_result']}`",
                f"- G1 XOR result: `{upper['sat_or_unsat_result']}`",
                f"- G1 certification: `{upper['certification_level']}`",
                f"- Instance status: `{record['instance_checker_status']}`",
                "",
            ]
        )
    lines.extend(
        [
            "## Resource Exclusions",
            "",
        ]
    )
    if certificate["resource_exclusions"]:
        for exclusion in certificate["resource_exclusions"]:
            lines.append(f"- `{exclusion['instance_id']}`: `{exclusion['status']}` / `{exclusion['reason']}`")
    else:
        lines.append("- None for this finite certificate build.")
    lines.extend(
        [
            "",
            "## Claim Boundary",
            "",
            "- No full `G0_BASE` strictness claim.",
            "- No scalable family theorem claim.",
            "- No hierarchy completeness claim.",
            "- No P vs NP progress claim.",
            "- Native certificates are not DRAT.",
            "",
        ]
    )
    return "\n".join(lines)


def theorem_candidate_updates(certificate: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "id": "TC-033",
            "name": "Finite Restricted G0-vs-G1 Strictness Certificate",
            "statement": (
                "For the finite checked instance set I, each F in I is rejected by G0_WIDTH_C under cap c "
                "via verified width obstruction and accepted by G1_XOR_FOR_STRICTNESS via verified XOR certificate."
            ),
            "status": certificate["strictness_status"],
            "supporting_witnesses": [record["instance_id"] for record in certificate["instances"]],
            "forbidden_interpretations": certificate["forbidden_interpretations"],
        },
        {
            "id": "TC-032",
            "name": "Scalable Tseitin Family Strictness Candidate",
            "status": SCALABLE_FAMILY_PROOF_OBLIGATION,
            "supporting_witnesses": ["scalable Tseitin/expander family"],
            "forbidden_interpretations": ["not marked proven by finite certificates"],
        },
    ]


def build_outputs(
    *,
    instances: Iterable[str] = DEFAULT_FINITE_INSTANCES,
    cap_c: int = 4,
    out_root: str | Path = "outputs/v2.10-finite-strictness-certificate",
    strict: bool = False,
    zip_path: str | Path = "witnora-core-v2.10-finite-strictness-certificate.zip",
) -> dict[str, Any]:
    root = Path(out_root)
    root.mkdir(parents=True, exist_ok=True)
    cert = build_finite_strictness_certificate(instances=instances, cap_c=cap_c)
    checker = check_finite_strictness_certificate(cert.to_dict())
    cert_dict = cert.to_dict() | {
        "checker_status": checker.checker_status,
        "strictness_status": FINITE_STRICTNESS_CERTIFIED if checker.checker_status == FINITE_STRICTNESS_CERTIFICATE_VERIFIED else FINITE_STRICTNESS_CERTIFICATE_FAILED,
    }
    checker_dict = checker.to_dict()
    payloads = {
        "finite_strictness_certificate.json": cert_dict,
        "finite_strictness_checker_result.json": checker_dict,
        "instance_strictness_records.json": {"instance_strictness_records": cert_dict["instances"]},
        "width_obstruction_replay_summary.json": {
            "width_obstruction_replay_summary": [
                {
                    "instance_id": record["instance_id"],
                    "checker_status": record["lower_result"]["width_obstruction_certificate"]["checker_status"],
                    "certified_lower_bound": record["lower_result"]["certified_lower_bound"],
                    "cap_c": cap_c,
                    "restricted_route_result": record["lower_result"]["restricted_route_result"],
                }
                for record in cert_dict["instances"]
            ]
        },
        "xor_upper_bound_replay_summary.json": {
            "xor_upper_bound_replay_summary": [
                {
                    "instance_id": record["instance_id"],
                    "checker_status": record["upper_result"]["xor_upper_bound_certificate"]["checker_status"],
                    "extraction_verified": record["upper_result"]["extraction_verified"],
                    "sat_or_unsat_result": record["upper_result"]["sat_or_unsat_result"],
                    "certification_level": record["upper_result"]["certification_level"],
                }
                for record in cert_dict["instances"]
            ]
        },
        "scalable_family_proof_obligations.json": {
            "scalable_family_status": SCALABLE_FAMILY_PROOF_OBLIGATION,
            "proof_obligations": proof_obligation_updates(cap_c),
        },
        "theorem_candidate_updates.json": {"theorem_candidate_updates": theorem_candidate_updates(cert_dict)},
        "restricted_grammar_definitions.json": {"restricted_grammar_definitions": restricted_grammar_definitions(cap_c)},
    }
    for name, payload in payloads.items():
        _write_json(root / name, payload)
    with (root / "finite_strictness_summary.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "instance_id",
                "family",
                "cap_c",
                "certified_lower_bound",
                "restricted_route_result",
                "xor_checker_status",
                "sat_or_unsat_result",
                "instance_checker_status",
            ],
        )
        writer.writeheader()
        for record in cert_dict["instances"]:
            writer.writerow(
                {
                    "instance_id": record["instance_id"],
                    "family": record["family"],
                    "cap_c": cap_c,
                    "certified_lower_bound": record["lower_result"]["certified_lower_bound"],
                    "restricted_route_result": record["lower_result"]["restricted_route_result"],
                    "xor_checker_status": record["upper_result"]["xor_upper_bound_certificate"]["checker_status"],
                    "sat_or_unsat_result": record["upper_result"]["sat_or_unsat_result"],
                    "instance_checker_status": record["instance_checker_status"],
                }
            )
    (root / "FINITE_STRICTNESS_CERTIFICATE_REPORT.md").write_text(
        finite_strictness_report(certificate=cert_dict, checker_result=checker_dict),
        encoding="utf-8",
        newline="\n",
    )
    digest = make_zip(root, zip_path) if zip_path else ""
    return {
        "out_root": str(root),
        "zip": str(zip_path) if zip_path else "",
        "zip_sha256": digest,
        "strict": strict,
        "finite_strictness_certificate": cert_dict,
        "finite_strictness_checker_result": checker_dict,
        "instance_strictness_records": cert_dict["instances"],
        "resource_exclusions": cert_dict["resource_exclusions"],
        "theorem_candidate_updates": theorem_candidate_updates(cert_dict),
    }


def check_command(
    *,
    certificate_path: str | Path,
    out_root: str | Path,
) -> dict[str, Any]:
    root = Path(out_root)
    root.mkdir(parents=True, exist_ok=True)
    result = check_finite_strictness_certificate(certificate_path)
    _write_json(root / "finite_strictness_checker_result.json", result.to_dict())
    return {"out_root": str(root), "finite_strictness_checker_result": result.to_dict()}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build/check finite strictness certificates")
    sub = parser.add_subparsers(dest="command", required=True)
    build = sub.add_parser("build")
    build.add_argument("--instances", nargs="+", default=list(DEFAULT_FINITE_INSTANCES))
    build.add_argument("--cap-c", type=int, default=4)
    build.add_argument("--out-root", default="outputs/v2.10-finite-strictness-certificate")
    build.add_argument("--strict", action="store_true")
    build.add_argument("--zip", default="witnora-core-v2.10-finite-strictness-certificate.zip")
    check = sub.add_parser("check")
    check.add_argument("--certificate", required=True)
    check.add_argument("--out-root", default="outputs/v2.10-finite-strictness-certificate/check")
    args = parser.parse_args(argv)
    if args.command == "build":
        result = build_outputs(
            instances=args.instances,
            cap_c=args.cap_c,
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
                    "checker_status": result["finite_strictness_checker_result"]["checker_status"],
                    "strictness_status": result["finite_strictness_certificate"]["strictness_status"],
                    "certified_instances": [record["instance_id"] for record in result["instance_strictness_records"]],
                    "resource_exclusions": result["resource_exclusions"],
                }
            )
        )
        return 0
    if args.command == "check":
        result = check_command(certificate_path=args.certificate, out_root=args.out_root)
        print(stable_json(result["finite_strictness_checker_result"]))
        return 0 if result["finite_strictness_checker_result"]["checker_status"] == FINITE_STRICTNESS_CERTIFICATE_VERIFIED else 1
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
