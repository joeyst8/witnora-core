"""Reusable verification-report and trust-card helpers."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import re
from typing import Any

from .claim_boundary import scan_text_for_claim_boundary
from .partial_replay import partial_replay_diagnostic_artifact
from .proof import verify_certificate_bundle

VERDICT_VERIFIED = "VERIFIED"
VERDICT_PARTIALLY_VERIFIED = "PARTIALLY_VERIFIED"
VERDICT_NOT_VERIFIED = "NOT_VERIFIED"
VERDICT_OVERCLAIM = "OVERCLAIM"
VERDICT_ARTIFACT_INTEGRITY_VERIFIED = "ARTIFACT_INTEGRITY_VERIFIED"
VERDICT_PARTIAL_REPLAY_VERIFIED = "PARTIAL_REPLAY_VERIFIED_WITH_SCOPE_LIMITS"

CERT_RELEASE_ARTIFACT_INTEGRITY_VERIFIED = "RELEASE_ARTIFACT_INTEGRITY_VERIFIED"
CERT_PARTIAL_REPLAY_ARTIFACT_AND_LOGS_VERIFIED = "PARTIAL_REPLAY_ARTIFACT_AND_LOGS_VERIFIED"
CERT_PARTIAL_REPLAY_INDEPENDENT_CHECKER_VERIFIED = "PARTIAL_REPLAY_INDEPENDENT_CHECKER_VERIFIED"
CERT_PARTIAL_REPLAY_DRAT_TRIM_VERIFIED = "PARTIAL_REPLAY_DRAT_TRIM_VERIFIED"
DEPTH_METADATA_HASH_CHECKS_ONLY = "metadata_hash_checks_only"
DEPTH_PARTIAL_REPLAY = "partial_replay"
DEPTH_FULL_REPLAY = "full"
CLAIM_SCAN_DEPTH_HEURISTIC_TEXT_SCAN = "heuristic_text_scan"

CLAIM_SCANNER_LIMITATION_TEXT = (
    "The claim-boundary scanner is a heuristic text safety net, not a proof of "
    "absence of overclaims. It can miss paraphrases, ambiguous wording, or "
    "context-sensitive claims. A human audit is still required before public release."
)

ARTIFACT_INTEGRITY_SCOPE_TEXT = (
    "The artifact hashes match the manifest, required files are present, and the "
    "claim-boundary scanner found no affirmative forbidden claims. This is a "
    "metadata and artifact-integrity check. It does not rerun the scientific "
    "proofs, rerun drat-trim on all proofs, or rerun the benchmark diagnostic."
)

PARTIAL_REPLAY_SCOPE_TEXT = (
    "This report reflects partial replay of selected evidence already present "
    "in the artifact. It does not rerun the full solver, regenerate CNFgen "
    "instances, or rerun the full benchmark diagnostic."
)

PROOF_SELECTION_LIMITED_TEXT = (
    "Only selected proof evidence was replayed. This trust card does not represent "
    "full replay of every proof in the artifact."
)

DEFAULT_METADATA_ONLY_RISK_FLAGS = [
    "METADATA_ONLY",
    "DRAT_TRIM_NOT_RERUN",
    "INDEPENDENT_CHECKER_NOT_RERUN",
    "CLAIM_SCAN_HEURISTIC_ONLY",
]

DEFAULT_ALLOWED_CLAIMS = [
    "Witnora reports only scoped certification levels supported by evidence.",
    "Externally verified UNSAT requires an accepted proof artifact and checker record.",
    "Native-only results are separated from externally verified results.",
]

DEFAULT_FORBIDDEN_CLAIMS = [
    "parity support",
    "broad XOR extraction",
    "CryptoMiniSat-style extraction",
    "competitive SAT solving",
    "industrial benchmark performance",
    "full DRAT/RAT/LRAT/FRAT support",
    "P vs NP progress",
    "HARD or UNKNOWN status claims",
]


@dataclass
class VerificationReport:
    claim: str
    logical_status: str
    discovery_route: str
    certification_level: str
    public_category: str
    evidence_files: list[str] = field(default_factory=list)
    external_checkers: list[str] = field(default_factory=list)
    checker_results: list[dict[str, Any]] = field(default_factory=list)
    artifact_hashes: dict[str, str] = field(default_factory=dict)
    reproducibility_status: str = "NOT_ASSESSED"
    verification_depth: str = DEPTH_METADATA_HASH_CHECKS_ONLY
    evidence_checked: list[dict[str, Any]] = field(default_factory=list)
    checks_performed: list[dict[str, Any]] = field(default_factory=list)
    claim_scan_depth: str = CLAIM_SCAN_DEPTH_HEURISTIC_TEXT_SCAN
    last_verification_timestamp: str = ""
    replay_depth: str | None = None
    selection_policy: str | None = None
    selected_evidence: list[dict[str, Any]] = field(default_factory=list)
    proof_syntax_checks: list[dict[str, Any]] = field(default_factory=list)
    drat_trim_log_checks: list[dict[str, Any]] = field(default_factory=list)
    independent_checker_replay: list[dict[str, Any]] = field(default_factory=list)
    drat_trim_replay: list[dict[str, Any]] = field(default_factory=list)
    allowed_claims: list[str] = field(default_factory=lambda: list(DEFAULT_ALLOWED_CLAIMS))
    forbidden_claims: list[str] = field(default_factory=lambda: list(DEFAULT_FORBIDDEN_CLAIMS))
    risk_flags: list[str] = field(default_factory=list)
    verdict: str = VERDICT_NOT_VERIFIED

    def to_dict(self) -> dict[str, Any]:
        return {
            "claim": self.claim,
            "logical_status": self.logical_status,
            "discovery_route": self.discovery_route,
            "certification_level": self.certification_level,
            "public_category": self.public_category,
            "evidence_files": self.evidence_files,
            "external_checkers": self.external_checkers,
            "checker_results": self.checker_results,
            "artifact_hashes": self.artifact_hashes,
            "reproducibility_status": self.reproducibility_status,
            "verification_depth": self.verification_depth,
            "evidence_checked": self.evidence_checked,
            "checks_performed": self.checks_performed,
            "claim_scan_depth": self.claim_scan_depth,
            "last_verification_timestamp": self.last_verification_timestamp,
            "replay_depth": self.replay_depth,
            "selection_policy": self.selection_policy,
            "selected_evidence": self.selected_evidence,
            "proof_syntax_checks": self.proof_syntax_checks,
            "drat_trim_log_checks": self.drat_trim_log_checks,
            "independent_checker_replay": self.independent_checker_replay,
            "drat_trim_replay": self.drat_trim_replay,
            "allowed_claims": self.allowed_claims,
            "forbidden_claims": self.forbidden_claims,
            "risk_flags": self.risk_flags,
            "verdict": self.verdict,
        }


def stable_json(data: Any) -> str:
    return json.dumps(data, indent=2, sort_keys=True) + "\n"


def sha256_file(path: str | Path) -> str:
    digest = sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def utc_timestamp() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def render_verification_report_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Witnora Verification Report",
        "",
        "## Claim Being Audited",
        "",
        str(report.get("claim", "")),
        "",
        "## Evidence Provided",
        "",
    ]
    for item in report.get("evidence_files", []):
        lines.append(f"- `{item}`")
    if not report.get("evidence_files"):
        lines.append("- none")
    lines.extend(["", "## Verification Depth", "", f"`{report.get('verification_depth', '')}`"])
    if report.get("verification_depth") == DEPTH_METADATA_HASH_CHECKS_ONLY:
        lines.extend(["", ARTIFACT_INTEGRITY_SCOPE_TEXT])
    if report.get("verification_depth") == DEPTH_PARTIAL_REPLAY:
        lines.extend(["", PARTIAL_REPLAY_SCOPE_TEXT])
        lines.extend(["", "## Replay Depth", "", f"`{report.get('replay_depth', '')}`"])
        lines.extend(["", "## Selection Policy", "", f"`{report.get('selection_policy', '')}`"])
        lines.extend(["", "## Selected Evidence", ""])
        selected_evidence = report.get("selected_evidence", [])
        if selected_evidence:
            for item in selected_evidence:
                lines.append(
                    f"- `{item.get('instance_id', '')}` c={item.get('c', '')} "
                    f"({item.get('cap_profile', '')}): `{item.get('public_category', '')}`"
                )
        else:
            lines.append("- none")
    lines.extend(["", "## Checks Performed", ""])
    checks_performed = report.get("checks_performed", [])
    if checks_performed:
        for check in checks_performed:
            lines.append(
                f"- `{check.get('name', '')}`: {str(check.get('status', '')).lower()} "
                f"(depth: `{check.get('depth', '')}`)"
            )
    else:
        lines.append("- none recorded")
    lines.extend(["", "## Checker Results", ""])
    for result in report.get("checker_results", []):
        name = result.get("checker", result.get("check", "checker"))
        passed = result.get("passed", result.get("verified", False))
        lines.append(f"- `{name}`: {'pass' if passed else 'fail'}")
    lines.extend(["", "## Evidence Checked", ""])
    evidence_checked = report.get("evidence_checked", [])
    if evidence_checked:
        for item in evidence_checked:
            lines.append(
                f"- `{item.get('path', '')}` ({item.get('kind', '')}): {item.get('status', '')}; "
                f"expected `{item.get('sha256_expected', '')}`, actual `{item.get('sha256_actual', '')}`"
            )
    else:
        lines.append("- none recorded")
    lines.extend(["", "## External Verification", ""])
    for checker in report.get("external_checkers", []):
        lines.append(f"- `{checker}`")
    if not report.get("external_checkers"):
        lines.append("- none recorded")
    if report.get("proof_syntax_checks"):
        lines.extend(["", "## Proof Syntax Checks", ""])
        for check in report.get("proof_syntax_checks", []):
            lines.append(f"- `{check.get('instance_id', '')}`: {check.get('status', '')} - {check.get('message', '')}")
    if report.get("drat_trim_log_checks"):
        lines.extend(["", "## drat-trim Log Checks", ""])
        for check in report.get("drat_trim_log_checks", []):
            lines.append(f"- `{check.get('instance_id', '')}`: {check.get('status', '')} - {check.get('message', '')}")
    if report.get("independent_checker_replay"):
        lines.extend(["", "## Independent Checker Replay", ""])
        for check in report.get("independent_checker_replay", []):
            lines.append(f"- `{check.get('instance_id', '')}`: {check.get('status', '')} - {check.get('message', '')}")
    if report.get("drat_trim_replay"):
        lines.extend(["", "## drat-trim Replay", ""])
        for check in report.get("drat_trim_replay", []):
            lines.append(f"- `{check.get('instance_id', '')}`: {check.get('status', '')} - {check.get('message', '')}")
    lines.extend(
        [
            "",
            "## Claim Boundary Scanner Limitation",
            "",
            CLAIM_SCANNER_LIMITATION_TEXT,
            "",
            f"claim_scan_depth: `{report.get('claim_scan_depth', '')}`",
        ]
    )
    lines.extend(["", "## Artifact Hashes", ""])
    for name, digest in sorted(report.get("artifact_hashes", {}).items()):
        lines.append(f"- `{name}`: `{digest}`")
    lines.extend(["", "## Certification Level", "", f"`{report.get('certification_level', '')}`"])
    lines.extend(["", "## Allowed Claims", ""])
    for claim in report.get("allowed_claims", []):
        lines.append(f"- {claim}")
    lines.extend(["", "## Forbidden Claims", ""])
    for claim in report.get("forbidden_claims", []):
        lines.append(f"- {claim}")
    lines.extend(["", "## Risk Flags", ""])
    for flag in report.get("risk_flags", []):
        lines.append(f"- {flag}")
    if not report.get("risk_flags"):
        lines.append("- none")
    lines.extend(["", "## Last Verification Timestamp", "", str(report.get("last_verification_timestamp", ""))])
    lines.extend(["", "## Final Verdict", "", f"`{report.get('verdict', '')}`", ""])
    return "\n".join(lines)


def write_report_files(report: dict[str, Any], json_path: str | Path, markdown_path: str | Path) -> None:
    Path(json_path).write_text(stable_json(report), encoding="utf-8")
    Path(markdown_path).write_text(render_verification_report_markdown(report), encoding="utf-8")


def verification_report_for_certificate(path: str | Path) -> dict[str, Any]:
    cert_path = Path(path)
    checker_result = verify_certificate_bundle(cert_path)
    verified = bool(checker_result.get("verified", False))
    risk_flags: list[str] = []
    if not verified:
        risk_flags.append(str(checker_result.get("failed_check", "certificate_verification_failed")))
    result = VerificationReport(
        claim="Witnora certificate bundle is internally consistent and independently replay-checkable.",
        logical_status=str(checker_result.get("status", "NOT_VERIFIED")),
        discovery_route="CERTIFICATE_BUNDLE_CHECK",
        certification_level="CERTIFICATE_BUNDLE_VERIFIED" if verified else "NOT_VERIFIED",
        public_category="CERTIFICATE_VERIFIED" if verified else "CERTIFICATE_NOT_VERIFIED",
        evidence_files=[str(cert_path)],
        external_checkers=[],
        checker_results=[{"checker": "witnora_certificate_bundle_verifier", **checker_result}],
        artifact_hashes={str(cert_path): sha256_file(cert_path)} if cert_path.is_file() else {},
        reproducibility_status="CERTIFICATE_REPLAYED" if verified else "CERTIFICATE_REPLAY_FAILED",
        verification_depth="partial_replay",
        checks_performed=[
            {
                "name": "certificate_bundle_replay",
                "status": "PASS" if verified else "FAIL",
                "depth": "partial_replay",
            }
        ],
        last_verification_timestamp=utc_timestamp(),
        risk_flags=risk_flags,
        verdict=VERDICT_VERIFIED if verified else VERDICT_NOT_VERIFIED,
    )
    return result.to_dict()


def parse_manifest_hash_table(text: str) -> dict[str, str]:
    hashes: dict[str, str] = {}
    row_pattern = re.compile(r"^\|\s*`([^`]+)`\s*\|\s*`?([A-Fa-f0-9]{64})`?\s*\|", re.MULTILINE)
    for match in row_pattern.finditer(text):
        hashes[match.group(1)] = match.group(2).upper()
    return hashes


def _manifest_lookup(path: Path, manifest_hashes: dict[str, str]) -> str | None:
    candidates = [str(path), path.name, str(path).replace("\\", "/")]
    for candidate in candidates:
        if candidate in manifest_hashes:
            return manifest_hashes[candidate]
    return None


def _evidence_status(path: Path, kind: str, expected: str | None) -> dict[str, Any]:
    exists = path.is_file()
    actual = sha256_file(path) if exists else None
    if not exists:
        status = "MISSING"
    elif expected is None:
        status = "MATCH"
        expected = actual
    elif actual == expected:
        status = "MATCH"
    else:
        status = "MISMATCH"
    return {
        "path": str(path),
        "kind": kind,
        "sha256_expected": expected,
        "sha256_actual": actual,
        "status": status,
    }


def verification_report_for_release(
    *,
    source_zip: str | Path,
    diagnostic_zip: str | Path,
    manifest: str | Path,
    depth: str = "metadata",
    selection_policy: str = "largest",
    rerun_drat_trim: bool = False,
    drat_trim_path: str | Path | None = None,
    max_replay_proofs: int = 3,
) -> dict[str, Any]:
    requested_depth = depth.strip().lower()
    if requested_depth == "full":
        return VerificationReport(
            claim="Full release replay was requested, but full replay is not implemented in v1.2.",
            logical_status="RELEASE_FULL_REPLAY_REQUEST",
            discovery_route="FULL_REPLAY_UNSUPPORTED",
            certification_level="NOT_VERIFIED",
            public_category="PUBLIC_RELEASE_VERIFICATION",
            evidence_files=[str(source_zip), str(diagnostic_zip), str(manifest)],
            reproducibility_status="FULL_REPLAY_NOT_IMPLEMENTED",
            verification_depth=DEPTH_FULL_REPLAY,
            checks_performed=[
                {
                    "name": "full_replay",
                    "status": "FAIL",
                    "depth": DEPTH_FULL_REPLAY,
                    "message": "full replay is reserved for future work",
                }
            ],
            last_verification_timestamp=utc_timestamp(),
            risk_flags=["FULL_REPLAY_NOT_IMPLEMENTED"],
            verdict=VERDICT_NOT_VERIFIED,
        ).to_dict()

    source_path = Path(source_zip)
    diagnostic_path = Path(diagnostic_zip)
    manifest_path = Path(manifest)
    evidence = [str(source_path), str(diagnostic_path), str(manifest_path)]
    artifact_hashes = {str(path): sha256_file(path) for path in [source_path, diagnostic_path, manifest_path] if path.is_file()}
    manifest_text = manifest_path.read_text(encoding="utf-8")
    manifest_hashes = parse_manifest_hash_table(manifest_text)

    checker_results: list[dict[str, Any]] = []
    checks_performed: list[dict[str, Any]] = []
    risk_flags: list[str] = list(DEFAULT_METADATA_ONLY_RISK_FLAGS)
    evidence_checked: list[dict[str, Any]] = []
    for path in [source_path, diagnostic_path]:
        expected = _manifest_lookup(path, manifest_hashes)
        evidence_item = _evidence_status(
            path,
            "source_archive" if path == source_path else "diagnostic_artifact",
            expected,
        )
        evidence_checked.append(evidence_item)
        check_name = "source_archive_sha256" if path == source_path else "diagnostic_artifact_sha256"
        if expected is None:
            risk_flags.append("UNVERIFIED_CLAIM")
            checker_results.append({"checker": "sha256_manifest_match", "path": str(path), "passed": False, "error": "not listed in manifest"})
            checks_performed.append({"name": check_name, "status": "FAIL", "depth": DEPTH_METADATA_HASH_CHECKS_ONLY})
        elif evidence_item["status"] == "MISSING":
            risk_flags.append("MISSING_FILE")
            checker_results.append({"checker": "sha256_manifest_match", "path": str(path), "passed": False, "expected": expected, "error": "missing file"})
            checks_performed.append({"name": check_name, "status": "FAIL", "depth": DEPTH_METADATA_HASH_CHECKS_ONLY})
        elif evidence_item["status"] == "MISMATCH":
            risk_flags.append("HASH_MISMATCH")
            checker_results.append(
                {
                    "checker": "sha256_manifest_match",
                    "path": str(path),
                    "passed": False,
                    "expected": expected,
                    "actual": evidence_item["sha256_actual"],
                }
            )
            checks_performed.append({"name": check_name, "status": "FAIL", "depth": DEPTH_METADATA_HASH_CHECKS_ONLY})
        else:
            checker_results.append({"checker": "sha256_manifest_match", "path": str(path), "passed": True, "sha256": evidence_item["sha256_actual"]})
            checks_performed.append({"name": check_name, "status": "PASS", "depth": DEPTH_METADATA_HASH_CHECKS_ONLY})

    evidence_checked.append(_evidence_status(manifest_path, "manifest", None))
    checks_performed.append({"name": "manifest_file_present", "status": "PASS", "depth": DEPTH_METADATA_HASH_CHECKS_ONLY})

    claim_scan = scan_text_for_claim_boundary(manifest_text)
    checker_results.append({"checker": "claim_boundary_scan", "passed": bool(claim_scan.get("passed")), "details": claim_scan})
    checks_performed.append(
        {
            "name": "claim_boundary_scan",
            "status": "PASS" if claim_scan.get("passed") else "FAIL",
            "depth": CLAIM_SCAN_DEPTH_HEURISTIC_TEXT_SCAN,
        }
    )
    if not claim_scan.get("passed"):
        risk_flags.append("UNVERIFIED_CLAIM")

    all_hash_checks_passed = all(
        result.get("passed") is True
        for result in checker_results
        if result.get("checker") == "sha256_manifest_match"
    )
    claim_scan_passed = bool(claim_scan.get("passed"))
    if not all_hash_checks_passed:
        verdict = VERDICT_PARTIALLY_VERIFIED
        reproducibility = "ARTIFACTS_HASHED_WITH_MANIFEST_GAPS"
        certification_level = "RELEASE_ARTIFACT_INTEGRITY_PARTIAL"
    elif not claim_scan_passed:
        verdict = VERDICT_OVERCLAIM
        reproducibility = "CLAIM_BOUNDARY_FAILED"
        certification_level = "RELEASE_ARTIFACT_INTEGRITY_OVERCLAIM"
    else:
        verdict = VERDICT_ARTIFACT_INTEGRITY_VERIFIED
        reproducibility = "SOURCE_AND_DIAGNOSTIC_HASHES_VERIFIED"
        certification_level = CERT_RELEASE_ARTIFACT_INTEGRITY_VERIFIED

    report = VerificationReport(
        claim=(
            "Witnora-Core release package supports the scoped public preprint claim "
            "with source, diagnostic artifact, manifest hashes, and recorded external-check evidence."
        ),
        logical_status="RELEASE_ARTIFACT_AUDIT",
        discovery_route="RELEASE_MANIFEST_AND_HASH_CHECK",
        certification_level=certification_level,
        public_category="PUBLIC_RELEASE_VERIFICATION",
        evidence_files=evidence,
        external_checkers=[],
        checker_results=checker_results,
        artifact_hashes=artifact_hashes,
        reproducibility_status=reproducibility,
        verification_depth=DEPTH_METADATA_HASH_CHECKS_ONLY,
        evidence_checked=evidence_checked,
        checks_performed=checks_performed,
        claim_scan_depth=CLAIM_SCAN_DEPTH_HEURISTIC_TEXT_SCAN,
        last_verification_timestamp=utc_timestamp(),
        risk_flags=risk_flags,
        verdict=verdict,
    ).to_dict()
    if requested_depth in {"metadata", "metadata_hash_checks_only"}:
        return report
    if requested_depth != "partial":
        report["verdict"] = VERDICT_NOT_VERIFIED
        report["verification_depth"] = requested_depth
        report["risk_flags"] = list(report.get("risk_flags", [])) + ["UNSUPPORTED_VERIFICATION_DEPTH"]
        return report
    return _with_partial_replay(
        report,
        diagnostic_path=diagnostic_path,
        selection_policy=selection_policy,
        rerun_drat_trim=rerun_drat_trim,
        drat_trim_path=drat_trim_path,
        max_replay_proofs=max_replay_proofs,
    )


def _without_flags(flags: list[str], *remove: str) -> list[str]:
    remove_set = set(remove)
    return [flag for flag in flags if flag not in remove_set]


def _with_flag(flags: list[str], flag: str) -> list[str]:
    return flags if flag in flags else flags + [flag]


def _with_partial_replay(
    report: dict[str, Any],
    *,
    diagnostic_path: Path,
    selection_policy: str,
    rerun_drat_trim: bool,
    drat_trim_path: str | Path | None,
    max_replay_proofs: int,
) -> dict[str, Any]:
    replay = partial_replay_diagnostic_artifact(
        diagnostic_path,
        selection_policy=selection_policy,
        rerun_drat_trim=rerun_drat_trim,
        drat_trim_path=drat_trim_path,
        max_replay_proofs=max_replay_proofs,
    )
    report["verification_depth"] = DEPTH_PARTIAL_REPLAY
    report["selection_policy"] = selection_policy
    report["selected_evidence"] = replay.get("selected_evidence", [])
    candidate_count = int(replay.get("candidate_count") or 0)
    selected_count = len(report["selected_evidence"])
    report["candidate_evidence_count"] = candidate_count
    report["selected_evidence_count"] = selected_count
    report["proof_syntax_checks"] = replay.get("proof_syntax_checks", [])
    report["drat_trim_log_checks"] = replay.get("drat_trim_log_checks", [])
    report["independent_checker_replay"] = replay.get("independent_checker_replay", [])
    report["drat_trim_replay"] = replay.get("drat_trim_replay", [])
    report["checks_performed"] = list(report.get("checks_performed", [])) + list(replay.get("structure_checks", []))
    report["checks_performed"].extend(report["proof_syntax_checks"])
    report["checks_performed"].extend(report["drat_trim_log_checks"])
    report["checks_performed"].extend(report["independent_checker_replay"])
    report["checks_performed"].extend(report["drat_trim_replay"])

    flags = _without_flags(list(report.get("risk_flags", [])), "METADATA_ONLY")
    flags = _with_flag(flags, "PROOF_SYNTAX_CHECKED")
    flags = _with_flag(flags, "PROOF_LOGS_CHECKED")
    if candidate_count and selected_count < candidate_count:
        flags = _with_flag(flags, "PROOF_SELECTION_LIMITED")
    if replay.get("independent_checker_passed"):
        flags = _without_flags(flags, "INDEPENDENT_CHECKER_NOT_RERUN")
        flags = _with_flag(flags, "INDEPENDENT_CHECKER_RERUN")
    if replay.get("drat_trim_replay_passed"):
        flags = _without_flags(flags, "DRAT_TRIM_NOT_RERUN")
        flags = _with_flag(flags, "DRAT_TRIM_RERUN")
    elif rerun_drat_trim:
        flags = _with_flag(flags, "DRAT_TRIM_REPLAY_FAILED_OR_SKIPPED")

    syntax_and_logs_passed = bool(replay.get("passed"))
    independent_passed = bool(replay.get("independent_checker_passed"))
    drat_replay_passed = bool(replay.get("drat_trim_replay_passed"))
    if syntax_and_logs_passed and drat_replay_passed:
        report["verdict"] = VERDICT_PARTIAL_REPLAY_VERIFIED
        report["certification_level"] = CERT_PARTIAL_REPLAY_DRAT_TRIM_VERIFIED
        report["replay_depth"] = "independent_checker_and_drat_trim_replay"
    elif syntax_and_logs_passed and independent_passed:
        report["verdict"] = VERDICT_PARTIAL_REPLAY_VERIFIED
        report["certification_level"] = CERT_PARTIAL_REPLAY_INDEPENDENT_CHECKER_VERIFIED
        report["replay_depth"] = "independent_checker_replay"
    elif syntax_and_logs_passed:
        report["verdict"] = VERDICT_PARTIAL_REPLAY_VERIFIED
        report["certification_level"] = CERT_PARTIAL_REPLAY_ARTIFACT_AND_LOGS_VERIFIED
        report["replay_depth"] = "proof_syntax_and_logs"
    else:
        report["verdict"] = VERDICT_PARTIALLY_VERIFIED
        report["certification_level"] = "PARTIAL_REPLAY_FAILED_OR_INCOMPLETE"
        report["replay_depth"] = "partial_replay_failed"
        flags = _with_flag(flags, "PARTIAL_REPLAY_FAILED")
    report["risk_flags"] = flags
    return report


def trust_card_from_report(report: dict[str, Any], *, project: str = "Witnora-Core") -> dict[str, Any]:
    verdict = str(report.get("verdict", "NOT_VERIFIED"))
    if verdict == VERDICT_ARTIFACT_INTEGRITY_VERIFIED:
        trust_verdict = "VERIFIED_ARTIFACT_INTEGRITY_WITH_SCOPE_LIMITS"
    elif verdict == VERDICT_PARTIAL_REPLAY_VERIFIED:
        trust_verdict = VERDICT_PARTIAL_REPLAY_VERIFIED
    elif verdict == VERDICT_VERIFIED:
        trust_verdict = "VERIFIED_WITH_SCOPE_LIMITS"
    elif verdict == VERDICT_PARTIALLY_VERIFIED:
        trust_verdict = "PARTIALLY_VERIFIED_WITH_RISK_FLAGS"
    elif verdict == VERDICT_OVERCLAIM:
        trust_verdict = "OVERCLAIM_DETECTED"
    else:
        trust_verdict = "NOT_VERIFIED"
    verified_by = list(report.get("external_checkers", []))
    verified_by.extend(check.get("name", "check") for check in report.get("checks_performed", []))
    verified_by.extend(result.get("checker", "checker") for result in report.get("checker_results", []))
    return {
        "project": project,
        "claim": report.get("claim", ""),
        "verified_by": verified_by,
        "certification_level": report.get("certification_level", ""),
        "verification_depth": report.get("verification_depth", DEPTH_METADATA_HASH_CHECKS_ONLY),
        "replay_depth": report.get("replay_depth"),
        "not_claimed": report.get("forbidden_claims", []),
        "reproducibility": report.get("reproducibility_status", ""),
        "risk_flags": report.get("risk_flags", []),
        "verdict": trust_verdict,
    }


def render_trust_card_markdown(card: dict[str, Any]) -> str:
    if card.get("verification_depth") == DEPTH_PARTIAL_REPLAY:
        scope_text = (
            "This trust card reflects partial replay of selected evidence. "
            "It does not rerun the full solver or regenerate the benchmark diagnostic."
        )
    else:
        scope_text = (
            "This trust card verifies artifact integrity and scope boundaries only. "
            "It does not rerun the scientific proof pipeline."
        )
    lines = [
        "# Witnora Trust Card",
        "",
        f"**Project:** {card.get('project', '')}",
        "",
        scope_text,
        "",
        "## Claim",
        "",
        str(card.get("claim", "")),
        "",
        "## Verified By",
        "",
    ]
    if "PROOF_SELECTION_LIMITED" in card.get("risk_flags", []):
        lines[6:6] = [PROOF_SELECTION_LIMITED_TEXT, ""]
    for item in card.get("verified_by", []):
        lines.append(f"- {item}")
    lines.extend(["", "## Certification Level", "", f"`{card.get('certification_level', '')}`"])
    lines.extend(["", "## Verification Depth", "", f"`{card.get('verification_depth', '')}`"])
    if card.get("verification_depth") == DEPTH_PARTIAL_REPLAY:
        lines.extend(
            [
                "",
                "## Replay Depth",
                "",
                f"`{card.get('replay_depth', '')}`",
            ]
        )
    lines.extend(["", "## Not Claimed", ""])
    for item in card.get("not_claimed", []):
        lines.append(f"- {item}")
    lines.extend(["", "## Risk Flags", ""])
    for item in card.get("risk_flags", []):
        lines.append(f"- {item}")
    lines.extend(["", "## Reproducibility", "", str(card.get("reproducibility", ""))])
    lines.extend(["", "## Verdict", "", f"`{card.get('verdict', '')}`", ""])
    return "\n".join(lines)
